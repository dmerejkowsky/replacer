#!/usr/bin/env python

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
    "light-red": "\033[1;31m",

    "green": "\033[0;32m",
    "light-green": "\033[1;32m",

    "blue": "\033[0;34m",
    "light-blue": "\033[1;34m",

    "magenta": "\033[0;36m",
    "light-magenta": "\033[1;36m",

}

COLORS_REPLACE = {
    "line1": COLORS["clear"],
    "line2": COLORS["clear"],
    "line1start": COLORS["clear"] + COLORS["light-red"],
    "line2start": COLORS["clear"] + COLORS["light-green"],
    "word1": COLORS["clear"] + COLORS["underline"] + COLORS["light-red"],
    "word2": COLORS["clear"] + COLORS["underline"] + COLORS["light-green"],
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


def display_one_diff(regexp, repl, in_line, out_line):

    in_line = in_line.strip()
    out_line = out_line.strip()
    match = re.search(regexp, in_line)
    in_line_color = in_line[0:match.start()]
    in_line_color += COLORS["red"] + COLORS["underline"]
    in_line_color += in_line[match.start():match.end()]
    in_line_color += COLORS["clear"]
    in_line_color += in_line[match.end():]
    colored_replacement = COLORS["green"] + COLORS["underline"]
    colored_replacement += repl
    colored_replacement += COLORS["clear"]
    out_line_color = re.sub(regexp, colored_replacement, in_line)

    print("%s--%s %s%s" % (COLORS_REPLACE["line1start"], COLORS_REPLACE["line1"], in_line_color, COLORS["clear"]))
    print("%s++%s %s%s" % (COLORS_REPLACE["line2start"], COLORS_REPLACE["line2"], out_line_color, COLORS["clear"]))
    print()


def display_diff(in_file, regexp, repl, in_lines, out_lines):
    print(COLORS["bold"], COLORS["light-blue"], "Patching: ",
          COLORS["clear"], COLORS["bold"], os.path.relpath(in_file),
          sep="")
    for (in_line, out_line) in zip(in_lines, out_lines):
        if in_line != out_line:
            display_one_diff(regexp, repl, in_line, out_line)


def replace_in_file(args, in_file, regexp, repl):
    """
    Perfoms re.sub(regexp, repl, line) for each line in
    in_file
    """
    in_lines = []
    try:
        with open(in_file, "r") as in_fd:
            in_lines = in_fd.readlines()
    except OSError as error:
        print("Cant open file:", in_file, error)
        return

    out_lines = in_lines[:]
    out_lines = [re.sub(regexp, repl, l) for l in in_lines]

    # Exit early if there's no diff:
    if in_lines == out_lines:
        return

    if not args.quiet:
        display_diff(in_file, regexp, repl, in_lines, out_lines)

    if args.go:
        if args.backup:
            rand_int = random.randint(100, 999)
            back_file = "%s-%i.back" % (in_file, rand_int)
            back_file_fd = open(back_file, "w")
            back_file_fd.writelines(in_lines)
            back_file_fd.close()
        out_fd = open(in_file, "w")
        out_fd.writelines(out_lines)
        out_fd.close()



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

    if not args.go and not args.quiet:
        print()
        print("To apply change, run again:")
        print("$ %s %s --go\n" % (os.path.basename(sys.argv[0]),
              ' '.join(sys.argv[1:])))
        print("To backup altered files,",
              "add '--backup' to the above command line.")
        print()


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
    parser.add_argument("--color", action="store_true", dest="color",
                        help="Colorize output. This is the default")
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
        color=True,
        quiet=False,
        )

    args = parser.parse_args(args=args)

    if not args.color or not sys.stdout.isatty():
        for k in COLORS.keys():
            COLORS[k] = ""
        for k in COLORS_REPLACE.keys():
            COLORS_REPLACE[k] = ""

    repl_main(args)


if __name__ == "__main__":
    main()
