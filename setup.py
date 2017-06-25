# Copyright (c) 2016 Dimitri Merejkowsky
# Use of this source code is governed by a BSD-style license that can be
# found in the COPYING file.

from setuptools import setup

setup(name="replacer",
      version="1.1.0",
      description="Replace text in files",
      url="http://github.com/dmerejkowsky/replacer",
      author="Dimitri Merejkowky",
      author_email="d.merej@gmail.com",
      license="BSD",
      py_modules=["replacer"],
      classifiers=[
          "Environment :: Console",
          "License :: OSI Approved :: BSD License",
          "Programming Language :: Python",
          "Topic :: System :: Shells",
      ],
      entry_points={
        "console_scripts": [
          "replacer = replacer:main"
        ]
      })
