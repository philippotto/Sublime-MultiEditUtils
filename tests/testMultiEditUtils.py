#!/usr/bin/python
# -*- coding: utf-8 -*-

import sublime
from unittest import TestCase
import re

version = sublime.version()


class TestMultiEditUtils(TestCase):

    def setUp(self):

        self.view = sublime.active_window().new_file()

    def tearDown(self):

        if self.view:
            self.view.set_scratch(True)
            self.view.window().run_command('close_file')

    def splitBy(self, separator, expectedAmount):

        testString = 'this, is, a, test'
        self.view.run_command('insert', {'characters': testString})
        self.view.run_command('select_all')
        self.view.run_command('split_selection',
                              {'separator': separator})

        selection = self.view.sel()
        selection_length = len([region for region in selection])
        self.assertEqual(len(selection), expectedAmount)

    def testSplitBySpace(self):

        self.splitBy(' ', 4)

    def testSplitByCommaSpace(self):

        self.splitBy(', ', 4)

    def testSplitByCharacter(self):

        self.splitBy('', 17)

    def testToggleRegionEnds(self):

        testString = 'this is a test'
        self.view.run_command('insert', {'characters': testString})

        regionTuple = [0, 14]
        self.selectRegions([regionTuple])

        selection = self.view.sel()
        self.assertRegionEqual(selection[0], regionTuple)

        self.view.run_command('normalize_region_ends')

        self.assertRegionEqual(selection[0], regionTuple[::-1])

    def testToggleRegionsEnds(self):

        testString = 'test test'
        self.view.run_command('insert', {'characters': testString})

        regionTuples = [[0, 4], [9, 5]]
        self.selectRegions(regionTuples)

        selection = self.view.sel()
        self.assertRegionEqual(selection[0], regionTuples[0])
        self.assertRegionEqual(selection[1], regionTuples[1])

        self.view.run_command('normalize_region_ends')

        self.assertRegionEqual(selection[0], regionTuples[0])
        self.assertRegionEqual(selection[1], regionTuples[1][::-1])

    def testJumpToLastRegion(self):

        testString = 'test test test test'
        self.view.run_command('insert', {'characters': testString})

        self.selectRegions([[0, 4], [5, 9]])

        selection = self.view.sel()
        self.assertEqual(len(selection), 2)

        self.view.run_command('jump_to_last_region')

        self.assertEqual(len(selection), 1)
        self.assertRegionEqual(selection[0], [9, 9])

    def testAddLastSelection(self):

        testString = 'this is a test'
        self.view.run_command('insert', {'characters': testString})

        regions = [[0, 4], [5, 9]]
        self.selectRegions([regions[0]])
        self.view.run_command('trigger_selection_modified')
        self.selectRegions([regions[1]])
        self.view.run_command('trigger_selection_modified')

        self.view.run_command('add_last_selection')

        selection = self.view.sel()

        self.assertEqual(len(selection), 2)
        self.assertRegionEqual(selection[0], regions[0])
        self.assertRegionEqual(selection[1], regions[1])

    def testRemoveEmptyRegions(self):

        testString = '''a
b

c'''
        regions = [[0, 1], [2, 3], [5, 6]]

        self.view.run_command('insert', {'characters': testString})
        self.view.run_command('select_all')
        self.view.run_command('split_selection_into_lines')
        self.view.run_command('remove_empty_regions')

        selection = self.view.sel()

        self.assertEqual(len(selection), 3)

        for (actual, expected) in zip(selection, regions):
            self.assertRegionEqual(actual, expected)

    def testStripSelection(self):

        testString = '  too much whitespace here  '

        self.view.run_command('insert', {'characters': testString})
        self.view.run_command('select_all')
        self.view.run_command('strip_selection')

        selection = self.view.sel()

        self.assertEqual(len(selection), 1)
        self.assertRegionEqual(selection[0], [2, 26])

    def testStripSelectionWithPureWhitespace(self):

        testString = '    '

        self.view.run_command('insert', {'characters': testString})
        selection = self.view.sel()

    # cursor should stay at the end of the line

        self.view.run_command('select_all')
        self.view.run_command('strip_selection')

        self.assertEqual(len(selection), 1)
        self.assertRegionEqual(selection[0], [4, 4])

    # cursor should be at the beginning of the line

        self.view.run_command('select_all')
        self.view.run_command('normalize_region_ends')
        self.view.run_command('strip_selection')

        self.assertEqual(len(selection), 1)
        self.assertRegionEqual(selection[0], [0, 0])

    def testMultiFindAll(self):

        testString = 'abc def - abc - def - def'

        self.view.run_command('insert', {'characters': testString})
        selection = self.view.sel()

    # select the first occurrences of abc and def

        selection.clear()
        selection.add(sublime.Region(0, 3))
        selection.add(sublime.Region(4, 7))

        self.view.run_command('multi_find_all')

        self.assertEqual(len(selection), 5)
        expectedRegions = [[0, 3], [4, 7], [10, 13], [16, 19], [22, 25]]

        self.assertRegionsEqual(selection, expectedRegions)

    def testDecode(self):

        sel = self.decode_sel('>test< some->Test< >TEST<')

        print(sel)

    def decode_sel(self, content):

        splitted = re.split(r'([│><])', content)
        content = ''
        pos = 0
        regionStart = 0
        regions = []
        for s in splitted:
            if s == '│':
                regions.append(pos)
            elif s == '<':
                regions.append(sublime.Region(regionStart, pos))
            elif s == '>':
                regionStart = pos
            else:
                pos += len(s)
                content += s

        return (content, regions)

    def testBasicPreserveCase(self):

        testString = '>test< some->Test< some_test Some-Test >TEST<'
        (testString, regions) = self.decode_sel(testString)
        self.view.run_command('insert', {'characters': testString})
        selection = self.view.sel()

        for region in regions:
            selection.add(region)

        self.view.run_command('preserve_case', {'newString': 'case'})

        self.assertEqual(self.view.substr(regions[0]), 'case')
        self.assertEqual(self.view.substr(regions[1]), 'Case')
        self.assertEqual(self.view.substr(regions[2]), 'CASE')

    def testAdvancedPreserveCase(self):

        expectedStrings = [
            'some case',
            'some-Case',
            'some_case',
            'Some-Case',
            'SomeCase',
            'someCase',
            'SomeCASE',
            ]
        testString = \
            '>some test< >some-Test< >some_test< >Some-Test< >SomeTest< >someTest< >SomeTEST<'
        (testString, regions) = self.decode_sel(testString)
        self.view.run_command('insert', {'characters': testString})
        selection = self.view.sel()

        for region in regions:
            selection.add(region)

        self.view.run_command('preserve_case', {'newString': 'some case'
                              })

        for (region, expectedString) in zip(regions, expectedStrings):
            self.assertEqual(self.view.substr(region), expectedString)

    def assertRegionEqual(self, a, b):

        self.assertEqual(a.a, b[0])
        self.assertEqual(a.b, b[1])

    def assertRegionsEqual(self, selection, expectedRegions):

        for (index, region) in enumerate(expectedRegions):
            self.assertRegionEqual(selection[index], region)

    def selectRegions(self, regions):

        self.view.sel().clear()
        for regionTuple in regions:
            self.view.sel().add(sublime.Region(regionTuple[0],
                                regionTuple[1]))
