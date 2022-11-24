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
"""Get all Version information from Xcode."""

from os.path import basename, expandvars, splitext

from urllib.parse import urlsplit

from autopkglib import Processor


__all__ = ["XcodeVersionEmitter"]


class XcodeVersionEmitter(Processor):
    """Output a version number based on the URL. Skipped by default."""

    description = __doc__
    input_variables = {
        "dont_skip": {
            "description": (
                "If this evaluates as truthy, do not skip this step."
            ),
            "default": False,
            "required": False
        },
        "url": {
            "description": "URL to parse the version from.",
            "required": True
        },
        "output_filepath": {
            "description": "Path to which xcode version tag is emitted.",
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
        url = self.env["url"]
        url_split_object = urlsplit(url)
        # "https://download.developer.apple.com/Developer_Tools/Xcode_10.2.1/Xcode_10.2.1.xip"  # noqa
        # "https://developer.apple.com//services-account/download?path=/Developer_Tools/Xcode_11_Beta_2/Xcode_11_Beta_2.xip"  # noqa
        filename = splitext(basename(url_split_object.path))[0].lower()
        self.output(f"Derived filename: {filename}")
        self.env["derived_filename"] = filename

        destination = expandvars(self.env["output_filepath"])
        with open(destination, "w") as f:
            f.write(filename)
        self.output(
            f"Derived filename ({filename}) written to disk at {destination}")


if __name__ == "__main__":
    PROCESSOR = XcodeVersionEmitter()
    PROCESSOR.execute_shell()
