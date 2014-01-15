#!/usr/bin/env/python
#
# Copyright 2013 Nick McSpadden
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#	  http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from autopkglib.URLDownloader import URLDownloader

__all__ = ["MinecraftEduDownloader"]


class MinecraftEduDownloader(Processor):
	description = "Functionally identical to URLDownloader, but verifies that the download didn't return FILE_NOT_FOUND."
	
	__doc__ = description
	
   
	def main(self):
		 self.output("Downloaded %s" % pathname)
	

if __name__ == "__main__":
	processor = MinecraftEduDownloader()
	processor.execute_shell()
	
