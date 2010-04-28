#!/usr/bin/env python

import os
import shutil
import subprocess
import sys
import tempfile

import common
import autobuild_base

from llbase import llsd

# for the time being, we expect that we're checked out side-by-side with
# parabuild buildscripts, so back up a level to find $helper.
get_params = None
helper = os.path.join(os.path.dirname(__file__),
                      os.pardir,
                      os.pardir,
                      'buildscripts/hg/bin')
if os.path.exists(helper):
    # Append helper to sys.path.
    _helper_idx = len(sys.path)
    sys.path.append(helper)
    assert sys.path[_helper_idx] == helper

    try:
        import get_params
        print >>common.log(), "found get_params: '%s'" % get_params.__file__
    except ImportError:
        pass
    # *TODO - restore original sys.path value

def load_vsvars(vsver):
    vsvars_path = os.path.join(os.environ["VS%sCOMNTOOLS" % vsver], "vsvars32.bat")
    temp_script_name = tempfile.mktemp(suffix=".cmd")

    shutil.copy(vsvars_path, temp_script_name)
    # append our little llsd+notation bit to the end
    temp_script_file = open(temp_script_name, "a")
    temp_script_file.write("""
        echo {
        echo "VSPATH":"%PATH%",
        echo "VSINCLUDE":"%INCLUDE%",
        echo "VSLIB":"%LIB%",
        echo "VSLIBPATH":"%LIBPATH%",
        echo }
    """)
    temp_script_file.close()

    cmd = subprocess.Popen(['cmd', '/Q', '/C', temp_script_name], stdout=subprocess.PIPE)
    (cmdout, cmderr) = cmd.communicate()

    os.remove(temp_script_name)

    # *HACK
    # slice off the 1st line ("Setting environment for using..." preamble)
    cmdout = '\n'.join(cmdout.split('\n')[1:])
    # escape backslashes
    cmdout = '\\\\'.join(cmdout.split('\\'))

    vsvars = llsd.parse(cmdout)

    # translate paths from windows to cygwin format
    vsvars['VSPATH'] = ":".join(
        ['"$(cygpath -u \'%s\')"' % p for p in vsvars['VSPATH'].split(';') ]
    )
    return vsvars

environment_template = """
    export AUTOBUILD="%(AUTOBUILD_EXECUTABLE_PATH)s"
    export AUTOBUILD_VERSION_STRING="%(AUTOBUILD_VERSION_STRING)s"
    export AUTOBUILD_PLATFORM="%(AUTOBUILD_PLATFORM)s"
    if [ -z "$PARABUILD_BUILD_NAME" ] ; then
        # only define this function if parabuild isn't present
        upload_item () {
            # back-compat wrapper for parbuild buildscripts
            local item_type="$1"
            local item="$2"
            local encoding="$3"
            local asset_urls="${4:-"$build_log_dir"/asset_urls}"
            local asset_name="$5"

            # *TODO - delegate this properly to 'autobuild upload'
            "$AUTOBUILD" upload "$item"
        }
    fi
    fail () {
        echo "BUILD FAILED"
        if [ -n "$PARABUILD_BUILD_NAME" ] ; then
            # if we're running under parabuild then we have to clean up its stuff
            finalize false "$@"
        else
            exit 1
        fi
    }
    pass () {
        echo "BUILD SUCCEEDED"
        succeeded=true
    }

    # imported build-lindenlib functions
    fetch_archive () {
        local url=$1
        local archive=$2
        local md5=$3
        if ! [ -r "$archive" ] ; then
            curl -L -o "$archive" "$url"                    || return 1
        fi
        if [ "$AUTOBUILD_PLATFORM" = "darwin" ] ; then
            test "$md5 $archive" = "$(md5 -r "$archive")"
        else
            echo "$md5 *$archive" | md5sum -c
        fi
    }
    extract () {
        # Use a tar command appropriate to the extension of the filename passed as
        # $1. If a subsequent update of a given tarball changes compression types,
        # this should hopefully avoid having to go through this script to update
        # the tar switches to correspond to the new file type.
        switch="-x"
        # Decide whether to specify -xzvf or -xjvf based on whether the archive
        # name ends in .tar.gz or .tar.bz2.
        if [ "${1%%.tar.gz}" != "$1" ]
        then switch="${switch}z"
        elif [ "${1%%.tar.bz2}" != "$1" ]
        then switch="${switch}j"
        fi
        switch="${switch}vf"
        tar "$switch" "$1" || exit 1
    }
    calc_md5 () {
        local archive=$1
        local md5_cmd=md5sum
        if [ "$AUTOBUILD_PLATFORM" = "darwin" ] ; then
            md5_cmd="md5 -r"
        fi
        $md5_cmd "$archive" | cut -d ' ' -f 1
    }

    MAKEFLAGS="%(MAKEFLAGS)s"
    DISTCC_HOSTS="%(DISTCC_HOSTS)s"
"""

if common.get_current_platform() is "windows":
    windows_template = """
    USE_INCREDIBUILD=%(USE_INCREDIBUILD)s
    build_vcproj() {
        local vcproj=$1
        local config=$2

        if ((%(USE_INCREDIBUILD)s)) ; then
            BuildConsole "$vcproj" /CFG="$config"
        else
            devenv "$vcproj" /build "$config"
        fi
    }

    build_sln() {
        local solution=$1
        local config=$2
        local proj=$3

        if ((%(USE_INCREDIBUILD)s)) ; then
            if [ -z "$proj" ] ; then
                BuildConsole "$solution" /CFG="$config"
            else
                BuildConsole "$solution" /PRJ="$proj" /CFG="$config"
            fi
        else
            if [ -z "$proj" ] ; then
                devenv "$solution" /build "$config"
            else
                devenv "$solution" /build /project "$proj" /projectconfig "$config"
            fi
        fi
    }

    # function for loading visual studio related env vars
    load_vsvars() {
        export PATH=%(VSPATH)s:"$PATH"
        export INCLUDE="%(VSINCLUDE)s"
        export LIB="%(VSLIB)s"
        export LIBPATH="%(VSLIBPATH)s"
    }
    """
    environment_template = "%s\n%s" % (environment_template, windows_template)

def do_source_environment(args):
    var_mapping = {
            'AUTOBUILD_EXECUTABLE_PATH':common.get_autobuild_executable_path(),
            'AUTOBUILD_VERSION_STRING':"0.0.1-mvp",
            'AUTOBUILD_PLATFORM':common.get_current_platform(),
            'MAKEFLAGS':"",
            'DISTCC_HOSTS':"",
            'USE_INCREDIBUILD':1,
        }

    if common.get_current_platform() is "windows":
        # reset stdout in binary mode so sh doesn't get confused by '\r'
        import msvcrt
        msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)

        # load vsvars32.bat variables
        # *TODO - find a way to configure this instead of hardcoding to vc80
        var_mapping.update(load_vsvars("80"))

    sys.stdout.write(environment_template % var_mapping)

    if get_params:
        # *TODO - run get_params.generate_bash_script()
        pass

class autobuild_tool(autobuild_base.autobuild_base):
    def get_details(self):
        return dict(name=self.name_from_file(__file__),
                    description='Prints out the shell environment Autobuild-based buildscripts to use (by calling \'eval\').')
    
    # called by autobuild to add help and options to the autobuild parser, and
    # by standalone code to set up argparse
    def register(self, parser):
        parser.add_argument('-v', '--version', action='version', version='source_environment tool module 1.0')

    def run(self, args):
        do_source_environment(args)

