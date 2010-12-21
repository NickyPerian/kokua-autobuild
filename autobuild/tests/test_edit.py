# $LicenseInfo:firstyear=2010&license=mit$
# Copyright (c) 2010, Linden Research, Inc.
# $/LicenseInfo$
#
# Unit testing of edit subcommand.
#


import os
import subprocess
import sys
import unittest

from llbase import llsd
from autobuild import configfile
from autobuild import common
from autobuild.autobuild_main import Autobuild
from baseline_compare import AutobuildBaselineCompare
from autobuild.autobuild_tool_edit import AutobuildTool


class TestEdit(unittest.TestCase, AutobuildBaselineCompare):
    def setUp(self):
        os.environ["PATH"] = os.pathsep.join([os.environ["PATH"], os.path.abspath(os.path.dirname(__file__))])
        self.tmp_file = self.get_tmp_file(4)
        self.edit_cmd = AutobuildTool()

    def _try_cmd(self, args):
        """
        Try running an edit 'command with args'.
        Return results.
        """
        self.edit_cmd.main(args)
        return llsd.parse(file(self.tmp_file, 'rb').read())

    def test_build(self):
        """
        Perform non-interactive configuration of build command.
        Check results.
        """
        args = ['build', "--config-file=%s" % self.tmp_file, 'name=newbuild', 'platform=windows', 'command=makethis']
        expected_config = {'package_description': {'platforms': {'windows': {'name': 'windows', 'configurations': {'newbuild': {'build': {'command': 'makethis'}, 'name': 'newbuild'}}}}}, 'version': '1.2', 'type': 'autobuild'}
        built_config = self._try_cmd(args)
        assert (expected_config == built_config)
           
    def test_configure(self):
        """
        Perform non-interactive configuration of configure command.
        Check results.
        """
        args = ['configure', "--config-file=%s" % self.tmp_file, 'name=newbuild', 'platform=windows', 'command=makethat']
        expected_config = {'package_description': {'platforms': {'windows': {'name': 'windows', 'configurations': {'newbuild': {'configure': {'command': 'makethat'}, 'name': 'newbuild'}}}}}, 'version': '1.2', 'type': 'autobuild'}
        built_config = self._try_cmd(args)
        assert (expected_config == built_config)

    def test_build_configure(self):
        """
        Perform two updates to the config file in series. 
        Check results after each iteration.
        """
        args = ['configure', "--config-file=%s" % self.tmp_file, 'name=newbuild', 'platform=windows', 'command=makethat']
        built_config1 = self._try_cmd(args)
        expected_config1 = {'package_description': {'platforms': {'windows': {'name': 'windows', 'configurations': {'newbuild': {'configure': {'command': 'makethat'}, 'name': 'newbuild'}}}}}, 'version': '1.2', 'type': 'autobuild'}
        assert (expected_config1 == built_config1)
        args = ['build', "--config-file=%s" % self.tmp_file, 'name=newbuild', 'platform=windows', 'command=makethis']
        built_config2 = self._try_cmd(args)
        expected_config2 = {'package_description': {'platforms': {'windows': {'name': 'windows', 'configurations': {'newbuild': {'build': {'command': 'makethis'}, 'name': 'newbuild', 'configure': {'command': 'makethat'}}}}}}, 'version': '1.2', 'type': 'autobuild'}
        assert (expected_config2 == built_config2)
        
    def test_platform_configure(self):
        args = ['platform', "--config-file=%s" % self.tmp_file, 'name=windows', 'build_directory=foo/bar/baz']
        built_config = self._try_cmd(args)
        assert built_config['package_description']['platforms']['windows']['build_directory'] == 'foo/bar/baz'

    def tearDown(self):
        self.cleanup_tmp_file()


class TestEditCmdLine(unittest.TestCase, AutobuildBaselineCompare):
    def setUp(self):
        os.environ["PATH"] = os.pathsep.join([os.environ["PATH"], os.path.abspath(os.path.dirname(__file__))])
        self.tmp_file = self.get_tmp_file(0)

    def test_autobuild_edit(self):
        """
        Verify that 'autobuild edit' can be run from the command line.
        """
        result = subprocess.call('autobuild edit --config-file=%s --help > /dev/null ' % \
            self.tmp_file, shell=True)
        assert result == 0
        result = subprocess.call('autobuild edit build --config-file=%s name=foo command=buildme.py' % \
            self.tmp_file, shell=True)
        assert result == 0

    def tearDown(self):
        self.cleanup_tmp_file()


if __name__ == '__main__':
    unittest.main()
