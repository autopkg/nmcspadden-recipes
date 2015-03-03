#!/usr/bin/env/python
#
# Copyright 2015 Nick McSpadden
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from autopkglib import Processor, ProcessorError
import urllib2

__all__ = ["ChefClientVersionProvider"]


DOWNLOAD_URL = ("http://www.chef.io/chef/metadata?p=mac_os_x&pv=%s&m=x86_64")

OS_DEFAULT = "10.10"

class ChefClientVersionProvider(Processor):
    description = "Provides the version of the latest Chef client download."
    input_variables = {
        "os_version": {
            "required": True,
            "description": ("Which OS to use.  Choose development or "
                            "stable.  Defaults to %s." % OS_DEFAULT)
        }
    }
    output_variables = {
        "md5": {
            "description": "MD5 hash of latest Chef client release.",
        },
        "version": {
            "description": "Version in the form of: download.build (i.e. 1.64.6).",
        },
        "sha256": {
            "description": "SHA256 hash of latest Chef client release.",
        },
        "url": {
            "description": "URL of latest Chef client release.",
        }
    }

    __doc__ = description

    def main(self):
        # Determine type, hashed, username and password.
        os_version = self.env.get("os_version", OS_DEFAULT)

        request = urllib2.Request(DOWNLOAD_URL % os_version)
        request.add_header("x-requested-with", "XMLHttpRequest")
        try:
            url_handle = urllib2.urlopen(request)
            version_output = url_handle.read()
            url_handle.close()
        except BaseException as e:
            raise ProcessorError("Can't open %s: %s" % (base_url, e))
        results = [item.split("\t") for item in version_output.rstrip().split("\n")]
        self.env["url"] = results[0][1]
        self.env["md5"] = results[1][1]
        self.env["sha256"] = results[2][1]
    
        # I'm sorry for this, I know it hurts
        self.env["version"] = self.env["url"].rsplit('/')[-1].rsplit('-1.dmg', 1)[0].lstrip('chef-')

        self.output("Found version %s" % self.env["version"])


if __name__ == "__main__":
    processor = ChefClientVersionProvider()
    processor.execute_shell()
