#!/usr/bin/env python
# $LicenseInfo:firstyear=2010&license=mit$
# Copyright (c) 2010, Linden Research, Inc.
# $/LicenseInfo$


import argparse
import common
import os
import sys

import autobuild_base
import configfile
	

class autobuild_tool(autobuild_base.autobuild_base):
    def get_details(self):
        return dict(name='dump',
            description="Output the contents of an autobuild configuration file in a human "
            "readable format.")
     
    def register(self, parser):
        parser.add_argument('-v', '--version', action='version', version='dump tool 1.0')
        parser.add_argument('file', default=configfile.BUILD_CONFIG_FILE, nargs='?',
            help='The configuration file to dump')
        parser.add_argument('--format', default='all',
            help='Comma separated list of package elements to dump')

    def run(self, args):
        config = configfile.ConfigFile()
        if config.load(args.file) is False:
            raise  ConfigurationFileNotFoundError("configuration file '%s' not found" % args.file)
        formatString = args.format
        if formatString.lower() == 'all':
            self._reset_format_flags(True)
        else:
            self._set_format_flags(formatString)
        self._pretty_print(config)
    
    def _reset_format_flags(self, state):
        for key in self._display_flags.keys():
            self._display_flags[key] = state;
        
    def _set_format_flags(self, formatString):
        self._reset_format_flags(False)
        for format in [s.strip() for s in formatString.split(',')]:
            if self._display_flags.has_key(format):
                self._display_flags[format] = True
            else:
                print >> sys.stderr, "format: keyword '%s' not found" % format
        
    def _pretty_print(self, config):
        for name in config.package_names:
            self._pretty_print_package(name, config.package(name))
            print
            print
        
    def _pretty_print_package(self, name, info):
        print name,
        if info.version is not None and self._display_flags['version']:
            print info.version,
        if info.copyright is not None and self._display_flags['copyright']:
            print '(' + info.copyright + ')'
        else:
            print
        if info.summary is not None and self._display_flags['summary']:
            print info.summary
            print
        if info.description is not None and self._display_flags['description']:
            print info.description
            print
        if info.license is not None and self._display_flags['license']:
            print "License:", info.license
        if info.homepage is not None and self._display_flags['homepage']:
            print "homepage:", info.homepage
        if info.uploadtos3 is not None and self._display_flags['uploadtos3']:
            print "Upload to S3:", bool(info.uploadtos3)
        if info.source is not None and self._display_flags['source']:
            if info.sourcetype is not None and self._display_flags['sourcetype']:
                print "Source (" + info.sourcetype + "):",
            else:
                print "Source:",
            print info.source
        if info.sourcedir is not None and self._display_flags['sourcedir']:
            print "Source directory:", info.sourcedir
        if info.builddir is not None and self._display_flags['builddir']:
            print "Build directory:", info.builddir
        if info.patches is not None and self._display_flags['patches']:
            print "Patches:"
            for patch in info.patches:
                print "\t", patch
        if info.obsoletes is not None and self._display_flags['obsoletes']:
            print "Obsoletes:"
            for obsolete in info.obsoletes:
                print "\t", obsolete
        if info.packages is not None and len(info.packages) > 0 and self._display_flags['packages']:
            print
            self._pretty_print_platform_packages(info)
        if info.depends is not None and len(info.depends) > 0 and self._display_flags['depends']:
            print
            self._pretty_print_platform_depends(info)
        if (info.configure is not None and
            len(info.configure) > 0 and 
            self._display_flags['configure']):
            print
            self._pretty_print_platform_configure(info)
        if info.build is not None and len(info.build) > 0 and self._display_flags['build']:
            print
            self._pretty_print_platform_build(info)
        if (info.postbuild is not None and 
            len(info.postbuild) > 0 and 
            self._display_flags['postbuild']):
            print
            self._pretty_print_platform_post_build(info)
        if info.manifest is not None and len(info.manifest) > 0 and self._display_flags['manifest']:
            print
            self._pretty_print_platform_manifest(info)
        
    def _pretty_print_platform_packages(self, info):
        print "Packages:"
        for platform in info.packages:
            print platform
            print "\turl:", info.packages_url(platform)
            print "\tmd5:", info.packages_md5(platform)
            print "\tfiles:"
            for file in info.packages_files(platform):
                print "\t\t", file

    def _pretty_print_platform_depends(self, info):
        print "Dependencies:"
        for platform in info.depends:
            print platform
            print "\turl:", info.depends_url(platform)
            print "\tmd5:", info.depends_md5(platform)

    def _pretty_print_platform_configure(self, info):
        print "Configuration:"
        for platform in info.configure:
            print platform, "configuration command:", info.configure_command(platform)
    
    def _pretty_print_platform_build(self, info):
        print "Build:"
        for platform in info.build:
            print platform, "build command:", info.build_command(platform)
    
    def _pretty_print_platform_post_build(self, info):
        print "Post build:"
        for platform in info.build:
            print platform, "post build command:", info.post_build_command(platform)
    
    def _pretty_print_platform_manifest(self, info):
        print "Manifest:"
        for platform in info.manifest:
            print platform
            for file in info.manifest_files(platform):
                print "\t", file
    
    _display_flags = {
        # Package properties:
        'copyright' : True,
        'summary' : True,
        'description': True,
        'license': True,
        'homepage': True,
        'uploadtos3': True,
        'source': True,
        'sourcetype': True,
        'sourcedir': True,
        'builddir': True,
        'version': True,
        'patches': True,
        'obsoletes': True,
        
        # Platform properties:
        'packages': True,
        'depends': True,
        'configure': True,
        'build': True,
        'postbuild': True,
        'manifest': True
    }


class ConfigurationFileNotFoundError(Exception):
    pass


if __name__ == "__main__":
    sys.exit( autobuild_tool().main( sys.argv[1:] ) )
