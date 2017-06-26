# Use of this source code is governed by a BSD-style license that can be
# found in the COPYING file.

"""
Quick script to replace stuff in files

"""

from __future__ import print_function

import sys
import os
import re
import random
import fnmatch

from argparse import ArgumentParser

COLORS = {
    "clear": "\033[0m",
    "bold": "\033[1m",
    "underline": "\033[4m",
    "red": "\033[0;31m",
    "green": "\033[0;32m",
    "blue": "\033[0;34m",
}

FILTER_OUT = (
    ".git",
    ".svn",
    "*.back",
    "*~",
    "*.so",
    "*.a",
)

__usage__ = """
replacer [options]  PATTERN REPL [files]

eg:
  replacer 'toto' 'titi'
  replacer '(.*)toto([0-9]{0,3})' '\\1titi\\2'

Files matching %s are discarded.
""" % (str(FILTER_OUT))


def setup_colors(args):
    auto_off = args.color == "auto" and not sys.stdout.isatty()
    if args.color == "never" or auto_off:
        for key in COLORS:
            COLORS[key] = ""


def is_binary(filename):
    """ Returns True if the file is binary

    """
    with open(filename, 'rb') as fp:
        data = fp.read(1024)
        if not data:
            return False
        if b'\0' in data:
            return True
        return False


def is_excluded_directory(args, entry):
    if os.path.isdir(entry):
        for exclude in args.excludes:
            if "/" in exclude:
                root = exclude.split("/")[0]
                if entry == root:
                    return True


def is_hidden(args, entry):
    if args.skip_hidden and entry.startswith("."):
        return True


def is_in_default_excludes(entry):
    for fo in FILTER_OUT:
        if fnmatch.fnmatch(entry, fo):
            return True


def is_included(args, entry):
    if not args.includes:
        return True

    for fo in args.includes:
        if fnmatch.fnmatch(entry, fo):
            return True

    # --include was used, and no match was found,
    # skip this entry:
    return False


def is_excluded(args, entry, directory):
    full_path = os.path.join(directory, entry)
    relpath = os.path.relpath(full_path)
    for fo in args.excludes:
        if fnmatch.fnmatch(relpath, fo):
            return True
    return False


def walk_files(args, root, directory, action):
    """
    Recusively go do the subdirectories of the directory,
    calling the action on each file

    """
    for entry in os.listdir(directory):
        if is_hidden(args, entry):
            continue
        if is_excluded_directory(args, entry):
            continue
        if is_in_default_excludes(entry):
            continue
        if not is_included(args, entry):
            continue
        if is_excluded(args, entry, directory):
            continue
        entry = os.path.join(directory, entry)
        if os.path.isdir(entry):
            walk_files(args, root, entry, action)
        if os.path.isfile(entry):
            if is_binary(entry):
                continue
            action(entry)


def apply_replacements(line, replacements):
    res = ""
    i = 0
    while i < len(line):
        if i in replacements:
            end, repl = replacements[i]
            res += repl
            i = end
        else:
            res += line[i]
            i += 1
    return res


def get_replacements(line, regexp, repl):
    in_replacements = dict()
    out_replacements = dict()
    for match in re.finditer(regexp, line):
        in_repl = COLORS["red"] + COLORS["bold"] + COLORS["underline"]
        in_repl += match.group() + COLORS["clear"]
        in_replacements[match.start()] = (match.end(), in_repl)
        full_repl = re.sub(regexp, repl, match.group())
        out_repl = COLORS["green"] + COLORS["bold"] + COLORS["underline"]
        out_repl += full_repl + COLORS["clear"]
        out_replacements[match.start()] = (match.end(), out_repl)
    return (in_replacements, out_replacements)


def shorten_line(line, regexp):
    if len(line) < 100:
        return line
    match = re.search(regexp, line)
    if len(match.group()) >= 100:
        return line[:100]
    else:
        padding = (100 - len(match.group())) // 2
        padding -= 9  # (the two ellipsis plus the \n)
        res = line[match.start() - padding: match.end() + padding]
        return "... " + res + " ..." + "\n"


def display_one_diff(line, regexp, repl):
    line = shorten_line(line, regexp)
    in_replacements, out_replacements = get_replacements(line, regexp, repl)
    in_color = apply_replacements(line, in_replacements)
    out_color = apply_replacements(line, out_replacements)
    print(COLORS["red"], "-- ", COLORS["clear"], in_color, end="", sep="")
    print(COLORS["green"], "++ ", COLORS["clear"], out_color, end="", sep="")
    print()


def display_diff(in_file, regexp, repl, in_lines, out_lines):
    print(COLORS["bold"], COLORS["blue"], "Patching: ",
          COLORS["clear"], COLORS["bold"], os.path.relpath(in_file),
          COLORS["clear"], sep="")
    for (in_line, out_line) in zip(in_lines, out_lines):
        if in_line != out_line:
            display_one_diff(in_line, regexp, repl)


def backup(filename, lines):
    rand_int = random.randint(100, 999)
    backup_name = "%s-%i.back" % (filename, rand_int)
    with open(backup_name, "w") as fd:
        fd.writelines(lines)


def replace_in_file(args, in_file, regexp, repl):
    """
    Perfoms re.sub(regexp, repl, line) for each line in
    in_file
    """
    in_lines = []
    try:
        with open(in_file, "r") as in_fd:
            in_lines = in_fd.readlines()
    except (OSError, UnicodeDecodeError) as error:
        print("Cant open file:", in_file, error)
        return

    out_lines = in_lines[:]
    out_lines = [re.sub(regexp, repl, l) for l in in_lines]

    # Exit early if there's no diff:
    if in_lines == out_lines:
        return

    if not args.quiet:
        display_diff(in_file, regexp, repl, in_lines, out_lines)

    if not args.go:
        return

    if args.backup:
        backup(in_file, in_lines)

    with open(in_file, "w") as fd:
        fd.writelines(out_lines)


def repl_main(args):
    """ replacer main """
    pattern = args.pattern
    repl = args.replacement
    regexp = re.compile(pattern)

    def repl_action(f):
        return replace_in_file(args, f, regexp, repl)

    if args.paths:
        for f in args.paths:
            repl_action(f)
    else:
        root = os.getcwd()
        walk_files(args, root, root, repl_action)


def main(args=None):
    """
    manages options when called from command line

    """
    parser = ArgumentParser(usage=__usage__)
    parser.add_argument("--no-skip-hidden", action="store_false",
                        dest="skip_hidden",
                        help="Do not skip hidden files. "
                        "Use this if you know what you are doing...")
    parser.add_argument("--include", dest="includes", action="append",
                        help="Only replace in files matching theses patterns")
    parser.add_argument("--exclude", dest="excludes", action="append",
                        help="Ignore files matching theses patterns")
    parser.add_argument("--backup",
                        action="store_true", dest="backup",
                        help="Create a backup for each file. "
                             "By default, files are modified in place")
    parser.add_argument("--go",
                        action="store_true", dest="go",
                        help="Perform changes rather than just printing then")
    parser.add_argument("--dry-run", "-n",
                        action="store_false", dest="go",
                        help="Do not change anything. This is the default")
    parser.add_argument("--color", choices=["always", "never", "auto"],
                        help="When to colorize the output. "
                             "Default: when output is a tty")
    parser.add_argument("--no-color", action="store_false", dest="color",
                        help="Do not colorize output")
    parser.add_argument("--quiet", "-q", action="store_true", dest="quiet",
                        help="Do not produce any output")
    parser.add_argument("pattern")
    parser.add_argument("replacement")
    parser.add_argument("paths", nargs="*")

    parser.set_defaults(
        includes=list(),
        excludes=list(),
        skip_hidden=True,
        backup=False,
        go=False,
        color="auto",
        quiet=False,
        )

    args = parser.parse_args(args=args)
    setup_colors(args)
    repl_main(args)


if __name__ == "__main__":
    main()
