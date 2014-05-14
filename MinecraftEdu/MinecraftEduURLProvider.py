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

from autopkglib import Processor, ProcessorError
from operator import itemgetter
import urllib2

__all__ = ["MinecraftEduURLProvider"]


VERSION_LIST_URL = ("http://www.minecraftedu.com/api/api.php?action=b_getversions&eduversiontype=2")

DOWNLOAD_URL = ("http://minecraftedu.com/api/api.php?action=b_downloadversion&username=%s&password=%s&hashed=%s&versiontodownload=%s&build=%s&eduversiontype=2&releasetype=%s")

TYPE_DEFAULT = "stable"
HASHED_DEFAULT = "true"

class MinecraftEduURLProvider(Processor):
	description = "Provides URL to the latest MinecraftEdu release."
	input_variables = {
		"type": {
			"required": False,
			"description": ("Which branch to use.  Choose development or "
							"stable.  Defaults to %s." % TYPE_DEFAULT)
		},
		"hashed": {
			"required": False,
			"description": ("Password is hashed: true or false. Defaults"
							"to %s." % HASHED_DEFAULT)
		},
		"username": {
			"required": True,
			"description": ("Username for MinecraftEdu site.")
		},
		"password": {
			"required": True,
			"description": ("Password for MinecraftEdu site.  Can be cleartext or "
							"hashed.  Use http://minecraftedu.com/api/api.php?action=gethash&username=username&password=password"
							"to generate hashed password.")
		}
	}
	output_variables = {
		"url": {
			"description": "URL to the latest MinecraftEdu release.",
		},
		"version": {
			"description": "Version in the form of: download.build (i.e. 1.64.6).",
		}
	}
	
	__doc__ = description
	
	def get_mcedu_url(self, dl_type, hashed, username, password):
		request = urllib2.Request(VERSION_LIST_URL)
		request.add_header("x-requested-with", "XMLHttpRequest")
		try:
			url_handle = urllib2.urlopen(request)
			version_output = url_handle.read()
			url_handle.close()
		except BaseException as e:
			raise ProcessorError("Can't open %s: %s" % (base_url, e))
		stable_releases = filter(lambda x: dl_type in x,version_output.split("<version>"))
		version_numbers = []
		build_length = int(len(dl_type)) + 1 #length of 'stable' or 'development' + 1 for the '|'
		for item in stable_releases:
			version_numbers.append(item[:-build_length].split("_"))
		#version_numbers.sort(key = itemgetter(1))
		float_version_numbers = list()
		# Now convert all the strings to floats, so we can sort them
		for version in version_numbers:
			float_version_numbers.append([float(x) for x in version])
		float_version_numbers.sort(reverse=True)
		# version_numbers[0][0] = latest stable version
		# version_numbers[0][1] = latest stable build
		separator = "."
		self.env["version"] = separator.join(string(float_version_numbers[0]))
		return DOWNLOAD_URL % (username, password, hashed, float_version_numbers[0][0], float_version_numbers[0][1], dl_type)
   
	def main(self):
		# Determine type, hashed, username and password.
		dl_type = self.env.get("type", TYPE_DEFAULT)
		username = self.env.get("username")
		password = self.env.get("password")
		hashed = self.env.get("hashed", HASHED_DEFAULT)
		
		self.env["url"] = self.get_mcedu_url(
			dl_type, hashed, username, password)
		self.output("Found URL %s" % self.env["url"])
	

if __name__ == "__main__":
	processor = MinecraftEduURLProvider()
	processor.execute_shell()
	
