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

#I would just like to state, for the record, I am fully aware of how awful this script is.
#I will eventually fix it to make it much more robust, but it's more of a "get-it-done" kind of solution.

import subprocess
from autopkglib import Processor, ProcessorError

__all__ = ["LZMADecompress"]

class LZMADecompress(Processor):
	description = "Decompresses an LZMA file using xz, a precompiled binary for OS X 10.5+."
	input_variables = {
		"lzma_file": {
			"required": True,
			"description": ("Path to .lzma file."),
		},
		"decompressor": {
			"required": True,
			"description": ("Path to xz binary."),
		}
	}
	output_variables = {
	}

	__doc__ = description

	def decompress_the_file(self):
		file = self.env.get("lzma_file")
		if not file:
			raise ProcessorError("lzma_file not found: %s" % (file))
		xz = self.env.get("decompressor")
		if not xz:
			raise ProcessorError("xz binary not found: %s" % (xz))
		cmd = [xz,'-k','--format=lzma','--decompress',file]
		proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		(output, errors) = proc.communicate()
		return errors      

	def main(self):
		'''Does nothing except decompresses the file'''
		if "lzma_file" in self.env:
			self.output("Using input LZMA file %s decompressing with %s" % (self.env["lzma_file"], self.env["decompressor"]))
		self.env["results"] = self.decompress_the_file()
		self.output("Decompressed: %s" % self.env["results"])


if __name__ == '__main__':
    processor = LZMADecompress()
    processor.execute_shell()
    

