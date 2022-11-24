#!/usr/local/autopkg/python
#
# Copyright (c) Facebook, Inc. and its affiliates.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
""" Emit Xcode Build Number to disk """

import os.path

from autopkglib import Processor


__all__ = ["XcodeBuildNumberEmitter"]


class XcodeBuildNumberEmitter(Processor):
    """Emit file containing Xcode Build Number"""

    description = __doc__
    input_variables = {
        "dont_skip": {
            "description": (
                "If this evaluates as truthy, do not skip this step."
            ),
            "default": False,
            "required": False
        },
        "build_version": {
            "description": "The build version number for this Xcode Release",
            "required": True
        },
        "output_filepath": {
            "description": "Path to which xcode build number is emitted.",
            "required": True
        }
    }
    output_variables = {
        "derived_filename": {
            "description": "The derived filename to emit."
        }
    }


    def main(self):
        """Main."""
        if not self.env["dont_skip"]:
            self.output("dont_skip is false, so skipping this Processor.")
            return

        build_number = self.env["build_version"]
        destination = os.path.expandvars(self.env["output_filepath"])

        with open(destination, "w") as f:
            f.write(build_number)
        self.output(
            f"Xcode build number ({build_number}) written to disk at {destination}"
        )


if __name__ == "__main__":
    PROCESSOR = XcodeBuildNumberEmitter()
    PROCESSOR.execute_shell()
