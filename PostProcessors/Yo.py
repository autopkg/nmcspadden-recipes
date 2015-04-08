#!/usr/bin/env/python
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

from autopkglib import Processor, ProcessorError

import subprocess
import os.path

__all__ = ["Yo"]

class Yo(Processor):
    description = "Provides a Yo notification if anything was imported."
    input_variables = {
        "munki_info": {
            "required": False,
            "description": ("Munki info dictionary to use to display info.")
        },
        "munki_repo_changed": {
            "required": False,
            "description": ("Whether or not item was imported.")
        },
        "yo_path": {
            "required": False,
            "description": ("Path to yo.app. Defaults to /Applications "
                            "/Utilities/yo.app.")
        }
    }
    output_variables = {
    }
    
    __doc__ = description
   
    def main(self):
        # Determine type, hashed, username and password.
        was_imported = self.env.get("munki_repo_changed")
        munkiInfo = self.env.get("munki_info")
        yo_path = self.env.get("yo_path") or "/Applications/Utilities/yo.app"
        yo = os.path.join(yo_path, 'Contents/MacOS/yo')
        if was_imported:
            subtext = "%s was imported" % munkiInfo["name"]
            cmd = [yo, "-t", "Autopkg", "-s", subtext ]
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            (cmd_out, cmd_err) = proc.communicate()


if __name__ == "__main__":
    processor = Yo()
    processor.execute_shell()
    
