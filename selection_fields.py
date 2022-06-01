import sublime
import sublime_plugin

_FLAGS = sublime.DRAW_EMPTY | sublime.DRAW_NO_FILL


def get_settings(key, default=None):
    """Get the setting specified by the key."""
    settings = sublime.load_settings('MultiEditUtils.sublime-settings')
    return settings.get(key, default)


def _get_settings(key, default=None):
    """
    Get the setting specified by the key,
    with the prefix `selection_fields.`.
    '''
    return get_settings('selection_fields.{0}'.format(key), default)


def _set_fields(view, regions, added_fields=False):
    """Set the fields as regions in the view."""
    # push the fields to the view
    if not added_fields:
        reg_name = 'meu_sf_stored_selections'
        scope_setting = 'scope.fields'
    else:
        reg_name = 'meu_sf_added_selections'
        scope_setting = 'scope.added_fields'
    scope = _get_settings(scope_setting, 'comment')
    view.add_regions(reg_name, regions, scope=scope, flags=_FLAGS)


def _get_fields(view, added_fields=True):
    fields = view.get_regions('meu_sf_stored_selections')
    if added_fields:
        fields.extend(view.get_regions('meu_sf_added_selections'))
    return fields


def _erase_added_fields(view):
    view.erase_regions('meu_sf_added_selections')


def _erase_fields(view):
    view.erase_regions('meu_sf_stored_selections')
    view.erase_regions('meu_sf_added_selections')
    view.erase_status('meu_field_message')


def _change_selection(view, regions, pos):
    """Extract the next selection, push all other fields."""
    # save and remove the position in the regions
    sel = regions[pos]
    del regions[pos]
    # add the regions as fields to the view
    _set_fields(view, regions)
    # add a feedback to the statusbar
    if len(regions) >= 1:
        view.set_status('meu_field_message',
                        f'Selection-Field {pos + 1} of {len(regions) + 1}')
                        .format(pos + 1, len(regions) + 1))
    else:
        view.erase_status("meu_field_message")
    # return the selection, which was at the position
    sel_regions = [sel]
    return sel_regions


def _restore_selection(view, only_other):
    """Restore the selection from the pushed fields."""
    sel_regions = _get_fields(view)
    if not only_other:
        sel_regions.extend(view.sel())
    _erase_fields(view)
    return sel_regions


def _execute_jump(view, jump_forward, only_other):
    """
    Add the selection to the fields and move the selection to the
    next field.
    """
    regions = _get_fields(view)

    try:
        # search for the first field, which is behind the last selection
        end = max(sel.end() for sel in view.sel())
        pos = next(i for i, sel in enumerate(regions) if sel.begin() > end)
    except:
        # if there is no remaining field move the position behind the regions
        pos = len(regions)
    # insert the selection into the region
    if only_other:
        sel_count = 0
    else:
        sel_count = len(view.sel())
        if sel_count == 1:
            # handle special case of one selection
            regions.insert(pos, view.sel()[0])
        else:
            # put the selections into the regions array
            regions = regions[:pos] + list(view.sel()) + regions[pos:]
    # the forward jump must jump over all added selections
    delta = sel_count if jump_forward else -1
    # move the position to the next field
    pos = pos + delta
    return regions, pos


def _subtract_selection(pushed_regions, sel_regions):
    """Subtract the selections from the pushed fields."""
    for reg in pushed_regions:
        for sel in sel_regions:
            if sel.begin() <= reg.end() and reg.begin() <= sel.end():
                # yield the region from the start of the field to the selection
                if reg.begin() < sel.begin():
                    yield sublime.Region(reg.begin(), sel.begin())
                # update the region to be from the end of the selection to
                # the end of the field
                reg = sublime.Region(sel.end(), reg.end())
                # if the region is not forward, break and don't add it as field
                if not reg.a < reg.b:
                    break
        else:
            # yield the region as field
            yield reg


_valid_modes = [
    'push',  # push the current selection as fields, overwrite existing fields
    'pop',  # pop the pushed field and add them to the selection
    'remove',  # pop the pushed field without adding them to the selection
               # same behavior as pop if only_other is true
    'add',  # add the current selection to the pushed fields
    'subtract',  # subtract the current selection from the pushed fields
    'smart',  # try to detect whether to push, pop or go next
    'toggle',  # pop if fields are pushed, else push
    'cycle'  # push or go next, go to first if at the end, never pop
]


class SelectionFieldsCommand(sublime_plugin.TextCommand):
    def run(self, edit, mode="smart", jump_forward=True, only_other=False):
        if mode not in _valid_modes:
            sublime.error_message(
                f'\'{mode}\' is an invalid mode for \'selection_fields\'.\n' +
                f'Valid modes are: [{", ".join(_valid_modes)}]')
            return
        view = self.view
        has_fields = bool(_get_fields(view))
        has_only_added_fields = (not _get_fields(view, added_fields=False) and
                                 _get_settings('add_separated', True))
        do_push = {
            'pop': False,
            'remove': False,
            'push': True,
            'subtract': False,
            'add': False  # add is specially handled
        }.get(mode, not has_fields)
        # the regions, which should be selected after executing this command
        sel_regions = None

        if do_push:  # push or initial trigger with anything except pop
            sels = list(view.sel())
            border_pos = 0 if jump_forward else len(sels) - 1
            sel_regions = _change_selection(view, sels, border_pos)
        elif mode == 'subtract':  # subtract selections from the pushed fields
            sel_regions = list(view.sel())
            pushed_regions = _get_fields(view)
            regions = list(_subtract_selection(pushed_regions, sel_regions))
            _erase_added_fields(view)
            _set_fields(view, regions, added_fields=has_only_added_fields)
        elif mode == 'add':  # add selections to the pushed fields
            pushed_regions = _get_fields(view)
            sel_regions = list(view.sel())
            _set_fields(view, sel_regions + pushed_regions,
                        added_fields=has_only_added_fields)
        elif mode == 'remove':  # remove pushed fields
            pop_regions = _restore_selection(view, only_other)
            sel_regions = list(view.sel()) if not only_other else pop_regions
        elif mode not in ['smart', 'cycle']:  # pop or toggle with region
            sel_regions = _restore_selection(view, only_other)
        # pop added fields instead of jumping
        elif mode == 'smart' and has_only_added_fields:
            sel_regions = _restore_selection(view, only_other)
        else:  # smart or cycle
            # execute the jump
            regions, pos = _execute_jump(view, jump_forward, only_other)
            # if we are in the cycle mode force the position to be valid
            if mode == 'cycle':
                pos = pos % len(regions)
            # check whether it is a valid position
            pos_valid = pos == pos % len(regions)
            if pos_valid:
                # move the selection to the new field
                sel_regions = _change_selection(view, regions, pos)
            else:
                # if we reached the end restore the selection and
                # remove the highlight regions
                sel_regions = _restore_selection(view, only_other)

        # change to the result selections, if they exists
        if sel_regions:
            view.sel().clear()
            view.sel().add_all(sel_regions)
            view.show(sel_regions[0])


class SelectionFieldsContext(sublime_plugin.EventListener):
    def on_query_context(self, view, key, operator, operand, match_all):
        if key not in ['is_selection_field', 'is_selection_field.added_fields',
                       'selection_fields_tab_enabled',
                       'selection_fields_escape_enabled']:
            return False

        if key == 'is_selection_field':
            # selection field is active if the regions are pushed to the view
            result = bool(_get_fields(view, added_fields=False))
        elif key == 'is_selection_field.added_fields':
            # selection field is active if the regions are pushed to the view
            # also if added fields are pushed
            result = bool(_get_fields(view))
        else:
            # the *_enabled key has the same name in the settings
            result = get_settings(key, False)

        if operator == sublime.OP_EQUAL:
            result = result == operand
        elif operator == sublime.OP_NOT_EQUAL:
            result = result != operand
        else:
            raise Exception(f'Invalid Operator \'{operator}\'.')
        return result
