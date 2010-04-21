# $LicenseInfo:firstyear=2010&license=mit$
# Copyright (c) 2010, Linden Research, Inc.
# $/LicenseInfo$

"""
Autobuild sub-command to build the source for a package.
"""

import sys
import os
import subprocess

# autobuild modules:
import common
import autobuild_base
import configfile

class autobuild_tool(autobuild_base.autobuild_base):
    def get_details(self):
        return dict(name=self.name_from_file(__file__),
                    description='Runs the package\'s build command')

    def register(self, parser):
        parser.add_argument('--config-file',
            dest='config_file',
            default=configfile.BUILD_CONFIG_FILE,
            help="")
        parser.add_argument('--build-extra-args',
            dest='build_extra_args',
            default='',
            help="extra arguments to the build command, will be split on any whitespace boundaries (*TODO add escaping)")

    def run(self, args):
        cf = configfile.ConfigFile()
        cf.load(args.config_file)
        package_definition = cf.package_definition

        # *TODO -use common.find_executable() to search the path and append the current working directory to the build command if necessary
        build_command = package_definition.build_command(common.get_current_platform())

        # *TODO -find a better way to split this to avoid escaping problems
        for build_arg in args.build_extra_args.split():
            build_command.append(build_arg)

        print "executing '%s' in '%s'" % (' '.join(build_command), os.getcwd())
        subprocess.call(build_command)

