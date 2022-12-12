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
"""See docstring for AppleURLSearcher class"""

import datetime
import json
import os
import posixpath
import re

from urllib.parse import urlsplit

from autopkglib import ProcessorError, URLGetter


__all__ = ["AppleURLSearcher"]


class AppleURLSearcher(URLGetter):
    """Search the various Apple URLs for a matching Xcode."""

    description = __doc__
    input_variables = {
        "result_output_var_name": {
            "description": (
                "The name of the output variable that is returned "
                "by the match. If not specified then a default of "
                "'match' will be used."
            ),
            "default": "match",
            "required": False
        },
        "re_pattern": {
            "description": (
                "Regex to match URLs against. To match specific Xcodes, you "
                "would need to know the URL from the Apple dev portal. "
                "If BETA is set in the environment, only search Betas for "
                "matches (i.e. isReleased is false)."
            ),
            "required": True
        }
    }
    output_variables = {
        "result_output_var_name": {
            "description": (
                "First matched sub-pattern from input found on the fetched "
                "URL. Note the actual name of variable depends on the input "
                "variable 'result_output_var_name' or is assigned a default "
                "of 'match.'"
            )
        },
        "beta_version": {
            "description": (
                "If this is a Beta version of Xcode, this will contain the "
                "'beta X' string. For Release Candidates, it will be 'RC X'."
                " For non-betas, this will be an empty string."
            )
        },
        "beta_version_underscores": {
            "description": (
                "Same as beta_version, but with underscores instead of spaces."
            )
        }
    }


    def generate_beta_name(self, beta_string, xcode_item, underscores=False):
        """Generate a string for beta or RC version"""
        beta_number = xcode_item["displayName"].split(" ")[-1]
        if beta_number and underscores:
            return f"{beta_string}_{beta_number}"
        elif beta_number:
            return f"{beta_string} {beta_number}"
        return ""


    # xcode_item is a Dict defined in main()
    def parse_beta_info(self, xcode_item):
        """Parse download url to set beta environment variables"""
        self.env["is_beta"] = bool(self.env.get("BETA"))
        self.env["beta_version"] = ""
        if not self.env.get("BETA"):    
            return
        if "beta" in xcode_item["displayName"].lower():
            self.env["beta_version"] = self.generate_beta_name("beta", xcode_item)
        elif "release candidate" in xcode_item["displayName"].lower():
            self.env["beta_version"] = self.generate_beta_name("RC", xcode_item)
            self.env["beta_version_underscores"] = self.generate_beta_name("RC", xcode_item, underscores=True)
        self.output(f"Generated beta version string: {self.env['beta_version']}")


    def output_result(self, url):
        """Output the desired result."""
        # The final entry is the highest one
        self.output(f"Full URL: {url}")
        self.env[self.env["result_output_var_name"]] = url
        self.output_variables = {self.env["result_output_var_name"]: url, self.env["beta_version"]: self.env["beta_version"]}


    def main(self):
        # If we have "URL" already passed in, we should just use it
        if self.env.get("URL"):
            self.output_result(self.env["URL"])
            self.parse_beta_info(self.env["URL"])
            return

        # Search the Apple downloads list
        download_dir = os.path.join(self.env["RECIPE_CACHE_DIR"], "downloads")
        downloads = os.path.join(download_dir, "listDownloads.json")
        if not os.path.exists(downloads):
            raise ProcessorError(
                "Missing the download data from AppleCookieDownloader"
            )
        pattern = self.env["re_pattern"]
        with open(downloads) as f:
            data = json.load(f)
        dl_base_url = "https://download.developer.apple.com"
        xcode_list = []
        # data["downloads"] is the top-level list
        for x in data["downloads"]:
            for y in x["files"]:
                # are we looking for Betas only? If so, limit our search to
                # the "isReleased = false" entries.
                # If we are not looking for betas, ignore anything for which
                # isReleased is false
                if self.env.get("BETA"):
                    if x["isReleased"]:
                        continue
                else:
                    if not x["isReleased"]:
                        continue
                # Regex the results
                url = dl_base_url + y["remotePath"]
                re_pattern = re.compile(pattern)
                dl_match = re_pattern.findall(url)
                if not dl_match:
                    continue
                xcode_item = {
                    "datePublished_str": x["datePublished"],
                    "datePublished_obj": datetime.datetime.strptime(
                        x["datePublished"], "%m/%d/%y %H:%M"
                    ),
                    "remotePath": y["remotePath"],
                    "filename": y["filename"],
                    "displayName": y["displayName"],
                    "full_url": url,
                }
                xcode_list.append(xcode_item)
        matches = sorted(xcode_list, key=lambda i: i["datePublished_obj"])
        match = matches[-1]
        if not match or not xcode_list:
            raise ProcessorError("No match found!")
        self.output(
            f"Sorted list of possible filenames: {[x['filename'] for x in matches]}",
            verbose_level=2
        )
        self.output(f"Found matching item: {match['filename']}")
        if not (full_url_match := match["full_url"]):
            raise ProcessorError("No matching URL found!")
        self.parse_beta_info(match)
        self.output_result(full_url_match)


if __name__ == "__main__":
    PROCESSOR = AppleURLSearcher()
    PROCESSOR.execute_shell()
