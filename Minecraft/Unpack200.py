#!/usr/bin/env python
#
# Copyright 2013 Nick McSpadden
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

# I would just like to state, for the record, I am fully aware of how awful this script is.
# I will eventually fix it to make it much more robust, but it's more of a "get-it-done" kind of solution.

from __future__ import absolute_import
import subprocess
from autopkglib import Processor, ProcessorError

__all__ = ["Unpack200"]

class Unpack200(Processor):
	description = "Unpacks a Java .pack file."
	input_variables = {
		"file_path": {
			"required": True,
			"description": ("Path to .pack file."),
		},
		"destination": {
			"required": True,
			"description": ("Location to unpack the file."),
		}
	}
	output_variables = {
	}

	__doc__ = description

	def unpack_the_file(self):
		file = self.env.get("file_path")
		if not file:
			raise ProcessorError("file_path not found: %s" % (file))
		destination = self.env.get("destination")
		if not destination:
			raise ProcessorError("destination not found: %s" % (destination))
		cmd = ['/usr/bin/unpack200',file,destination]
		proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		(output, errors) = proc.communicate()
		return output      

	def main(self):
		'''Does nothing except decompresses the file'''
		if "file_path" in self.env:
			self.output("Using input .pack file %s to extract to %s" % (self.env["file_path"], self.env["destination"]))
		self.env["results"] = self.unpack_the_file()
		self.output("Unpacked: %s" % self.env["results"])


if __name__ == '__main__':
    processor = Unpack200()
    processor.execute_shell()
    

