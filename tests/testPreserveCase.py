import sublime
from unittest import TestCase

import os.path, sys
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))

import MultiEditUtils.MultiEditUtils


class TestPreserveCase(TestCase):

  def setUp(self):

    self.view = sublime.active_window().new_file()
    self.cmd = MultiEditUtils.PreserveCaseCommand(None)

  def tearDown(self):

    if self.view:
      self.view.set_scratch(True)
      self.view.window().run_command("close_file")

  def assertListEqual(self, listA, listB):

    self.assertEqual(len(listA), len(listB))

    for idx, el in enumerate(listA):
      self.assertEqual(el, listB[idx])


  def testAnalyzeString(self):

    meta = self.cmd.analyzeString("a-BU-Cap-MiX")

    Case = MultiEditUtils.Case

    self.assertEqual(meta.separator, "-")
    self.assertListEqual(meta.cases, [Case.lower, Case.upper, Case.capitalized, Case.mixed])
    self.assertListEqual(meta.stringGroups, ["a", "BU", "Cap", "MiX"])


  def testSplitByCase(self):

    self.assertListEqual(self.cmd.splitByCase("abcDefGhi"), ["abc", "Def", "Ghi"])
    self.assertListEqual(self.cmd.splitByCase("AbcDefGhi"), ["Abc", "Def", "Ghi"])
    self.assertListEqual(self.cmd.splitByCase("AbcDEF"), ["Abc", "DEF"])
    self.assertListEqual(self.cmd.splitByCase("ABCDef"), ["ABCD", "ef"])
    self.assertListEqual(self.cmd.splitByCase("AbcDEFGhi"), ["Abc", "DEFG", "hi"])



  def testReplaceStringWithCase_Equal(self):

    oldString = "test-TEST-Test"
    newStringGroups = ["case", "case", "case"]
    replacedString = self.cmd.replaceStringWithCase(oldString, newStringGroups)

    self.assertEqual(replacedString, "case-CASE-Case")

  def testReplaceStringWithCase_Less(self):

    oldString = "test-TEST-Test"
    newStringGroups = ["case", "case"]
    replacedString = self.cmd.replaceStringWithCase(oldString, newStringGroups)

    self.assertEqual(replacedString, "case-CASE")


  def testReplaceStringWithCase_More(self):

    oldString = "test-TEST-Test"
    newStringGroups = ["case", "case", "case", "case"]
    replacedString = self.cmd.replaceStringWithCase(oldString, newStringGroups)

    self.assertEqual(replacedString, "case-CASE-Case-Case")
