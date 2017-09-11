Sublime MultiEditUtils [![Build Status](https://travis-ci.org/philippotto/Sublime-MultiEditUtils.svg?branch=master)](https://travis-ci.org/philippotto/Sublime-MultiEditUtils)
==============

A Sublime Text 2/3 Plugin which enhances editing of multiple selections. In case you aren't familar with Sublime's awesome multiple selection features, visit [this page](https://www.sublimetext.com/docs/2/multiple_selection_with_the_keyboard.html).

## Features

### Preserve case while editing selection contents

When multi-selecting all occurences of an identifier it is cumbersome to change it to another one if the case differs (camelCase, PascalCase, UPPER CASE and even cases with separators like snake_case, dash-case, dot.case etc.). The "Preserve case" feature facilitates this. Just invoke "Preserve case" via the command palette (or define an own keybinding) and type in the new identifier.

![](http://philippotto.github.io/Sublime-MultiEditUtils/screens/preserve-case.gif)


### Split the selection

Sublime has a default command to split selections into lines, but sometimes you want to define your own splitting character(s). MultiEditUtils' ```split_selection``` command (default keybinding is **ctrl/cmd+alt+,**) will ask you for a separator and split the selection using your input. An empty separator will split the selection into its characters.

![](http://philippotto.github.io/Sublime-MultiEditUtils/screens/05%20split%20selection.gif)


### Extend the current selection with the last selection

Sometimes Sublime's standard features for creating multiple selections won't cut it. MultiEditUtils allows to select the desired parts individually and merge the selections with the ```add_last_selection``` command (default keybinding is **ctrl/cmd+alt+u**).

![](http://philippotto.github.io/Sublime-MultiEditUtils/screens/01%20expand%20with%20last%20region.gif)


### Normalize and toggle region ends

When creating selections in Sublime, it can occur that the end of the selection comes before the beginning. This happens when you make the selection "backwards". To resolve this, you can normalize the regions with MultiEditUtils' ```normalize_region_ends``` command (default keybinding is **ctrl/cmd+alt+n**). When executing this command a second time, all regions will be reversed.

![](http://philippotto.github.io/Sublime-MultiEditUtils/screens/02a%20normalize%20region%20ends.gif)

This feature can also be very handy when you want to toggle the selection end of a single region.

![](http://philippotto.github.io/Sublime-MultiEditUtils/screens/02b%20toggle%20selection%20end.gif)


### Jump to last region

When exiting multi selection mode, Sublime will set the cursor to the **first** region of your previous selection. This can be annoying if the regions were scattered throughout the current buffer and you want to continue your work at the **last** region. To avoid this, just execute MultiEditUtils' ```jump_to_last_region``` command (default keybinding is **shift+esc**) and the cursor will jump to the last region.

![](http://philippotto.github.io/Sublime-MultiEditUtils/screens/03%20jump%20to%20last%20region.gif)


### Cycle through the regions

In case you want to double check your current selections, MultiEditUtils' ```cycle_through_regions``` command (default keybinding is **ctrl/cmd+alt+c**) will let you cycle through the active regions. This can come handy if the regions don't fit on one screen and you want to avoid scrolling through the whole file.

![](http://philippotto.github.io/Sublime-MultiEditUtils/screens/04%20cycle%20through%20regions.gif)


### Strip selection

Sometimes selections contain surrounding whitespace which can get in the way of your editing. The ```strip_selection``` command strips the regions so that this whitespace gets removed. The default keybinding is **ctrl/cmd+alt+s**.

![](http://philippotto.github.io/Sublime-MultiEditUtils/screens/06%20strip%20selection.gif)


### Remove empty regions

When splitting your selection or performing other actions on your selection, it can happen that some regions are empty while others are not. Often only the non-empty regions are of interest. The ```remove_empty_regions``` commands will take care of this and remove all empty regions from your current selection. The default keybinding is **ctrl/cmd+alt+r**.

![](http://philippotto.github.io/Sublime-MultiEditUtils/screens/07%20remove%20empty%20selections.gif)


### Quick Find All for multiple selections

Similar to the built-in "Quick Find All" functionality, MultiEditUtils provides a functionality which selects all occurrences of all active selections. The default keybinding of the ```multi_find_all``` command is **ctrl+alt+f** (on Mac it's **cmd+alt+j**).

![](http://philippotto.github.io/Sublime-MultiEditUtils/screens/08%20multi%20find%20all.gif)


### Use selections as fields

Converts the selections to fields similar to the fields used in snippets. When the `selection_fields` command is executed, all current selections are saved as fields, which can be activated one by one. The first field is activated automatically. You can jump to the next field with **tab** (or the default keybinding) and to the previous field with **shift+tab**. If you jump behind the last field or press **escape** all fields will be converted to proper selections again. If you press **shift+escape** all fields will be removed and the current selection remains unchanged.

![demo_selection_fields](https://cloud.githubusercontent.com/assets/12573621/14402686/17391716-fe3d-11e5-8fba-4e52a4f93459.gif)

You can bind this command to a keybinding by adding the following to your keymap (Change the key to the keybinding you prefer):

``` js
{ "keys": ["alt+d"], "command": "selection_fields" },
```

Although using one keybinding with the default options should be sufficient for most cases, additional modes and arguments are possible. Feel free to ignore or use them as you wish.

Arguments:

- `mode` (`"smart"`) is the executing mode, which defines the executed action. Possible modes are:
    + `"push"` to push the current selection as fields. This will overwrite already pushed fields.
    + `"pop"` to pop the pushed fields as selections
    + `"remove"` to remove the pushed fields without adding them to the selection. This has the same behavior as pop if `only_other` is `true`.
    + `"add"` to add the current selection to the pushed fields
    + `"subtract"` to subtract the current selection from the pushed fields
    + `"smart"` to try to detect whether to push, pop or jump to the next field
    + `"toggle"` to pop if fields are pushed, else push the selections as fields.
    + `"cycle"` to push or go next. This will cycle, i.e. go to the first if the last field is reached, never pops
- `jump_forward` (`true`) can be `true` to jump forward and `false` to jump backward
- `only_other` (`false`) ignores the current selection for pop and go next actions.

Suggestion for more keybindings based on the arguments:

``` js
// default use of selection_fields
{ "keys": ["alt+d"], "command": "selection_fields" },
// add the current selections as a fields
{ "keys": ["alt+a"], "command": "selection_fields", "args": {"mode": "add"} },
// jump and remove current selection in selection_fields
{ "keys": ["ctrl+alt+d"], "command": "selection_fields",
  "args": {"mode": "smart", "only_other": true} },
// cancel selection_fields and remove current selection
{ "keys": ["ctrl+alt+shift+d"], "command": "selection_fields",
  "args": {"mode": "toggle", "only_other": true} },
```

## Installation

Either use [Package Control](https://sublime.wbond.net/installation) and search for `MultiEditUtils` or clone this repository into Sublime Text "Packages" directory.

## Shortcut Cheat Sheet

[![multieditutilscheatsheetmain](https://user-images.githubusercontent.com/2641327/27285539-57bd445c-54fd-11e7-867f-2e3a264c7d35.png)](https://github.com/philippotto/Sublime-MultiEditUtils/files/1084890/multiEditUtilsCheatsheetMain.pdf)

Thank you [@AllanLRH](https://github.com/AllanLRH) for creating this cheat sheet!

## License

MIT © Philipp Otto
