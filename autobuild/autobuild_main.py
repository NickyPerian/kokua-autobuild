# $LicenseInfo:firstyear=2010&license=mit$
# Copyright (c) 2010, Linden Research, Inc.
# $/LicenseInfo$

"""
High-level option parsing functionality for autobuild.

This module parses the autobuild command line and runs the appropriate
sub-command.
"""

import sys
import os
import optparse

class OptionParser(optparse.OptionParser):
    def __init__(self):
        default_platform = {
            'linux2':'linux',
            'win32':'windows',
        }.get(sys.platform, sys.platform)

        #package usage="\n    %prog -t expat GL\n    %prog -u ../tarfile_tmp/expat-1.2.5-darwin-20080810.tar.bz2\n    %prog -i ./tmp/zlib*.tar.bz2 ../glh_lin*.bz2", 
        #package description="""Create tar archives from library files, and upload as appropriate.  Tarfiles will be formed from paths as specified in the manifest in autobuild.xml, or alternately 'configdir', if supplied as a command-line argument.""")

        optparse.OptionParser.__init__(self, usage="\n\t%prog [options] command [commandopts]\n\twhere command is one of 'install' 'configure' 'build' 'package' or 'upload'")
        self.add_option('--package-info', default='autobuild.xml',
            help="file containing package info database (for now this is llsd+xml, but it will probably become sqlite)")
        self.add_option('--verbose', '-v', action='store_true', default=False)
        self.add_option('--install-dir', default='build-linux-i686-relwithdebinfo/packages',
            help="directory to install packages into")
        self.add_option('--platform', type='string', default=default_platform,
            help="Specify platform to use: linux, darwin, or windows.  Left unspecified, the current platform will be used (formerly all three platforms were used).")


        ##########
        # BEGIN packaging options
        ##########
        self.add_option('--version', type='string', default="", dest='version',
            help='Overrides the version number for the specified library(ies).  If unspecified, the version number in "versions.txt" (in configdir) will be used, if present.  Can be left blank.')
        #self.add_option('-i', '--install', action='store_true', default=False, dest='install',
        #    help='Update autobuild.xml with the data for the specified tarfile(s). List paths to tarfiles to update (supports glob expressions).  Use --s3 option if appropriate (read about --s3 option).')
        group = optparse.OptionGroup(self, "S3 Uploading", "*NOTE*: S3 upload does not work on Windows, since command-line tool (s3curl.pl) is not supported there.  Either perform S3 uploads from a unix machine, or see wiki for uploading to S3 from Windows.")

        group.add_option('-s', '--s3', action='store_true', default=False, dest='s3',
            help='Indicates tarfile(s) belong on S3.  If unspecified, "S3ables.txt" (in configdir) will be used to determine which libraries are stored on S3.  Please verify clearance for public distribution prior to uploading any new libraries to S3.')
        self.add_option('--configdir', type='string', default=os.getcwd(), dest='configdir',
            help='Specify the config directory to use.  Defaults to current working directory.  If configdir specified, tarfiles will be assembled relative to root of tree containing configdir.')
        self.add_option('--tarfiledir', type='string', default="", dest='tarfiledir',
            help='Specify the directory in which to store new tarfiles.  Defaults to "tarfile_tmp".')
        self.add_option('--dry-run', action='store_true', default=False, dest='dry_run',
            help='Show what would be done, but don\'t actually do anything.')
        self.add_option_group(group)
        ##########
        # END packaging options
        ##########

        self.add_option('--build-command', type='string', default='build.sh', dest='build_command',
            help="command to execute for building a package (defaults to 'build.sh' or whatever's specified in autobuild.xml")

def parse_args(args):
    parser = OptionParser()
    return parser.parse_args(args)

def main(args):
    parser = OptionParser()
    options,extra_args = parser.parse_args(args)
    if options.verbose:
        print "options:'%r', args:%r" % (options.__dict__, args)

    if not extra_args:
        parser.print_usage()
        print >>sys.stderr, "run '%s --help' for more details" % sys.argv[0]
        return 1

    if extra_args[0] == 'install':
        import install
        return install.main([a for a in args if a != 'install'])

    if extra_args[0] == 'configure':
        import configure
        return configure.main(args[1:])

    if extra_args[0] == 'package':
        import package
        return package.make_tarfile_main(options, extra_args[1:])

    if extra_args[0] == 'upload':
        import package
        return package.upload_main(options, extra_args[1:])

    if extra_args[0] == 'build':
        import build
        return build.main(options, extra_args[1:])

    parser.print_usage()
    print >>sys.stderr, "run '%s --help' for more details" % sys.argv[0]
    return 1

if __name__ == "__main__":
    sys.exit( main( sys.argv[1:] ) )

