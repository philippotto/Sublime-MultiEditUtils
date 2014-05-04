MultiEditUtils
==============

A Sublime Test 3 Plugin which enhances editing of multiple selections. In case you aren't familar with Sublime's awesome multiple selection features, visit [this page](https://www.sublimetext.com/docs/2/multiple_selection_with_the_keyboard.html).


## Extend the current selection with the last selection

Sometimes Sublime's standard features for creating multiple selections won't cut it. MultiEditUtils allows to select the desired parts individually and merge the selections with one hotkey (**ctrl+alt+u**)

![](http://philippotto.github.io/Sublime-MultiEditUtils/screens/01%20expand%20with%20last%20region.gif)


## Normalize and toggle region ends

When creating selections in Sublime, it can occur that the end of the selection comes before the beginning. This happens when you make the selection "backwards". To resolve this, you can normalize the regions with MultiEditUtils' **ctrl+alt+n** command. When executing this command a second time, all regions will be reversed.

![](http://philippotto.github.io/Sublime-MultiEditUtils/screens/02a%20normalize%20region%20ends.gif)

This feature can also be very handy when you want to toggle the selection end of a single region.

![](http://philippotto.github.io/Sublime-MultiEditUtils/screens/02b%20toggle%20selection%20end.gif)


## Jump to last region

When exiting multi selection mode, Sublime will set the cursor to the **first** region of your previous selection. This can be annoying if the regions were scattered throughout the current buffer and you want to continue your work at the **last** region. To avoid this, just execute MultiEditUtils' **shift+esc** command and the cursor will jump to the last region.

![](http://philippotto.github.io/Sublime-MultiEditUtils/screens/03%20jump%20to%20last%20region.gif)


## Cycle through the regions

In case you want to double check your current selections, MultiEditUtils' **ctrl+alt+c** command will let you cycle through the active regions. This can come handy if the regions don't fit on one screen and you want to avoid scrolling through the whole file.

![](http://philippotto.github.io/Sublime-MultiEditUtils/screens/04%20cycle%20through%20regions.gif)


## Split the selection

Sublime has a default command to split selections into lines, but sometimes you want to define your own splitting character(s). MultiEditUtils' **ctrl+alt+,** command will ask you for a separator and split the selection using your input. An empty separator will split the selection into its characters.

![](http://philippotto.github.io/Sublime-MultiEditUtils/screens/05%20split%20selection.gif)
