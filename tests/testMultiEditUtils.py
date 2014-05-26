import sublime
from unittest import TestCase

version = sublime.version()

class TestHelloWorld(TestCase):

	def setUp(self):

		self.view = sublime.active_window().new_file()


	def runCommand(self, commandName, argTuple = ()):

		self.view.run_command("test_multi_edit_utils", dict(commandName = commandName, argTuple = argTuple))


	def tearDown(self):

		if self.view:
			self.view.set_scratch(True)
			self.view.window().run_command("close_file")


	def splitBy(self, separator, expectedAmount):

		testString = "this, is, a, test"
		self.runCommand("insertSomeText", (testString, ))
		self.runCommand("selectText")
		self.view.run_command("split_selection", dict(separator = separator))

		selection = self.view.sel()

		self.assertEqual(len(selection), expectedAmount)


	def testSplitBySpace(self):

		self.splitBy(" ", 4)


	def testSplitByCommaSpace(self):

		self.splitBy(", ", 4)


	def testSplitByCharacter(self):

		self.splitBy("", 17)


	def testToggleRegionEnds(self):

		testString = "this is a test"
		self.runCommand("insertSomeText", (testString, ))

		regionTuple = (0, 14)
		self.runCommand("selectText", [regionTuple])

		selection = self.view.sel()
		self.assertRegionEqual(selection[0], regionTuple)

		self.view.run_command("normalize_region_ends")

		self.assertRegionEqual(selection[0], regionTuple[::-1])


	def testToggleRegionEnds(self):

		testString = "test test"
		self.runCommand("insertSomeText", (testString, ))

		regionTuples = [(0, 4), (9, 5)]
		self.runCommand("selectText", regionTuples)

		selection = self.view.sel()
		self.assertRegionEqual(selection[0], regionTuples[0])
		self.assertRegionEqual(selection[1], regionTuples[1])

		self.view.run_command("normalize_region_ends")

		self.assertRegionEqual(selection[0], regionTuples[0])
		self.assertRegionEqual(selection[1], regionTuples[1][::-1])


	def testJumpToLastRegion(self):

		testString = "test test test test"
		self.runCommand("insertSomeText", (testString, ))

		self.runCommand("selectText", [(0, 4), (5, 9)])

		selection = self.view.sel()
		self.assertEqual(len(selection), 2)

		self.view.run_command("jump_to_last_region")

		self.assertEqual(len(selection), 1)
		self.assertRegionEqual(selection[0], (5, 5))


	def testAddLastSelection(self):

		testString = "this is a test"
		self.runCommand("insertSomeText", (testString, ))

		regions = [(0, 4), (5, 9)]
		self.runCommand("selectText", [regions[0]])
		self.runCommand("selectText", [regions[1]])

		self.view.run_command("add_last_selection")

		selection = self.view.sel()


		self.assertEqual(len(selection), 2)
		self.assertRegionEqual(selection[0], regions[0])
		self.assertRegionEqual(selection[1], regions[1])


	def assertRegionEqual(self, a, b):

		self.assertEqual(a.a, b[0])
		self.assertEqual(a.b, b[1])

