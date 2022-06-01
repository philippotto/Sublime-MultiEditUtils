import sublime

import re


def find_next_literal(view, pt, arg):
    lr = view.line(pt)
    line = view.substr(sublime.Region(pt, lr.b))
    idx = line.find(arg)

    if idx != -1:
        pt_start = pt + idx
        return sublime.Region(pt_start, pt_start + len(arg))


def find_next_re(view, pt, arg):
    lr = view.line(pt)
    line = view.substr(sublime.Region(pt, lr.b))
    try:
        result = re.search(arg, line)
    except Exception:
        sublime.status_message('JumpTo: Error in regular expression!')
        return None

    if result:
        return sublime.Region(pt + result.start(), pt + result.end())


def find_next_count(view, pt, arg):
    lr = view.line(pt)
    idx = pt + int(arg)
    if lr.a <= idx <= lr.b:
        return sublime.Region(idx, idx)


MATCHERS = [
    (r'\[(.+)\]', find_next_literal),
    (r'/(.+)/', find_next_re),
    (r'\{(-?\d+)\}', find_next_count),
]


def find_regions(view, start_regions, text):
    find_func, arg = find_next_literal, text
    for pattern, func in MATCHERS:
        m = re.match(pattern, text)
        if m:
            find_func, arg = func, m.group(1)
            break

    for reg in start_regions:
        new_reg = find_func(view, reg.b, arg)
        yield reg, new_reg


def process_results(regions, whole_match, extend):
    for reg, new_reg in regions:
        if new_reg is None:
            yield reg
            continue
        if not whole_match:
            new_reg = sublime.Region(new_reg.a, new_reg.a)
        if extend:
            new_reg = sublime.Region(reg.a, new_reg.b)
        yield new_reg


def get_new_regions(view, text, whole_match, extend, **_):
    start_regions = list(view.sel())
    find_results = find_regions(view, start_regions, text)
    return process_results(find_results, whole_match, extend)
