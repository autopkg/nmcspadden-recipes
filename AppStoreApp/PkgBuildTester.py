#!/usr/bin/python
#
# Copyright 2014 Shea G. Craig
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Look in the build directory for a pre-existing package."""


import os.path
import subprocess
import xml.etree.ElementTree as ET

from autopkglib import Processor, ProcessorError


__all__ = ["PkgBuildTester"]


class PkgBuildTester(Processor):
    """Look in the build directory for a pre-existing package."""
    description = __doc__
    input_variables = {
        "pkg_build_name": {
            "required": True,
            "description": "The name of the pkg to be built."
        },
        "pkg_dir": {
            "required": True,
            "description": "The directory where the packages are built."
        },
        "force_pkg_build": {
            "required": False,
            "description": (
                "When set, this forces returning False even if a package "
                "already exists in the output directory with the same "
                "identifier and version number. See docs for PkgCreator "
                "processor for more information. Defaults to False."),
        },
        "version": {
            "required": True,
            "description" : "The version number of the software.",
        },
        "bundleid": {
            "required": True,
            "description": (
                "The software's bundle identifier."),
        },
    }
    output_variables = {
        "pkg_build_matches": {
            "default": False,
            "description": (
                "False if no built package exists. "
                "True if a package with the same filename, identifier and "
                "version already exists and thus no package needs to be built "
                "(see 'force_pkg_build' input variable."),
        },
    }

    def xar_expand(self, source_path):
        '''Uses xar to expand an archive.'''
        # Originally from PkgCreator.py
        try:
            xarcmd = ["/usr/bin/xar",
                      "-x",
                      "-C", self.env.get('RECIPE_CACHE_DIR'),
                      "-f", source_path,
                      "PackageInfo"]
            proc = subprocess.Popen(xarcmd,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
            (_, stderr) = proc.communicate()
        except OSError as err:
            raise ProcessorError("xar execution failed with error code %d: %s"
                                 % (err.errno, err.strerror))
        if proc.returncode != 0:
            raise ProcessorError("extraction of %s with xar failed: %s"
                                 % (source_path, stderr))

    def check_for_package(self):
        """Check for an existing flat package in the output dir and compare its
        identifier and version to the one we're going to build.  Originally
        from PkgCreator.py.

        """
        pkg_build_name = self.env['pkg_build_name']
        pkg_dir = self.env['pkg_dir']
        pkg_path = os.path.join(pkg_dir, pkg_build_name + '.pkg')
        if os.path.exists(pkg_path) and not self.env.get("force_pkg_build"):
            self.output("Package already exists at path %s." % pkg_path)
            self.xar_expand(pkg_path)
            packageinfo_file = os.path.join(self.env['RECIPE_CACHE_DIR'],
                                            'PackageInfo')
            if not os.path.exists(packageinfo_file):
                raise ProcessorError(
                    "Failed to parse existing package, as no PackageInfo "
                    "file count be found in the extracted archive.")

            tree = ET.parse(packageinfo_file)
            root = tree.getroot()
            local_version = root.attrib['version']
            local_id = root.attrib['identifier']

            if (local_version == self.env['version']
                    and local_id == self.env['bundleid']):
                self.output("Existing package matches version and identifier, "
                            "not building.")
                self.env["pkg_path"] = pkg_path
                self.env['pkg_build_matches'] = True


    def main(self):
        '''Look for an already built package.'''
        self.check_for_package()


if __name__ == '__main__':
    PROCESSOR = PkgBuildTester()
    PROCESSOR.execute_shell()

