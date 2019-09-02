#!/usr/bin/python
#
# Copyright 2015 Nick McSpadden
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
"""See docstring for PackageInfoReader class"""

from __future__ import absolute_import

import os.path
import xml.etree.ElementTree as ET

from autopkglib import Processor, ProcessorError

__all__ = ["PackageInfoReader"]


class PackageInfoReader(Processor):
    """Extracts attributes from a PackageInfo file extracted from a flat package."""

    description = __doc__
    input_variables = {
        "info_path": {
            "required": True,
            "description": (
                "Path to a PackageInfo file to be read. "),
        },
    }
    output_variables = {
        "packageinfo_reader_output_variables": {
            "description": (
                "Output variables per packageinfo attributes. "
                "Note that this output variable is used as both a "
                "placeholder for documentation and for auditing purposes. "
                "One should use the actual named output variables as values "
                "to refer to the output of this processor.")
        },
    }


    def main(self):
        path = self.env["info_path"]
        # Check whether this is at least a valid path
        if not os.path.exists(path):
            raise ProcessorError("Path '%s' doesn't exist!" % path)

        # Try to read the PackageInfo file
        self.output("Reading: %s" % path)
        try:
            tree = ET.parse(path)
            info = tree.getroot()
        except Error as err:
            raise ProcessorError(err)

        # Copy each PackageInfo's key's value and assign to new env variables
        self.env["packageinfo_reader_output_variables"] = {}
        for key in info.attrib:
            self.env["packageinfo_" + str(key)] = info.attrib.get(key)
            self.output(
                "Assigning value of '%s' to output variable '%s'"
                % (self.env["packageinfo_" + str(key)], info.attrib.get(key)))
            # This one is for documentation/recordkeeping
            self.env["packageinfo_reader_output_variables"]["packageinfo_" + str(key)] = (
                self.env["packageinfo_" + str(key)])



if __name__ == '__main__':
    PROCESSOR = PackageInfoReader()
    PROCESSOR.execute_shell()
