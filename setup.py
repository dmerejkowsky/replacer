## Copyright (c) 2016 Dimitri Merejkowsky
## Use of this source code is governed by a BSD-style license that can be
## found in the COPYING file.

from setuptools import setup

setup(name="replacer",
      version="1.0",
      description="Replace text in files",
      url="http://github.com/yannicklm/replacer",
      author="Dimitri Merejkowky",
      author_email="d.merej@gmail.com",
      scripts=["bin/replacer"],
      license="BSD",
      classifiers=[
          "Environment :: Console",
          "License :: OSI Approved :: BSD License",
          "Programming Language :: Python",
          "Topic :: System :: Shells",
    ]
)
