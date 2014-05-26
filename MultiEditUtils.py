import sublime, sublime_plugin


class JumpToLastRegionCommand(sublime_plugin.TextCommand):

	def run(self, edit):

		selection = self.view.sel()
		lastRegion = selection[-1]
		cursorPosition = lastRegion.begin()
		selection.clear()
		selection.add(sublime.Region(cursorPosition))



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
			if max(region.a, region.b) > visibleRegion.b:
				nextRegion = region
				break

		# If the last region in the buffer was reached, take the first region.
		nextRegion = nextRegion or selectedRegions[0]

		view.show(nextRegion, False)



class NormalizeRegionEndsCommand(sublime_plugin.TextCommand):

	def run(self, edit):

		view = self.view
		selection = view.sel()
		if self.areRegionsNormalized(selection):
			regions = self.invertRegions(selection)
		else:
			regions = self.normalizeRegions(selection)

		selection.clear()
		for region in regions:
			selection.add(region)


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

	def run(self, edit):

		self.savedSelection = [r for r in self.view.sel()]
		onConfirm, onChange = self.getHandlers()

		sublime.active_window().show_input_panel(
			"Separating character(s) for splitting the selection",
			"",
			onConfirm,
			onChange,
			self.restoreSelection
		)


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
		# see:
		# https://github.com/code-orchestra/colt-sublime-plugin/commit/9e6ffbf573fc60b356665ff2ba9ced614c71120f

		# work around sublime bug with caret position not refreshing
		bug = [s for s in selection]
		view.add_regions("bug", bug, "bug", "dot", sublime.HIDDEN | sublime.PERSISTENT)
		view.erase_regions("bug")



class SelectionListener(sublime_plugin.EventListener):

	def on_selection_modified(self, view):

		helper = Helper.getOrConstructHelperForView(view)
		lastSelections = helper.lastSelections

		if helper.ignoreSelectionCommand:
			helper.ignoreSelectionCommand = False
			return

		currentSelection = view.sel()

		if self.isComplexSelection(currentSelection):

			currentRegions = [region for region in currentSelection]
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

		return str([region for region in selection])
