v1.1.1
======

* Fix regression: non UTF-8 files are now ignored insteod of
  crashing the whole program.

Properly handling non UTF-8 files is not done yet, see
`issue #3 <https://github.com/dmerejkowsky/replacer/issues/3>`_


v1.1.0
=======

New features
------------

* Truncate lines longer than 100 characters

* ``--file-filter`` is now called ``--include``.
* Add ``--exclude``.

This means you can use::


  # Skip everything in node_modules directory
  $ replace foo bar --exclude 'node_modules/*'

  # Only change .c files:
  $ replace foo bar --include '*.c'

Fixes
-----

* Fix crash when ``sys.stdout`` is not a tty and using Python3


Removed options
---------------

* ``-no-color``: use ``--color=(auto|never|always)`` instead.
* ``--find``: use ``ack``, ``grep``, ``ag`` or anything you like
* ``--debug``: only used during development

Internal
--------

* Add tests
* Use ``argparse`` instead of ``optparse``
* PEP8 compliant
* Remove dead code dealing with context
* Cleaner code


v1.0.4
======

Packaging changes

v1.0
====

Initial ``pypi`` release
