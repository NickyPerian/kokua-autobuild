#!/usr/bin/env python

import unittest
import subprocess
from autobuild import autobuild_tool_source_environment

class TestSourceEnvironment(unittest.TestCase):
    def setUp(self):
        pass

    def test_env(self):
        assert 'environment_template' in dir(autobuild_tool_source_environment)

    def tearDown(self):
        pass

if __name__ == '__main__':
    unittest.main()

