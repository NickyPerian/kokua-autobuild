# $LicenseInfo:firstyear=2010&license=mit$
# Copyright (c) 2010, Linden Research, Inc.
# $/LicenseInfo$

"""
API to access the autobuild package description config file.

This includes the ConfigFile class which is used to load, save,
and manipulate autobuild XML configuration files. Also the
PackageInfo class that encapsulates all the metadata for a 
single package description.

Author : Martin Reddy
Date   : 2010-04-13
"""

import os
import common
from llbase import llsd

AutobuildError = common.AutobuildError

AUTOBUILD_CONFIG_FILE="autobuild.xml"
INSTALLED_CONFIG_FILE="installed-packages.xml"

AUTOBUILD_CONFIG_VERSION="1.1"

PACKAGES_CONFIG_FILE="packages.xml"  # legacy file - do not use!

class PackageInfo(dict):
    """
    The PackageInfo class describes all the metadata for a single
    package in a ConfigFile. This is essentially a dictionary, so
    you can always access fields directly. Additionally, a number
    of accessors are provide for common metadata entries, such as
    copyright, description, and the various platform urls etc.

    The following code shows how to output the package description
    in a human-readable form, where pi is of type PackageInfo.

    print "Copyright:", pi.copyright
    print "Description:", pi.description

    Setting a key's value to None will remove that key from the
    PackageInfo structure. For example, the following will cause the
    copyright field to be removed from the package description.
    
    pi.copyright = None

    See the supported_properties dict for the set of currently
    supported properties. These map to fields of the same name in the
    config file.

    Also, see the supported_platform_properties dict for the set of
    platform-specific fields. These support a property that returns the
    list of platforms that have a definitions for that field. There are
    also explicit getter/setter methods to support these. The getter 
    will return the definition for the platform 'common' if the specified
    platform is not defined (or None if neither are defined). E.g.,

    for platform in pi.packages:
        print platform
        print pi.archives_url(platform)
        print pi.archives_md5(platform)

    for platform in pi.manifest:
        print platform
        print pi.manifest_files(platform)

    Design note: a ConfigFile contains 2 sections: a list of
    installable packages and a single description to build a package.
    Currently, we use PackageInfo() to describe both types of
    information. In the future, we may decide to introduce a separate
    PackageDesc() class so that each is modelled separately.
    """

    # basic read-write properties that describe the package
    supported_properties = {
        'name':         'The name of this package',
        'copyright':    'The copyright statement for the source code',
        'summary':      'A one-line overview of the package',
        'description':  'A longer description of the package',
        'license':      'The name of the software license (not the full text)',
        'licensefile':  'The relative path to the license file in the archive',
        'homepage':     'The home page URL for the source code being built',
        'uploadtos3':   'Whether the package should also be uploaded to Amazon S3',
        'source':       'URL where source for package lives',
        'sourcetype':   'The form of the source, e.g., archive, svn, hg, pypi',
        'sourcedir':    'The directory where sources extract/checkout to',
        'version':      'The current version of the source package',
        'patches':      'A list of patch(1) files to apply to the sources',
        'obsoletes':    'List of packages to uninstalled when this one is installed',
        }

    # platform-specific read-only properties that list the defined platforms
    supported_platform_properties = {
        'archives':     'List of platform-specific archives for the install command',
        'dependencies': 'List of packages that this package depends upon to build',
        'configure':    'List of platform-specific commands to configure the build',
        'build':        'List of platform-specific commands to build the software',
        'builddir':     'The directory into which the build products are written',
        'postbuild':    'Post build commands to relocate files in the builddir',
        'manifest':     'List of platform-specific commands to build the software',
        }

    def __init__(self, dictvalue=None, name=None):
        if dictvalue:
            for key in dictvalue.keys():
                self[key] = dictvalue[key]
        self.name = name

    def __getattr__(self, name):
        if self.supported_properties.has_key(name):
            return self.get_key(name)
        if self.supported_platform_properties.has_key(name):
            return self.__platform_list(name.replace("Platforms", ""))
        raise AutobuildError('%s is not a supported property' % name)

    def __setattr__(self, name, value):
        if self.supported_properties.has_key(name):
            return self.set_key(name, value)
        if self.supported_platform_properties.has_key(name):
            raise AutobuildError("%s is a read-only property" % name)
        raise AutobuildError('%s is not a supported property' % name)

    def archives_url(self, platform):
        # *TODO: remove legacy support for 'packages'
        url = self.__platform_key('archives', platform, 'url')
        if not url:
            url = self.__platform_key('packages', platform, 'url')
        return url
    def set_archives_url(self, platform, value):
        return self.__set_platform_key('archives', platform, 'url', value)
    def archives_files(self, platform):
        return self.__platform_key('archives', platform, 'files')
    def set_archives_files(self, platform, value):
        return self.__set_platform_key('archives', platform, 'files', value)
    def archives_md5(self, platform):
        # *TODO: remove legacy support for 'packages'
        md5sum = self.__platform_key('archives', platform, 'md5sum')
        if not md5sum:
            md5sum = self.__platform_key('packages', platform, 'md5sum')
        return md5sum
    def set_archives_md5(self, platform, value):
        return self.__set_platform_key('archives', platform, 'md5sum', value)

    def dependencies_url(self, platform):
        return self.__platform_key('dependencies', platform, 'url')
    def set_dependencies_url(self, platform, value):
        return self.__set_platform_key('dependencies', platform, 'url', value)
    def dependencies_md5(self, platform):
        return self.__platform_key('dependencies', platform, 'md5sum')
    def set_dependencies_md5(self, platform, value):
        return self.__set_platform_key('dependencies', platform, 'md5sum', value)

    def configure_command(self, platform):
        return self.__platform_key('configure', platform, 'command')
    def set_configure_command(self, platform, value):
        return self.__set_platform_key('configure', platform, 'command', value)

    def build_command(self, platform):
        return self.__platform_key('build', platform, 'command')
    def set_build_command(self, platform, value):
        return self.__set_platform_key('build', platform, 'command', value)
   
    def build_directory(self, platform):
        return self.__platform_key('build', platform, 'directory')
    def set_build_directory(self, platform, value):
        return self.__set_platform_key('build', platform, 'directory', value)

    def post_build_command(self, platform):
        return self.__platform_key('postbuild', platform, 'command')
    def set_post_build_command(self, platform, value):
        return self.__set_platform_key('postbuild', platform, 'command', value)

    def manifest_files(self, platform):
        return self.__platform_key('manifest', platform, 'files')
    def set_manifest_files(self, platform, value):
        return self.__set_platform_key('manifest', platform, 'files', value)

    def get_key(self, key):
        return self.get(key)
    def set_key(self, key, value):
        if value is None:
            if self.has_key(key):
                del self[key]
        else:
            self[key] = value

    def __platform_list(self, container):
        if self.has_key(container):
            return self[container].keys()
        return []
    def __platform_key(self, container, platform, key):
        try:
            return self[container][platform][key]
        except KeyError:
            try:
                return self[container]['common'][key]
            except KeyError:
                return None
    def __set_platform_key(self, container, platform, key, value):
        if not self.has_key(container):
            self[container] = {}
        if not self[container].has_key(platform):
            self[container][platform] = {}
        if value is None:
            if self[container][platform].has_key(key):
                del self[container][platform][key]
        else:
            self[container][platform][key] = value
        

class ConfigFile(object):
    """
    An autobuild configuration file contains all the package and
    for a build or an install. Using the ConfigFile class, you
    can read, manipulate, and save autobuild configuration files.

    Conceptually, a ConfigFile contains two optional sections: a set
    of named PackageInfo objects that describe each installable
    package, and a description of how to build the current
    package. This generic format is used by two autobuild file types:
    autobuild.xml and installed-packages.xml.

    Here's an example of reading a configuration file and printing
    some interesting information from it:

    c = ConfigFile()
    c.load()
    print "No. of packages =", c.package_count
    for name in c.package_names:
        package = c.package(name)
        print "Package '%s'" % name
        print "  Description: %s" % package.description
        print "  Copyright: %s" % package.copyright

    And here's an example of modifying some data in the config file
    and writing the file back to disk. In this case, changing the
    description field for every package in the config file.

    c = ConfigFile()
    c.load()
    for name in c.package_names:
        package = c.package(name)
        package.description = "Lynx woz here"
        c.set_package(name, package)
    c.save()

    You can access the package description for the current package via
    the package_definition property. This lets you access all of the
    information on how to configure, build, package, and upload the
    current package. For example,

    c = ConfigFile()
    c.load()
    pd = c.package_definition
    print "Name =", pd.name

    """
    def __init__(self, package_name='anonymous'):
        self.filename = None
        self.packages = {}
        self.definition = PackageInfo(name=package_name)
        self.changed = False

    def load(self, config_filename=AUTOBUILD_CONFIG_FILE):
        """
        Loads an autobuild configuration file from the named file.
        If no filename is specified then "autobuild.xml" will be
        assumed.

        Returns False if no file could not be loaded successfully.
        """

        # initialize the object state
        self.filename = config_filename
        self.packages = {}
        self.definition = {}
        self.changed = False

        # try to find the config file in the current, or any parent, dir
        if not os.path.isabs(self.filename):
            dir = os.getcwd()
            while not os.path.exists(os.path.join(dir, config_filename)) and len(dir) > 3:
                dir = os.path.dirname(dir)
            self.filename = os.path.join(dir, config_filename)

        # if this failed, then fallback to "packages.xml" for legacy support
        # *TODO: remove this legacy support eventually (Aug 2010)
        if not os.path.isabs(self.filename) and config_filename == AUTOBUILD_CONFIG_FILE:
            dir = os.getcwd()
            while not os.path.exists(os.path.join(dir, PACKAGES_CONFIG_FILE)) and len(dir) > 3:
                dir = os.path.dirname(dir)
            self.filename = os.path.join(dir, PACKAGES_CONFIG_FILE)

        if not os.path.exists(self.filename):
            # reset to passed in argument to allow --create options to work
            self.filename = config_filename
            return False

        # load the file as a serialized LLSD
        print "Loading %s" % self.filename
        try:
            keys = llsd.parse(file(self.filename, 'rb').read())
        except llsd.LLSDParseError:
            raise AutobuildError("Config file is corrupt: %s. Aborting..." % self.filename)

        # parse the contents of the file
        parsed_file = False
        if keys.has_key('package_definition'):
            # support new-style format that merges autobuild.xml and packages.xml
            self.definition = PackageInfo(keys['package_definition'], keys['package_definition'].get('name', None))
            parsed_file = True

        if keys.has_key('installables'):
            # support new-style format for binary packages to install
            for name in keys['installables']:
                self.packages[name] = PackageInfo(keys['installables'][name], name)
            parsed_file = True

        # if we loaded new-style format data, then we're done
        if parsed_file:
            return True

        # handle legacy file formats, such as the separate
        # autobuild.xml and packages.xml files
        # *TODO: remove all of this legacy support eventually (Aug 2010)
        if keys.has_key('package_name'):
            # support the old 'package_name' format for a short while...
            self.packages[keys['package_name']] = PackageInfo(keys, keys['package_name'])

        else:
            # support the old autobuild.xml and packages.xml formats

            # work out if we have loaded an autobuild.xml file, or one
            # that looks like an autobuild.xml file (may be named different)
            if (len(keys) == 1 or AUTOBUILD_CONFIG_FILE in self.filename) and PACKAGES_CONFIG_FILE not in self.filename:
                name = keys.keys()[0]
                self.definition = PackageInfo(keys[name], name)

                # also merge in the contents of "packages.xml", if present
                package_file = os.path.join(os.path.dirname(self.filename), PACKAGES_CONFIG_FILE)
                if os.path.exists(package_file):
                    print "Merging %s" % package_file
                    try:
                        package_keys = llsd.parse(file(package_file, 'rb').read())
                    except llsd.LLSDParseError:
                        raise AutobuildError("Config file is corrupt: %s. Aborting..." % package_file)

                    # add the list of installables from the packages.xml file
                    for name in package_keys.keys():
                        self.packages[name] = PackageInfo(package_keys[name], name)
                    
            else:
                # otherwise, assume that we have loaded packages.xml only
                for name in keys.keys():
                    self.packages[name] = PackageInfo(keys[name], name)

        return True

    def save(self, config_filename=None):
        """
        Save the current configuration file state to disk. If no
        filename is specified, the name of the file will default
        to the same file that the config data was loaded from
        (or the explicit filename specified in a previous call to
        this save method).
        Returns False if the file could not be saved successfully.
        """
        # use the name of file we loaded from, if no filename given
        if config_filename:
            self.filename = config_filename
            # if we loaded from a legacy packages.xml, save to autobuild.xml
            # *TODO: remove this line when legacy support no longer required
            self.filename = self.filename.replace(PACKAGES_CONFIG_FILE, AUTOBUILD_CONFIG_FILE)
        if not self.filename:
            self.filename = AUTOBUILD_CONFIG_FILE

        # create an appropriate dict structure to write to the file
        state = { 'version': AUTOBUILD_CONFIG_VERSION }

        if self.definition:
            state['package_definition'] = dict(self.definition)

        if self.packages:
            state['installables'] = {}
            for name in self.packages:
                value = dict(self.packages[name])
                # don't write out the package name - its the key name
                if value.has_key('name'):
                    del value['name']
                state['installables'][name] = value

        # try to write out to the file
        try:
            file(self.filename, 'wb').write(llsd.format_pretty_xml(state))
        except IOError:
            print "Could not save to file: %s" % self.filename
            return False

        return True

    # return the number of packages in this file and their names
    package_count = property(lambda x: len(x.packages))
    package_names = property(lambda x: x.packages.keys())

    # test whether the file is empty, i.e., contains no packages or package definition
    empty = property(lambda x: len(x.packages) == 0 and len(x.definition) == 0)

    # check that a file contains only 1 package, and return it (or None)
    package_definition = property(lambda x: len(x.definition) > 0 and x.definition or None)

    def package(self, name):
        """
        Return a PackageInfo object for the named package in this
        config file.  None will be returned if no such named package
        exists.
        """
        if not self.packages.has_key(name):
            return None
        return self.packages[name]

    def set_package(self, name, value):
        """
        Add/Update the PackageInfo object for a named package to this
        config file. This will overwrite any existing package
        description with the same name.
        """
        self.packages[name] = value
        self.changed = True
