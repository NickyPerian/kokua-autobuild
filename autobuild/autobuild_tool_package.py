# $LicenseInfo:firstyear=2010&license=mit$
# Copyright (c) 2010, Linden Research, Inc.
# $/LicenseInfo$

"""
Create archives of build output, ready for upload to the server.
"""

import sys
import os
import tarfile
import time
import glob
import common
import configfile
import autobuild_base
from connection import SCPConnection, S3Connection

AutobuildError = common.AutobuildError

def add_arguments(parser):
    parser.add_argument(
        '--dry-run', 
        action='store_true',
        default=False,
        dest='dryrun',
        help='Do not actually create an archive file.')
    parser.add_argument(
        '--package-info',
        default=configfile.BUILD_CONFIG_FILE,
        dest='autobuild_filename',
        help='The file used to describe how to build the package.')
    parser.add_argument(
        '--archive-name',
        default=None,
        dest='archive_filename',
        help='The filename of the archive that autobuild will create.')
    parser.add_argument(
        '-p', '--platform', 
        default=common.get_current_platform(),
        dest='platform',
        help='Override the automatically determined platform.')
    parser.add_argument(
        '--build-dir',
        default=None,
        dest='build_dir',
        help='Where the output of the build command can be found.')

def generate_archive_name(package, platform, suffix=''):
    """
    Create a tarball name for a given package and platform.
    """
    name = package.name + '-' + package.version + '-'
    name += '-'.join(platform.split('/')) + '-'
    name += time.strftime("%Y%m%d") + suffix
    name += '.tar.bz2'
    return name

def generate_unique_archive_name(package, platform):
    """
    Create a tarball name for the package that will not conflict with
    other tarball names currently on S3 or install-packages.

    N.B. This name might conflict at upload time if there is a long
    gap between packaging and uploading. We should really do this
    check as part of the upload process.
    """
    S3Conn = S3Connection()
    SCPConn = SCPConnection()

    unique = False
    suffix = ''
    next_suffix = 'a'
    while not unique:

        # get the next archive name to try
        name = generate_archive_name(package, platform, suffix)
        if suffix:
            print "Testing:", name

        # see if this name conflicts with a name on the server
        try:
            scp_exists = SCPConn.SCPFileExists(name)
            s3_exists = S3Conn.S3FileExists(name)
        except:
            print "Cannot contact SCP/S3! Archive name may conflict on the server."
            return name

        # yay! we found a non-conflicting change
        if not scp_exists and not s3_exists:
            if suffix:
                print "Found unique name:", name
            return name

        # keep trying... until we run out of alphabet
        if suffix == 'z':
           raise AutobuildError("Cannot create a unique archive name! I tried really hard though.") 
        suffix = next_suffix
        next_suffix = chr(ord(next_suffix)+1)

def get_file_list(package, platform, build_dir):
    """
    Expand the list of files specified in the platform-specific
    manifest array and the common-platform manifest array.
    Support glob-style wildcards.
    """

    # combine the platform-specific and common manifest spec
    platform_files = package.manifest_files(platform)
    common_files = package.manifest_files('common')
    if not platform_files:
        platform_files = []
    if not common_files:
        common_files = []

    # remove duplicates from the combine
    manifest = {}
    for file in platform_files + common_files:
        manifest[file] = True
    manifest = manifest.keys()

    # check that we have a non-zero set of manifest files
    if not manifest:
        raise AutobuildError("No manifest files specified for %s" % package.name)

    # glob the manifest entries to expand wildcards
    files = []
    for file in manifest:
        expanded = glob.glob(os.path.join(build_dir, file))
        for expfile in expanded:
            # keep the file list relative to the build dir
            expfile = expfile.replace(build_dir, "")
            expfile = expfile.lstrip(os.path.sep)
            files.append(expfile)

    return files

def check_license(package, build_dir, filelist):
    """
    Ensure that the package defines a license string and that it
    contains a valid licensefile specification.
    """
    
    # assert that the license field is non-empty
    if not package.license:
        raise AutobuildError("The license field is not specified for %s" % package.name)

    # if not specified, assume a default naming convention
    licensefile = package.licensefile
    if not licensefile:
        licensefile = 'LICENSES/%s.txt' % package.name

    # if a URL is given, assuming it's valid for now
    if licensefile.startswith('http://'):
        return

    # check that the license file exists
    if licensefile not in filelist:
        raise AutobuildError("License file %s not found in manifest" % licensefile)

def create_tarfile(tarfilename, build_dir, filelist):
    """
    Create the tarball using the list of files in the build dir.
    """

    # make sure the output directory exists
    if not os.path.exists(os.path.dirname(tarfilename)):
        os.makedirs(os.path.dirname(tarfilename))

    # chdir to the build dir to keep paths relative
    os.chdir(build_dir)

    # add the files to the tarball
    tfile = tarfile.open(tarfilename, 'w:bz2')
    for file in filelist:
        print "Adding", file
        try:
            tfile.add(file)
        except:
            raise AutobuildError("Unable to add %s to %s" % (file, tarfilename))
    tfile.close()

    print "Archive created: %s" % tarfilename

def create_archive(options):
    """
    Create a package archive given a set of command line options.
    """

    # read the autobuild.xml file and get the one PackageInfo object
    config_file = configfile.ConfigFile()
    config_file.load(options.autobuild_filename)
    package = config_file.package_definition
    if not package:
        raise AutobuildError("Config file must contain a single package definition")

    # get the build output directory - check it exists
    build_dir = options.build_dir
    if not build_dir:
        build_dir = package.builddir
        if not build_dir:
            raise AutobuildError("Build output directory not specified in config file")

    if not os.path.exists(build_dir):
        raise AutobuildError("Directory does not exist: %s" % build_dir)

    # Get the list of files to add to the tarball
    files = get_file_list(package, options.platform, build_dir)
    if not files:
        raise AutobuildError("No files to package found in %s" % build_dir)

    # Make sure that a license file has be specified
    check_license(package, build_dir, files)

    # work out the name of the package archive
    tarfilename = options.archive_filename
    if not tarfilename:
        tardir = os.path.dirname(config_file.filename)
        tarname = generate_unique_archive_name(package, options.platform)
        tarfilename = os.path.join(tardir, tarname)

    # create the package archive (unless in dryrun mode)
    if options.dryrun:
        for file in files:
            print "Adding (dry-run)", file
        print "Dry-run: would have created %s" % tarfilename
    else:
        create_tarfile(tarfilename, build_dir, files)


# define the entry point to this autobuild tool
class autobuild_tool(autobuild_base.autobuild_base):
    def get_details(self):
        return dict(name=self.name_from_file(__file__),
                    description='Creates archives of build output, ready for upload to the server.')

    def register(self, parser):
        add_arguments(parser)

    def run(self, args):
        create_archive(args)

if __name__ == '__main__':
    sys.exit("Please invoke this script using 'autobuild %s'" %
             autobuild_tool().get_details()["name"])
