import sublime, sublime_plugin
import re


class MultiFindAllCommand(sublime_plugin.TextCommand):

	def run(self, edit):

		view = self.view

		for region in view.sel():
			substr = view.substr(region)
			for region in view.find_all(substr, sublime.LITERAL):
				view.sel().add(region)



class JumpToLastRegionCommand(sublime_plugin.TextCommand):

	def run(self, edit):

		selection = self.view.sel()
		lastRegion = selection[-1]
		cursorPosition = lastRegion.b
		selection.clear()
		selection.add(sublime.Region(cursorPosition))
		self.view.show(cursorPosition, False)


class AddLastSelectionCommand(sublime_plugin.TextCommand):

	def run(self, edit):

		helper = Helper.getOrConstructHelperForView(self.view)
		lastSelections = helper.lastSelections

		if len(lastSelections) < 1:
			return

		currentSelection = self.view.sel()
		oldSelectionHash = Helper.hashSelection(currentSelection)

		for region in lastSelections[-1]:
			helper.ignoreSelectionCommand = True
			currentSelection.add(region)

		newSelectionHash = Helper.hashSelection(currentSelection)

		lastSelections.pop(-1)

		nothingChanged = oldSelectionHash == newSelectionHash
		if nothingChanged:
			# Rerun if the previous selection was only a subset of the current selection.
			self.run(edit)


class CycleThroughRegionsCommand(sublime_plugin.TextCommand):

	def run(self, edit):

		view = self.view
		visibleRegion = view.visible_region()
		selectedRegions = view.sel()

		if not len(selectedRegions):
			return

		nextRegion = None

		# Find the first region which comes after the visible region.
		for region in selectedRegions:
			if region.end() > visibleRegion.b:
				nextRegion = region
				break

		# If the last region in the buffer was reached, take the first region.
		# Empty regions will be evaluated falsy, which is why short-circuit evaluation doesn't work here.
		if nextRegion is None:
			nextRegion = selectedRegions[0]

		view.show(nextRegion, False)



class NormalizeRegionEndsCommand(sublime_plugin.TextCommand):

	def run(self, edit):

		view = self.view
		selection = view.sel()

		if not len(selection):
			return

		if self.areRegionsNormalized(selection):
			regions = self.invertRegions(selection)
		else:
			regions = self.normalizeRegions(selection)

		selection.clear()
		for region in regions:
			selection.add(region)

		firstVisibleRegion = self.findFirstVisibleRegion()
		if firstVisibleRegion is not None:
			# if firstVisibleRegion won't work with empty regions
			view.show(firstVisibleRegion.b, False)


	def findFirstVisibleRegion(self):

		visibleRegion = self.view.visible_region()

		for region in self.view.sel():
			if region.intersects(visibleRegion):
				return region

		return None


	def normalizeRegions(self, regions):

		return self.invertRegions(regions, lambda region: region.a > region.b)


	def invertRegions(self, regions, condition = lambda region: True):

		invertedRegions = []

		for region in regions:
			invertedRegion = region
			if condition(region):
				invertedRegion = sublime.Region(region.b, region.a)

			invertedRegions.append(invertedRegion)

		return invertedRegions


	def areRegionsNormalized(self, regions):

		return all(region.a < region.b for region in regions)



class SplitSelectionCommand(sublime_plugin.TextCommand):

	def run(self, edit, separator = None):

		self.savedSelection = [r for r in self.view.sel()]

		selectionSize = sum(map(lambda region: region.size(), self.savedSelection))
		if selectionSize == 0:
			# nothing to do
			sublime.status_message("Cannot split an empty selection.")
			return

		if separator != None:
			self.splitSelection(separator)
		else:
			onConfirm, onChange = self.getHandlers()

			inputView = sublime.active_window().show_input_panel(
				"Separating character(s) for splitting the selection",
				" ",
				onConfirm,
				onChange,
				self.restoreSelection
			)

			inputView.run_command("select_all")


	def getHandlers(self):

		settings = sublime.load_settings("MultiEditUtils.sublime-settings")
		live_split_selection = settings.get("live_split_selection")

		if live_split_selection:
			onConfirm = None
			onChange = self.splitSelection
		else:
			onConfirm = self.splitSelection
			onChange = None

		return (onConfirm, onChange)


	def restoreSelection(self):

		selection = self.view.sel()
		selection.clear()
		for region in self.savedSelection:
			selection.add(region)

		self.workaroundForRefreshBug(self.view, selection)


	def splitSelection(self, separator):

		view = self.view
		newRegions = []

		for region in self.savedSelection:
			currentPosition = region.begin()
			regionString = view.substr(region)

			if separator:
				subRegions = regionString.split(separator)
			else:
				# take each character separately
				subRegions = list(regionString)

			for subRegion in subRegions:
				newRegion = sublime.Region(
					currentPosition,
					currentPosition + len(subRegion)
				)
				newRegions.append(newRegion)
				currentPosition += len(subRegion) + len(separator)

		selection = view.sel()
		selection.clear()
		for region in newRegions:
			selection.add(region)

		self.workaroundForRefreshBug(view, selection)


	def workaroundForRefreshBug(self, view, selection):
		# work around sublime bug with caret position not refreshing
		# see: https://github.com/code-orchestra/colt-sublime-plugin/commit/9e6ffbf573fc60b356665ff2ba9ced614c71120f

		bug = [s for s in selection]
		view.add_regions("bug", bug, "bug", "dot", sublime.HIDDEN | sublime.PERSISTENT)
		view.erase_regions("bug")



class StripSelection(sublime_plugin.TextCommand):

	def run(self, edit):

		newRegions = []
		selection = self.view.sel()

		for currentRegion in selection:

			text = self.view.substr(currentRegion)

			lStrippedText = text.lstrip()
			rStrippedText = lStrippedText.rstrip()

			lStrippedCount = len(text) - len(lStrippedText)
			rStrippedCount = len(lStrippedText) - len(rStrippedText)

			a = currentRegion.begin() + lStrippedCount
			b = currentRegion.end() - rStrippedCount

			if a == b:
				# the region only contained whitespace
				# use the old selection end to avoid jumping of cursor
				a = b = currentRegion.b

			newRegions.append(sublime.Region(a, b))


		selection.clear()
		for region in newRegions:
			selection.add(region)



class RemoveEmptyRegions(sublime_plugin.TextCommand):

	def run(self, edit):

		selection = self.view.sel()
		regions = list(selection)
		newRegions = list(filter(lambda r: not r.empty(), regions))

		if len(newRegions) == 0:
			sublime.status_message("There are only empty regions. Removing those would remove all regions. Aborting.")
			return

		selection.clear()
		for r in newRegions:
			selection.add(r)



class SelectionListener(sublime_plugin.EventListener):

	def on_selection_modified(self, view):

		helper = Helper.getOrConstructHelperForView(view)
		lastSelections = helper.lastSelections

		if helper.ignoreSelectionCommand:
			helper.ignoreSelectionCommand = False
			return

		currentSelection = view.sel()

		if self.isComplexSelection(currentSelection):

			currentRegions = list(currentSelection)
			selectionWasExpanded = lastSelections and self.isSubsetOf(currentSelection, lastSelections[-1])

			if selectionWasExpanded:
				# Override the last entry since the selection was expanded.
				lastSelections[-1] = currentRegions
			else:
				lastSelections.append(currentRegions)


	def isComplexSelection(self, selection):
		# A "complex selection" is a selection which is not empty or has multiple regions.

		regionCount = len(selection)

		if not regionCount:
			return False

		firstRegionLength = len(selection[0])

		return regionCount > 1 or firstRegionLength > 0


	def isSubsetOf(self, selectionA, selectionB):
		# Check if selectionA is a subset of selectionB.

		return all(selectionA.contains(region) for region in selectionB)



class TriggerSelectionModifiedCommand(sublime_plugin.TextCommand):

	def run(self, edit):

		SelectionListener().on_selection_modified(self.view)



class Helper:

	viewToHelperMap = {}

	def __init__(self):

		# The SelectionCommand should be ignored if it was triggered by AddLastSelectionCommand.
		self.ignoreSelectionCommand = False
		self.lastSelections = []


	@staticmethod
	def getOrConstructHelperForView(view):

		mapping = Helper.viewToHelperMap
		viewID = view.id()

		if not viewID in mapping.keys():
			mapping[viewID] = Helper()

		helper = mapping[viewID]
		return helper


	@staticmethod
	def hashSelection(selection):

		return str(list(selection))
