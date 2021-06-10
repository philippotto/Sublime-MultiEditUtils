import sublime
import sublime_plugin
import re
from datetime import datetime
import uuid
import html
from collections import namedtuple

from .selection_fields import get_settings
from .utils import get_new_regions

COMMENT_SELECTOR = "comment - punctuation.definition.comment"

MULTI_FIND_MENU = [
    sublime.ListInputItem("Case +    Word +", 0,
                          '<strong>Matches:</strong> <em>case, word</em>'),
    sublime.ListInputItem("Case +    Word -",
                          1, '<strong>Matches:</strong> <em>case</em> <strong>Ignores:</strong> <em>word</em>'),
    sublime.ListInputItem("Case -    Word +",
                          2, '<strong>Matches:</strong> <em>word</em> <strong>Ignores:</strong> <em>case</em>'),
    sublime.ListInputItem("Case -    Word -",
                          3, '<strong>Ignores:</strong> <em>case, word</em>'),
    sublime.ListInputItem(
        "Case +    Word +  Comments -", 4, '<strong>Matches:</strong> <em>case, word</em>\t<strong>Ignores:</strong> <em>matches inside comments</em>')
]


class MultiFindMenuCommand(sublime_plugin.TextCommand):

    def run(self, edit, operation):
        if operation == 0:
            self.view.run_command(
                'multi_find_all', {"case": True, "word": True})
        elif operation == 1:
            self.view.run_command('multi_find_all', {"case": True})
        elif operation == 2:
            self.view.run_command(
                'multi_find_all', {"case": False, "word": True})
        elif operation == 3:
            self.view.run_command('multi_find_all', {"case": False})
        elif operation == 4:
            self.view.run_command(
                'multi_find_all', {"case": True, "word": True,
                                   "ignore_comments": True})

    def input(self, args):
        return MultiFindInputHandler()


class MultiFindInputHandler(sublime_plugin.ListInputHandler):
    def name(self):
        return "operation"

    def list_items(self):
        return MULTI_FIND_MENU


class MultiFindAllCommand(sublime_plugin.TextCommand):
    def run(self, edit, case=True, word=False, ignore_comments=False, expand=True):
        view = self.view
        new_regions = []

        # filter selections in order to exclude duplicates since it can hang
        # Sublime if search is performed on dozens of selections, this doesn't
        # happen with built-in command because it works on a single selection
        initial = [sel for sel in view.sel()]
        regions, substrings = [], []
        for region in view.sel():
            if expand and region.empty():
                # if expanding substring will be the word
                region = view.word(region.a)
                # add the region since nothing is selected yet
                view.sel().add(region)
            # filter by substring (word or not)
            substr = view.substr(region)
            if substr and substr not in substrings:
                regions.append(region)
                substrings.append(substr)
        view.sel().clear()
        if regions:
            for region in regions:
                view.sel().add(region)
        else:
            view.window().status_message("Multi Find All: nothing selected")
            for sel in initial:
                view.sel().add(sel)
            return

        selected_words = [view.substr(view.word(sel)).lower()
                          for sel in view.sel()]

        for region in view.sel():
            substr = view.substr(region)

            if case:
                for region in view.find_all(substr, sublime.LITERAL):
                    new_regions.append(region)
            else:
                for region in view.find_all(substr, sublime.LITERAL | sublime.IGNORECASE):
                    new_regions.append(region)

            if word:
                deleted = [region for region in new_regions
                           if view.substr(view.word(region)).lower() not in selected_words]
                new_regions = [
                    region for region in new_regions if region not in deleted]

            if ignore_comments:
                deleted = [region for region in new_regions
                           if view.score_selector(region.a, COMMENT_SELECTOR) > 0]
                new_regions = [
                    region for region in new_regions if region not in deleted]

        for region in new_regions:
            view.sel().add(region)


class MultiFindRegexCommand(sublime_plugin.TextCommand):
    def run(self, edit, subtractive, expression, case=True):
        case = sublime.IGNORECASE if not case else 0
        regions = self.view.find_all(expression, case)

        if subtractive:
            for region in regions:
                self.view.sel().subtract(region)
        elif not subtractive:
            for region in regions:
                self.view.sel().add(region)
        else:
            return

        [self.view.sel().subtract(r) for r in self.view.sel() if r.empty()]

    def input(self, args):
        if args.get('subtractive', None):
            return ExpressionInputHandler(self.view, args)
        return OperationInputHandler(self.view)


class OperationInputHandler(sublime_plugin.ListInputHandler):
    def __init__(self, view) -> None:
        self.view = view

    def name(self):
        return "subtractive"

    def list_items(self):
        return [
            sublime.ListInputItem(
                'Additive', False,  '<strong>Logic:</strong> <em>adds matches to current selection</em>'),
            sublime.ListInputItem(
                'Subtractive', True,  '<strong>Logic:</strong> <em>removes matches from current selection</em>')
        ]

    def next_input(self, args):
        return ExpressionInputHandler(self.view, args)


class ExpressionInputHandler(sublime_plugin.TextInputHandler):
    def __init__(self, view, args):
        self.view = view
        self.args = args

    def confirm(self, arg):
        self.view.erase_regions(
            'meu_expression_preview')
        return arg

    def preview(self, value):
        if value == '':
            self.view.erase_regions('meu_expression_preview')
            return

        operation = "Subtractive" if self.args.get(
            "subtractive", False) else "Additive"

        if operation == "Additive":
            preview_scope = get_settings(
                "find.regex.additive.scope", 'region.greenish')
        else:
            preview_scope = get_settings(
                "find.regex.subtractive.scope", 'region.redish')

        regions = self.view.find_all(value, 0)

        if operation == 'Additive':
            regions = [r for r in regions if not self.view.sel().contains(r)]
        else:
            regions = [r for r in regions if self.view.sel().contains(r)]

        self.view.add_regions(
            'meu_expression_preview', [s for s in regions], preview_scope, '',
            sublime.DRAW_NO_FILL | sublime.PERSISTENT)

        return sublime.Html(
            f'<strong>{operation} Expression:</strong>' +
            f' <em>{html.escape(value)}</em><br/>' +
            f'<strong>Selections:</strong> <em>{len(regions)}</em>'
        )

    def cancel(self):
        self.view.erase_regions(
            'meu_expression_preview')


class JumpToLastRegionCommand(sublime_plugin.TextCommand):

    def run(self, edit, clear_selection=True):
        last_region_point = self.view.sel()[-1].b

        if clear_selection:
            self.view.sel().clear()

        self.view.sel().add(sublime.Region(last_region_point))
        self.view.show(last_region_point, True)


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
            # Rerun if the previous selection was only a subset of the current
            # selection.
            self.run(edit)


class CycleThroughRegionsCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        view = self.view
        visible_region = view.visible_region()
        selectedRegions = view.sel()

        if not len(selectedRegions):
            return

        next_region = None

        # Find the first region which comes after the visible region.
        for region in selectedRegions:
            if region.end() > visible_region.b:
                next_region = region
                break

        # If the last region in the buffer was reached, take the first region.
        # Empty regions will be evaluated falsy, which is why short-circuit
        # evaluation doesn't work here.
        if next_region is None:
            next_region = selectedRegions[0]

        view.show(next_region, False)


class NormalizeRegionEndsCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        view = self.view
        selection = view.sel()

        if not len(selection):
            return

        if self.are_regions_normalized(selection):
            regions = self.invert_regions(selection)
        else:
            regions = self.normalize_regions(selection)

        selection.clear()
        for region in regions:
            selection.add(region)

        firstVisibleRegion = self.find_first_visible_region()
        if firstVisibleRegion is not None:
            # if firstVisibleRegion won't work with empty regions
            view.show(firstVisibleRegion.b, False)

    def find_first_visible_region(self):
        visibleRegion = self.view.visible_region()

        for region in self.view.sel():
            if region.intersects(visibleRegion):
                return region

        return None

    def normalize_regions(self, regions):
        return self.invert_regions(regions, lambda region: region.a > region.b)

    def invert_regions(self, regions, condition=lambda region: True):
        inverted_regions = []

        for region in regions:
            invertedRegion = region
            if condition(region):
                invertedRegion = sublime.Region(region.b, region.a)

            inverted_regions.append(invertedRegion)

        return inverted_regions

    def are_regions_normalized(self, regions):
        return all(region.a < region.b for region in regions)


class SplitSelectionCommand(sublime_plugin.TextCommand):

    def run(self, edit, separator=None):
        self.live_split_preview = get_settings(
            "live_split_selection.enabled", True)
        self.live_split_preview_scope = get_settings(
            "live_split_selection.scope", 'region.cyanish')

        self.savedSelection = [r for r in self.view.sel()]

        selectionSize = sum(
            map(lambda region: region.size(), self.savedSelection)
        )
        if selectionSize == 0:
            # nothing to do
            sublime.status_message("Cannot split an empty selection.")
            return

        if separator is not None:
            self.split_selection(False, separator)
        else:
            inputView = sublime.active_window().show_input_panel(
                "Separating character(s) for splitting the selection",
                " ",
                lambda x: self.split_selection(False,  x),
                lambda x: self.split_selection(self.live_split_preview, x),
                self.clear_split_regions
            )

            inputView.run_command("select_all")

    def clear_split_regions(self):
        self.view.erase_regions('meu_split_preview')

    def split_selection(self, preview, separator):
        view = self.view
        new_regions = []

        for region in self.savedSelection:
            currentPosition = region.begin()
            regionString = view.substr(region)

            if separator:
                subRegions = regionString.split(separator)
            else:
                # take each character separately
                subRegions = list(regionString)

            for subRegion in subRegions:
                new_region = sublime.Region(
                    currentPosition,
                    currentPosition + len(subRegion)
                )
                new_regions.append(new_region)
                currentPosition += len(subRegion) + len(separator)

        if preview:
            view.add_regions('meu_split_preview', [s for s in new_regions], self.live_split_preview_scope, '',
                             sublime.DRAW_NO_FILL | sublime.PERSISTENT)
            return

        selection = view.sel()
        selection.clear()
        for region in new_regions:
            selection.add(region)

        self.clear_split_regions()


class StashRegionSelectionsCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        stashed_regions = self.view.settings().get('meu_pop_stashed_regions', {})
        next_key = str(uuid.uuid4())

        regions = self.view.sel()
        self.view.add_regions(f'meu_pop_stashed_regions_{next_key}', regions,
                              f'meu_pop_stashed_regions_{next_key}', '',
                              sublime.HIDDEN | sublime.PERSISTENT)

        stashed_regions[
            f'{next_key}'] = f'Total of <strong>{len(regions)}</strong> selections|Stashed at: {str(datetime.now())}'

        self.view.settings().set('meu_pop_stashed_regions', stashed_regions)
        self.view.sel().clear()


class PopRegionSelectionsCommand(sublime_plugin.TextCommand):
    def run(self, edit, index):
        self.pop_regions(index, True)

    def pop_regions(self, key, clear):
        if key == -1:
            return

        popped_regions = self.view.get_regions(
            f'meu_pop_stashed_regions_{key}')
        if clear:
            self.view.sel().clear()

        self.view.sel().add_all(popped_regions)
        self.view.erase_regions(
            f'meu_pop_stashed_regions_{key}')
        stashed_regions = self.view.settings().get('meu_pop_stashed_regions', {})
        stashed_regions.pop(key)
        self.view.settings().set('meu_pop_stashed_regions', stashed_regions)

    def input(self, args):
        return StashListInputHandler(self.view)

    def is_visible(self):
        return bool(self.view.settings().get('meu_pop_stashed_regions', {}))


class ClearStashedSelectionsCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        self.view.settings().erase('meu_pop_stashed_regions')


class StashListInputHandler(sublime_plugin.ListInputHandler):
    def __init__(self, view):
        self.view = view

    def name(self):
        return 'index'

    def list_items(self):
        stashed_regions = self.view.settings().get('meu_pop_stashed_regions', {})
        options = [
            sublime.ListInputItem(f'Item: {key}', key, f'<em>{stashed_regions[key].split("|")[0]}</em>', stashed_regions[key].split('|')[1]) for key in stashed_regions.keys()
        ]
        return options

    def preview(self, args):
        regions = self.view.get_regions(f'meu_pop_stashed_regions_{args}')
        self.view.erase_regions('meu_pop_stashed_region_preview')
        self.view.add_regions('meu_pop_stashed_region_preview',
                              regions, 'region.cyanish', '', sublime.DRAW_NO_FILL)

    def cancel(self):
        self.view.erase_regions('meu_pop_stashed_region_preview')

    def validate(self, args):
        self.view.erase_regions('meu_pop_stashed_region_preview')
        return True


Case = namedtuple("Case", "lower upper capitalized mixed")(1, 2, 3, 4)
StringMetaData = namedtuple("StringMetaData", "separator cases stringGroups")


class PreserveCaseCommand(sublime_plugin.TextCommand):

    def run(self, edit, newString=None, selections=None):
        self.edit = edit
        if selections is not None:
            self.savedSelection = [sublime.Region(
                r[0], r[1]) for r in selections]
        else:
            self.savedSelection = [r for r in self.view.sel()]

        selectionSize = sum(
            map(lambda region: region.size(), self.savedSelection)
        )
        if selectionSize == 0:
            sublime.status_message(
                "Cannot run preserve case on an empty selection.")
            return

        if newString is not None:
            self.preserveCase(newString)
        else:
            firstRegionString = self.view.substr(self.savedSelection[0])
            inputView = sublime.active_window().show_input_panel(
                "New string for preserving case",
                firstRegionString,
                self.runPreserveCase,
                None,
                None
            )
            inputView.run_command("select_all")

    def runPreserveCase(self, newString):
        selections = [[s.a, s.b] for s in self.savedSelection]
        self.view.run_command(
            "preserve_case", {"newString": newString, "selections": selections})

    def preserveCase(self, newString):
        view = self.view
        regionOffset = 0
        newStringGroups = self.analyzeString(newString).stringGroups

        for region in self.savedSelection:
            region = sublime.Region(
                region.begin() + regionOffset, region.end() + regionOffset)
            regionString = view.substr(region)

            newRegionString = self.replaceStringWithCase(
                regionString, newStringGroups)
            view.replace(self.edit, region, newRegionString)
            regionOffset += len(newRegionString) - len(regionString)

    def analyzeString(self, aString):
        separators = "-_/. "
        counts = list(map(lambda sep: aString.count(sep), separators))
        maxCounts = max(counts)

        if max(counts) > 0:
            separator = separators[counts.index(maxCounts)]
            stringGroups = aString.split(separator)
        else:
            # no real separator
            separator = ""
            stringGroups = self.splitByCase(aString)

        cases = list(map(self.analyzeCase, stringGroups))

        return StringMetaData(separator, cases, stringGroups)

    def splitByCase(self, aString):
        # split at the change from lower to upper case (or vice versa)
        # groups = re.split('(?<!^)((?:[^A-Z][A-Z])|(?:[A-Z]{2,}[^A-Z]))', aString)
        groups = re.split('(?<!^)((?:[^A-Z][^a-z])|(?:[^a-z][^A-Z]))', aString)
        newGroups = [groups[0]]
        for index, group in enumerate(groups):
            if index % 2 == 1:
                newGroups[-1] += group[0:-1]
                newGroups.append(group[-1] + groups[index + 1])

        return newGroups

    def analyzeCase(self, aString):
        lowerReg = re.compile("^[^A-Z]*$")
        upperReg = re.compile("^[^a-z]*$")
        capitalizedReg = re.compile("^[A-Z]([^A-Z])*$")

        if lowerReg.match(aString):
            return Case.lower
        elif upperReg.match(aString):
            return Case.upper
        elif capitalizedReg.match(aString):
            return Case.capitalized
        else:
            return Case.mixed

    def replaceStringWithCase(self, oldString, newStringGroups):
        analyzedOldString = self.analyzeString(oldString)
        oldCases = analyzedOldString.cases
        oldSeparator = analyzedOldString.separator

        for index, currentElement in enumerate(newStringGroups):
            # If the user provides more new strings than old ones are given, we
            # just repeat the last case.
            clampedIndex = min(index, len(oldCases) - 1)
            currentCase = oldCases[clampedIndex]

            if currentCase == Case.upper:
                newStringGroups[index] = currentElement.upper()
            elif currentCase == Case.lower:
                newStringGroups[index] = currentElement.lower()
            elif currentCase == Case.capitalized:
                newStringGroups[index] = currentElement.capitalize()

        return oldSeparator.join(newStringGroups)


class StripSelection(sublime_plugin.TextCommand):

    def run(self, edit):
        newRegions = []
        selections = self.view.sel()

        for selection in selections:

            text = self.view.substr(selection)
            if selection.empty() or text.isspace():
                # the region only contained whitespace
                # use the old selection end to avoid jumping of cursor
                a = b = selection.b
            else:
                leading_spaces = len(text) - len(text.lstrip())
                trailing_spaces = len(text) - len(text.rstrip())

                a = selection.begin() + leading_spaces
                b = selection.end() - trailing_spaces

            newRegions.append(sublime.Region(a, b))

        selections.clear()
        for region in newRegions:
            selections.add(region)


class RemoveEmptyRegions(sublime_plugin.TextCommand):

    def run(self, edit, restore_if_all_empty=True):
        old_selection = [selection for selection in self.view.sel()]
        [
            self.view.sel().subtract(selection)
            for selection in self.view.sel()
            if selection.empty()
        ]

        if (
            len(self.view.sel()) == 1 and
            self.view.sel()[0].empty() and
            restore_if_all_empty
        ):
            self.view.sel().add_all(old_selection)


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
            selectionWasExpanded = lastSelections and self.isSubsetOf(
                currentSelection, lastSelections[-1])

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


class JumpToCommand(sublime_plugin.TextCommand):
    def run(self, edit, text, extend=False, create_new=False, whole_match=False):
        new_regions = get_new_regions(self.view, text, whole_match, extend)
        selection = self.view.sel()
        if not create_new:
            selection.clear()
        selection.add_all(new_regions)


class JumpToInteractiveCommand(sublime_plugin.WindowCommand):
    ADDREGIONS_KEY = "JumpTo"
    ADDREGIONS_SCOPE = "jumpto"
    ADDREGIONS_FLAGS = sublime.DRAW_EMPTY | sublime.DRAW_OUTLINED

    def run(self, text="", extend=False, create_new=False, whole_match=False):
        self.params = {'extend': extend, 'create_new': create_new, 'whole_match': whole_match}
        self.view = self.window.active_view()

        if extend:
            prompt = "Expand selection to"
        elif create_new:
            prompt = "Create caret at"
        else:
            prompt = "Jump to"
        prompt += " (chars or [chars] or {count} or /regex/):"

        self.window.show_input_panel(prompt, text, self._on_done, self._on_change, self._on_cancel)

    def _show_highlight(self, regions):
        if not regions:
            self.view.erase_regions(self.ADDREGIONS_KEY)
        else:
            self.view.add_regions(self.ADDREGIONS_KEY, regions,
                                  self.ADDREGIONS_SCOPE, "", self.ADDREGIONS_FLAGS)

    def _on_done(self, text):
        self._show_highlight(None)
        # Run the command to create a proper undo point
        args = self.params.copy()
        args['text'] = text
        self.view.run_command("jump_to", args)

    def _on_change(self, text):
        regions = list(get_new_regions(self.view, text, **self.params))
        if self.params['create_new']:
            regions += list(self.view.sel())
        self._show_highlight(tuple(regions))

    def _on_cancel(self):
        self._show_highlight(None)


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

        if viewID not in mapping.keys():
            mapping[viewID] = Helper()

        helper = mapping[viewID]
        return helper

    @staticmethod
    def hashSelection(selection):
        return str(list(selection))
