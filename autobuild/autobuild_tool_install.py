# $LicenseInfo:firstyear=2010&license=mit$
# Copyright (c) 2010, Linden Research, Inc.
# $/LicenseInfo$

"""
Install files into a repository.

This autobuild sub-command will read a packages.xml file and install any
new or updated packages defined in that file to the install directory.
An install-packages.xml file is also maintained in the install directory
to specify all the files that have been installed.

Author : Martin Reddy
Date   : 2010-04-19
"""

# For reference, the old indra install.py specification at:
# https://wiki.lindenlab.com/wiki/User:Phoenix/Library_Installation
# Proposed platform spec: OS[/arch[/compiler[/compiler_version]]]
# e.g., windows/i686/vs/2005 or linux/x86_64/gcc/3.3
#
# *TODO: add support for an 'autobuild uninstall' command
# *TODO: add an 'autobuild info' command to query config file contents

import os
import sys
import optparse
import pprint
import common
import configfile
import autobuild_base
from llbase import llsd

__help = """\
This autobuild command fetches and installs package archives.

The command will read a packages.xml file and install any new or
updated packages defined in that file to the install directory. An
install-packages.xml manifest file is also maintained in the install
directory to specify all the files that have been installed.

Downloaded package archives are cached on the local machine so that
they can be shared across multiple repositories and to avoid unnecessary
downloads. A new package will be downloaded if the packages.xml files is
updated with a new package URL or MD5 sum.

If an MD5 checksum is provided for a package in the packages.xml file,
this will be used to validate the downloaded package. The package will
not be installed if the MD5 sum does not match.

A package description must include the name of the license that applies to
the package. It may also contain the archive-relative path(s) to the full
text license file that is stored in the package archive. Both of these
metadata will be checked during the install process.

If no packages are specified on the command line, then the defaut
behavior is to install all known archives appropriate for the platform
specified. You can specify more than one package on the command line.

Supported platforms include: windows, darwin, linux, and a common platform
to represent a platform-independent package.
"""

def add_arguments(parser):
    parser.add_argument(
        'package',
        nargs='*',
        help='List of packages to consider for installation.')
    parser.add_argument(
        '--dry-run', 
        action='store_true',
        default=False,
        dest='dryrun',
        help='Do not actually install files. Downloads will still happen.')
    parser.add_argument(
        '--package-info',
        default=configfile.PACKAGES_CONFIG_FILE,
        dest='install_filename',
        help='The file used to describe what should be installed.')
    parser.add_argument(
        '--installed-manifest', 
        default=configfile.INSTALLED_CONFIG_FILE,
        dest='installed_filename',
        help='The file used to record what is installed.')
    parser.add_argument(
        '-p', '--platform', 
        default=common.get_current_platform(),
        dest='platform',
        help='Override the automatically determined platform.')
    parser.add_argument(
        '--install-dir', 
        default=None,
        dest='install_dir',
        help='Where to unpack the installed files.')
    parser.add_argument(
        '--list', 
        action='store_true',
        default=False,
        dest='list_archives',
        help="List the archives specified in the package file.")
    parser.add_argument(
        '--list-installed', 
        action='store_true',
        default=False,
        dest='list_installed',
        help="List the installed package names and exit.")
    parser.add_argument(
        '--skip-license-check', 
        action='store_false',
        default=True,
        dest='check_license',
        help="Do not perform the license check.")
    parser.add_argument(
        '--list-licenses', 
        action='store_true',
        default=False,
        dest='list_licenses',
        help="List known licenses and exit.")
    parser.add_argument(
        '--export-manifest', 
        action='store_true',
        default=False,
        dest='export_manifest',
        help="Print the install manifest to stdout and exit.")

def add_old_arguments(parser):
    parser.add_option(
        '--dry-run', 
        action='store_true',
        default=False,
        dest='dryrun',
        help='Do not actually install files. Downloads will still happen.')
    parser.add_option(
        '--package-info',
        default=configfile.PACKAGES_CONFIG_FILE,
        dest='install_filename',
        help='The file used to describe what should be installed.')
    parser.add_option(
        '--installed-manifest', 
        default=configfile.INSTALLED_CONFIG_FILE,
        dest='installed_filename',
        help='The file used to record what is installed.')
    parser.add_option(
        '-p', '--platform', 
        default=common.get_current_platform(),
        dest='platform',
        help='Override the automatically determined platform.')
    parser.add_option(
        '--install-dir', 
        default=None,
        dest='install_dir',
        help='Where to unpack the installed files.')
    parser.add_option(
        '--list', 
        action='store_true',
        default=False,
        dest='list_archives',
        help="List the archives specified in the package file.")
    parser.add_option(
        '--list-installed', 
        action='store_true',
        default=False,
        dest='list_installed',
        help="List the installed package names and exit.")
    parser.add_option(
        '--skip-license-check', 
        action='store_false',
        default=True,
        dest='check_license',
        help="Do not perform the license check.")
    parser.add_option(
        '--list-licenses', 
        action='store_true',
        default=False,
        dest='list_licenses',
        help="List known licenses and exit.")
    parser.add_option(
        '--export-manifest', 
        action='store_true',
        default=False,
        dest='export_manifest',
        help="Print the install manifest to stdout and exit.")

def print_list(label, array):
    """
    Pretty print an array of strings with a given label prefix.
    """
    list = "none"
    if array:
        array.sort()
        list = ", ".join(array)
    print "%s: %s" % (label, list)
    return True
    
def handle_query_args(options, config_file, installed_file):
    """
    Handle any arguments to query for package information.
    Returns True if an argument was handled.
    """
    if options.list_installed:
        return print_list("Installed", installed_file.packages)

    if options.list_archives:
        return print_list("Packages", config_file.packages)

    if options.list_licenses:
        licenses = []
        for p in config_file.packages:
            licenses.append(p.license)
        return print_list("Licenses", licenses)

    if options.export_manifest:
        for name in installed_file.packages:
            package = installed_file.package(name)
            pprint.pprint(package)
        return True

    return False

def get_packages_to_install(packages, config_file, installed_config, preferred_platform):
    """
    Given the (potentially empty) list of package archives on the command line, work out
    the set of packages that are out of date and require a new download/install. This will
    return [] if all packages are up to date.
    """

    # if no packages specified, consider all
    if not len(packages):
        packages = config_file.packages

    # compile a subset of packages we actually need to install
    to_install = []
    for pname in packages:
        
        toinstall = config_file.package(pname)
        installed = installed_config.package(pname)

        # raise error if named package doesn't exist in packages.xml
        if not toinstall:
            raise RuntimeError('Unknown package: %s' % pname)

        # work out the platform-specific or common url to use
        platform = preferred_platform
        if not toinstall.packages_url(platform):
            platform = 'common'
        if not toinstall.packages_url(platform):
           raise RuntimeError("No url specified for this platform for %s" % pname)

        # install this package if it is new or out of date
        if installed == None or \
           toinstall.packages_url(platform) != installed.packages_url(platform) or \
           toinstall.packages_md5(platform) != installed.packages_md5(platform):
            to_install.append(pname)

    return to_install

def pre_install_license_check(packages, config_file):
    """
    Return true if all specified packages have a license property set.
    """
    for pname in packages:
        package = config_file.package(pname)
        license = package.license
        if not license:
            raise RuntimeError("No license specified for %s. Aborting..." % pname)

    return True

def do_install(packages, config_file, installed_file, preferred_platform, install_dir, dryrun):
    """
    Install the specified list of packages. This will download the
    packages to the local cache, extract the contents of those
    archives to the install dir, and update the installed_file config.
    """

    # check that the install dir exists...
    if not os.path.exists(install_dir):
        os.makedirs(install_dir)

    # Filter for files which we actually requested to install.
    for pname in packages:

        # find the url/md5 for the platform, or fallback to 'common'
        package = config_file.package(pname)
        platform = preferred_platform
        if not package.packages_url(platform):
            platform = 'common'

        url = package.packages_url(platform)
        md5 = package.packages_md5(platform)
        cachefile = common.get_package_in_cache(url)

        # download the package, if it's not already in our cache
        if not common.is_package_in_cache(url):

            # download the package to the cache
            if not common.download_package(url):
                raise RuntimeError("Failed to download %s" % url)

            # error out if MD5 doesn't matches
            if not common.does_package_match_md5(url, md5):
                common.remove_package(url)
                raise RuntimeError("md5 mismatch for %s" % cachefile)

        # dry run mode = download but don't install packages
        if dryrun:
            print "Dry run mode: not installing %s" % pname
            continue

        # extract the files from the package
        files = common.extract_package(url, install_dir)

        # update the installed-packages.xml file
        package = installed_file.package(pname)
        if not package:
            package = configfile.PackageInfo()
        package.set_packages_url(platform, url)
        package.set_packages_md5(platform, md5)
        package.set_packages_files(platform, files)
        installed_file.set_package(pname, package)

def install_packages(options, args):
    # write packages into 'packages' subdir of build directory by default
    if not options.install_dir:
        import configure
        options.install_dir = configure.get_package_dir()

    # get the absolute paths to the install dir and installed-packages.xml file
    install_dir = os.path.realpath(options.install_dir)
    installed_filename = options.installed_filename
    if not os.path.isabs(installed_filename):
        installed_filename = os.path.join(install_dir, installed_filename)

    # load the list of already installed packages
    installed_file = configfile.ConfigFile()
    installed_file.load(os.path.join(options.install_dir, installed_filename))

    # load the list of packages to install
    config_file = configfile.ConfigFile()
    config_file.load(options.install_filename)
    if config_file.empty:
        print "No package information to load from", options.install_filename
        return 0

    # get the list of packages to actually installed
    packages = get_packages_to_install(args, config_file, installed_file, options.platform)

    # handle any arguments to query for information
    if handle_query_args(options, config_file, installed_file):
        return 0

    # check the license properties for the packages to install
    if options.check_license and not pre_install_license_check(packages, config_file):
        return 1

    # do the actual install of the new/updated packages
    do_install(packages, config_file, installed_file, options.platform, install_dir,
               options.dryrun)

    # update the installed-packages.xml file, if it was changed
    if installed_file.changed:
        installed_file.save()
    else:
        print "All packages are up to date."
    return 0

# The Old Way
def main(args):
    parser = optparse.OptionParser(
        usage="usage: %prog [options] [package1 [package2...]]",
        description=__help)
    add_old_arguments(parser)
    options, args = parser.parse_args(args)
    install_packages(options, args)

# The New Way
class autobuild_tool(autobuild_base.autobuild_base):
    def get_details(self):
        return dict(name='install', description='Fetch and install package archives.')

    def register(self, parser):
        add_arguments(parser)

    def run(self, args):
        install_packages(args, args.package)

if __name__ == '__main__':
    sys.exit("Please invoke this script using 'autobuild install'")
