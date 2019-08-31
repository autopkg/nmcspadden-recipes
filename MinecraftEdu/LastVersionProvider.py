#!/usr/bin/env python
#
# Copyright 2014 Nick McSpadden
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

from __future__ import absolute_import
import os
import FoundationPlist

from autopkglib import Processor, ProcessorError

__all__ = ["LastVersionProvider"]


class LastVersionProvider(Processor):
    description = "Check the current recipe's Cache folder for receipts and return the version of the last app imported."
    input_variables = {
    }
    output_variables = {
        "last_version": {
            "description": "Version of the most recently packaged version. If none found, defaults to 0.0."
        }
    }
    
    __doc__ = description

    def main(self):
        # Assign variables
		receipts_path = os.path.join(self.env['RECIPE_CACHE_DIR'],'receipts')
		if not os.path.isdir(receipts_path):
			self.output("No receipts directory found.")
			self.env['last_version'] = '0.0'
			return
		files = sorted([f for f in os.listdir(receipts_path)])
		if not files:
			self.output("No receipts found.")
			self.env['last_version'] = '0.0'
			return
		path = os.path.join(self.env['RECIPE_CACHE_DIR'],'receipts',files[-1])

		# Try to read the plist
		self.output("Reading: %s" % path)
		try:
			info = FoundationPlist.readPlist(path)
		except (FoundationPlist.NSPropertyListSerializationException,
				UnicodeEncodeError) as err:
			raise ProcessorError(err)
		self.env['last_version'] = info[1]['Output']['version']
		self.output('Version found in receipts: %s' % self.env['version'])
        # end

if __name__ == '__main__':
    processor = LastVersionProvider()
    processor.execute_shell()
    
