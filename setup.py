#!/usr/bin/env python

from distutils.core import setup

setup(name="galvanolab",
      version="0.2",
      description="Set of tools for importing and viewing experimental electro-chemical data.",
      author="Mark Wolfman",
      author_email="canismarko@gmail.com",
      url="https://github.com/m3wolf/galvanolab",
      license="GPLv3.0",
      packages=['galvanolab',],
      install_requires=('pint', 'numpy', 'pandas', 'pytz', 'scipy', 'matplotlib', 'python-dateutil'),
)
