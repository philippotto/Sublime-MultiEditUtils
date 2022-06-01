# coding: utf8

import sublime
from unittest import TestCase

_ST3 = sublime.version() >= '3000'
version = sublime.version()


content_string = '''Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod
tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam,
quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo
consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse
cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non
proident, sunt in culpa qui officia deserunt mollit anim id est laborum.'''


def to_region(v):
    if isinstance(v, int):
        region = sublime.Region(v, v)
    elif isinstance(v, sublime.Region):
        region = v
    else:
        region = sublime.Region(v[0], v[1])
    return region


class TestSelectionFields(TestCase):
    def setUp(self):
        self.view = sublime.active_window().new_file()
        regions = [(12, 14), (32, 30), 50, 60]
        self.start_regions = list(map(to_region, regions))

        self.view.run_command('insert', {'characters': content_string})
        self.select_regions(self.start_regions)

    def tearDown(self):
        if self.view:
            self.view.set_scratch(True)
            self.view.window().run_command('close_file')

    def assertSelectionEqual(self, sel1, sel2):
        self.assertEqual(len(sel1), len(sel2))
        for i in range(len(sel1)):
            self.assertEqual(to_region(sel1[i]), to_region(sel2[i]))

    def select_regions(self, regions):
        self.view.sel().clear()
        if _ST3:
            self.view.sel().add_all(map(to_region, regions))
        else:
            for region in regions:
                self.view.sel().add(to_region(region))

    def test_toggle(self):
        '''Test whether the toggle works.'''
        view = self.view
        regions = list(self.start_regions)

        view.run_command('selection_fields', {'mode': 'toggle'})

        self.assertEqual(len(view.sel()), 1)
        self.assertEqual(view.sel()[0], regions[0])
        stored_regions = view.get_regions('meu_sf_stored_selections')
        self.assertSelectionEqual(regions[1:], stored_regions)

        view.run_command('selection_fields', {'mode': 'toggle'})
        self.assertEqual(len(view.sel()), len(regions))
        self.assertSelectionEqual(view.sel(), regions)

    def test_smart_run(self):
        '''Test whether a full run with the smart mode works.'''
        view = self.view
        regions = list(self.start_regions)

        view.run_command('selection_fields', {'mode': 'smart'})

        for i in range(len(regions)):
            self.assertEqual(len(view.sel()), 1)
            self.assertEqual(view.sel()[0], regions[i])
            stored_regions = view.get_regions('meu_sf_stored_selections')
            self.assertSelectionEqual(regions[:i] + regions[i+1:],
                                      stored_regions)
            view.run_command('selection_fields', {'mode': 'smart'})
        self.assertSelectionEqual(view.sel(), regions)

    def test_smart_move(self):
        '''
        Test whether moving during a run, results in the corresponding
        caret positions after the run.
        '''
        view = self.view
        regions = list(self.start_regions)

        view.run_command('selection_fields', {'mode': 'smart'})

        for i in range(len(regions)):
            sel = view.sel()[0]
            if sel.empty():
                regions[i] = sel.end() + i + 1
            else:
                regions[i] = sel.end() + i
            for _ in range(i + 1):
                view.run_command('move', {'by': 'characters', 'forward': True})
            view.run_command('selection_fields', {'mode': 'smart'})
        self.assertSelectionEqual(view.sel(), regions)

    def test_smart_add_selections(self):
        '''
        Test whether adding carets during a run, results in the
        corresponding caret positions after the run.
        '''
        view = self.view
        regions = list(self.start_regions)

        view.run_command('selection_fields', {'mode': 'smart'})

        for i, v in enumerate(self.start_regions):
            sel = view.sel()[0]
            new_sel = to_region(sel.begin() - 1)
            view.sel().add(new_sel)
            regions.insert(i * 2, to_region(new_sel))

            view.run_command('selection_fields', {'mode': 'smart'})
        self.assertSelectionEqual(view.sel(), regions)

    def test_jump_remove(self):
        '''
        Test whether jumps remove other selections.
        '''
        view = self.view

        view.run_command('selection_fields', {'mode': 'smart'})

        jumps = 3
        for _ in range(jumps):
            view.run_command('selection_fields', {'mode': 'smart'})
        self.assertSelectionEqual(view.sel(), [self.start_regions[jumps]])

    def test_add(self):
        '''
        Test whether it is possible to add fields via the add mode.
        '''
        view = self.view
        regions = list(self.start_regions)
        add_regions_list = [(16, 17), 54, 109]
        view.run_command('selection_fields', {'mode': 'add'})

        view.sel().clear()
        self.select_regions(add_regions_list)

        view.run_command('selection_fields', {'mode': 'add'})
        view.run_command('move', {'by': 'characters', 'forward': True})
        view.run_command('selection_fields',
                         {'mode': 'pop', 'only_other': True})

        # add the added regions and sort it to retrieve the desired selections
        regions.extend(map(to_region, add_regions_list))
        regions.sort(key=lambda sel: sel.begin())
        self.assertSelectionEqual(view.sel(), regions)

    def test_subtract(self):
        '''Test whether subtract fields works properly.'''
        view = self.view
        regions_list = [(16, 35), 54, 60, (100, 103)]
        subtract_regions_list = [(2, 10), (14, 20), 54, (99, 120)]
        result_regions_list = [(20, 35), 60]

        self.select_regions(regions_list)

        view.run_command('selection_fields', {'mode': 'add'})

        self.select_regions(subtract_regions_list)

        view.run_command('selection_fields', {'mode': 'subtract'})

        view.run_command('selection_fields',
                         {'mode': 'pop', 'only_other': True})

        # add the added regions and sort it to retrieve the desired selections
        regions = list(map(to_region, result_regions_list))
        self.assertSelectionEqual(view.sel(), regions)
