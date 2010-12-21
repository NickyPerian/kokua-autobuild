# $LicenseInfo:firstyear=2010&license=mit$
# Copyright (c) 2010, Linden Research, Inc.
# $/LicenseInfo$

from distutils.core import setup

# most of this is shamelessly cloned from llbase's setup.py

PACKAGE_NAME = 'autobuild'
LLAUTOBUILD_VERSION = '0.0.0'
LLAUTOBUILD_SOURCE = 'autobuild'
CLASSIFIERS = """\
Development Status :: 4 - Beta
Intended Audience :: Developers
License :: OSI Approved :: MIT License
Programming Language :: Python
Topic :: Software Development
Topic :: Software Development :: Libraries :: Python Modules
Operating System :: Microsoft :: Windows
Operating System :: Unix
"""

ext_modules = []

setup(
    name=PACKAGE_NAME,
    version=LLAUTOBUILD_VERSION,
    author='Brad Linden',
    author_email='brad@lindenlab.com',
    url='http://bitbucket.org/brad_linden/autobuild/',
    description='Linden Lab Automated Package Management and Build System',
    platforms=["any"],
    package_dir={PACKAGE_NAME:LLAUTOBUILD_SOURCE},
    packages=[PACKAGE_NAME],
    scripts=['bin/autobuild'],
    license='MIT',
    classifiers=filter(None, CLASSIFIERS.split("\n")),
    #requires=['eventlet', 'elementtree'],
    #ext_modules=ext_modules,
    )
