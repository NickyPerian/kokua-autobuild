#!/usr/bin/env python
# $LicenseInfo:firstyear=2010&license=mit$
# Copyright (c) 2010, Linden Research, Inc.
# $/LicenseInfo$


"""
Configures source in preparation for building.
"""

import autobuild_base
import copy
import common
from common import AutobuildError
import configfile
import os


class ConfigurationError(AutobuildError):
    pass


class AutobuildTool(autobuild_base.AutobuildBase):
    def get_details(self):
        return dict(name='configure',
            description="Configures platform targets.")
     
    def register(self, parser):
        parser.add_argument('--config-file',
            dest='config_file',
            default=configfile.AUTOBUILD_CONFIG_FILE,
            help="")
        parser.add_argument('--configuration', '-c', nargs='?', action="append", dest='configurations', 
            help="build a specific build configuration", metavar='CONFIGURATION')
        parser.add_argument('--all','-a',dest='all', default=False, action="store_true",
            help="build all configurations")
        parser.add_argument('additional_options', nargs="*", metavar='OPT',
            help="an option to pass to the configuration command" )
        parser.add_argument('--use-cwd', dest='use_cwd', default=False, action="store_true",
            help="configure in current working directory")
        parser.usage = "%(prog)s [-h] [--dry-run] [-c CONFIGURATION][-a][--config-file FILE] [-- OPT [OPT ...]]"

    def run(self, args):
        if args.dry_run:
            return
        config = configfile.ConfigurationDescription(args.config_file)
        current_directory = os.getcwd()
        build_directory = config.make_build_directory()
        if not args.use_cwd:
            os.chdir(build_directory)
        try:
            if args.all:
                build_configurations = config.get_all_build_configurations()
            elif args.configurations is not None:
                build_configurations = \
                    [config.get_build_configuration(name) for name in args.configurations]
            else:
                build_configurations = config.get_default_build_configurations()
            for build_configuration in build_configurations:
                result = _configure_a_configuration(config, build_configuration,
                    args.additional_options)
                if result != 0:
                    raise ConfigurationError("default configuration returned '%d'" % (result))
        finally:
            os.chdir(current_directory)

def configure(config, build_configuration_name, extra_arguments=[]):
    """
    Execute the platform configure command for the named build configuration.

    A special 'common' platform may be defined which can provide parent commands for the configure 
    command using the inheritence mechanism described in the 'executable' package.  The working
    platform's build configuration will be matched to the build configuration in common with the
    same name if it exists.  To be configured, a build configuration must be defined in the working
    platform though it does not need to contain any actual commands if it is desired that the common
    commands be used.  Build configurations defined in the common platform but not the working
    platform are not configured.
    """
    build_configuration = config.get_build_configuration(build_configuration_name)
    return _configure_a_configuration(config, build_configuration, extra_arguments)


def _configure_a_configuration(config, build_configuration, extra_arguments):
    try:
        common_build_configuration = \
            config.get_build_configuration(build_configuration.name, 'common')
        parent_configure = common_build_configuration.configure
    except:
        parent_configure = None
    if build_configuration.configure is not None:
        configure_executable = copy.copy(build_configuration.configure)
        configure_executable.parent = parent_configure
        return configure_executable(extra_arguments)
    elif parent_configure is not None:
        return parent_configure(extra_arguments)
    else:
        return 0
