#!/usr/bin/python
#
# Copyright 2015 Nick McSpadden
# Reworked code from PlistReader.py, originally by Shea Craig
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
"""See docstring for UserPlistReader class"""

from __future__ import absolute_import

import os.path

import FoundationPlist
from autopkglib import Processor, ProcessorError

__all__ = ["UserPlistReader"]


class UserPlistReader(Processor):
    """Extracts values from top-level keys in a plist file, and assigns to
    arbitrary output variables. This is intended to be used on account plist
    files, which have a specific structure inside."""

    description = __doc__
    input_variables = {
        "info_path": {
            "required": True,
            "description": (
                "Path to a user account plist to be read. "),
        },
        "plist_keys": {
            "required": False,
            "default": {'name': 'username'},
            "description": ("Dictionary of plist values to query. Key names "
                            "should match a top-level key to read. Values "
                            "should be the desired output variable name. "
                            "Defaults to: ",
                            "{'name': 'username'}")
        },
    }
    output_variables = {
        "plist_reader_output_variables": {
            "description": (
                "Output variables per 'plist_keys' supplied as "
                "input. Note that this output variable is used as both a "
                "placeholder for documentation and for auditing purposes. "
                "One should use the actual named output variables as given "
                "as values to 'plist_keys' to refer to the output of this "
                "processor.")
        },
    }


    def main(self):
        keys = self.env.get('plist_keys')
        
        # Many types of paths are accepted. Figure out which kind we have.
        path = os.path.normpath(self.env['info_path'])
        
        # Check whether this is at least a valid path
        if not os.path.exists(path):
            raise ProcessorError("Path '%s' doesn't exist!" % path)

        # Does it have a 'plist' extension
        # (naively assuming 'plist' only names, for now)
        if not path.endswith('.plist'):
            # Full path to a plist was supplied, move on.
            raise ProcessorError("File '%s' is not a plist!" % path)

        # Try to read the plist
        self.output("Reading: %s" % path)
        try:
            info = FoundationPlist.readPlist(path)
        except (FoundationPlist.NSPropertyListSerializationException,
                UnicodeEncodeError) as err:
            raise ProcessorError(err)

        # Copy each plist_keys' values and assign to new env variables
        self.env["plist_reader_output_variables"] = {}
        for key, val in keys.items():
            try:
                # The unique aspect of user account plists is that each 
                # key at the root is an array that contains exactly one item.
                # So to get the actual meat, we need to access the first
                # item of the array
                self.env[val] = info[key][0]
                self.output(
                    "Assigning value of '%s' to output variable '%s'"
                    % (self.env[val], val))
                # This one is for documentation/recordkeeping
                self.env["plist_reader_output_variables"][val] = (
                    self.env[val])
            except KeyError:
                raise ProcessorError(
                    "Key '%s' could not be found in the plist %s!"
                    % (key, path))


if __name__ == '__main__':
    PROCESSOR = UserPlistReader()
    PROCESSOR.execute_shell()
