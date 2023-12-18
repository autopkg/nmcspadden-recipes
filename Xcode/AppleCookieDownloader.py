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
"""See docstring for AppleCookieDownloader class"""

import json
import os.path

from autopkglib import ProcessorError, URLGetter


__all__ = ["AppleCookieDownloader"]

class DownloadCookieError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)



class AppleCookieDownloader(URLGetter):
    """Downloads a URL to the specified download_dir using curl."""

    description = __doc__
    input_variables = {
        "login_data": {
            "description": "Path to login data file.",
            "required": True
        }
    }
    output_variables = {
        "download_cookies": {
            "description": "Path to the download cookies."
        }
    }


    def main(self):
        download_dir = os.path.join(self.env["RECIPE_CACHE_DIR"], "downloads")
        login_cookies = os.path.join(download_dir, "login_cookies")
        download_cookies = os.path.join(download_dir, "download_cookies")
        # create download_dir if needed
        if not os.path.exists(download_dir):
            try:
                os.makedirs(download_dir)
            except OSError as err:
                raise ProcessorError(
                    f"Can't create {download_dir}: {err.strerror}"
                )
        # We need to POST a request to the auth page to get the
        # 'myacinfo' cookie
        self.output("Getting login cookie")
        # Base curl options
        base_curl_opts = [
            "--request",
            "POST",
            "--silent",
            "--show-error",
            "--no-buffer",
            "--dump-header", "-",
            "--speed-time", "30"
        ]
        # Curl options to acquire login cookies
        login_curl_opts = [
            "--url",
            "https://idmsa.apple.com/IDMSWebAuth/authenticate",
            "--data",
            f"@{self.env['login_data']}",
            "--cookie-jar",
            login_cookies,
            "--output",
            "-"
        ]
        # Initialize the curl_cmd, add base curl options, and execute curl
        prepped_curl_cmd = self.prepare_curl_cmd()
        self.download_with_curl(
            prepped_curl_cmd + base_curl_opts + login_curl_opts
        )
        # Now we need to get the download cookie
        output = os.path.join(download_dir, "listDownloads.json")
        self.output("Getting download cookie")
        if os.path.exists(output):
            # Delete it first
            os.unlink(output)
        # Curl options to acquire the download list
        dl_curl_opts = [
            "--url",
            "https://developer.apple.com/services-account/QH65B2/downloadws/listDownloads.action",
            "--cookie",
            login_cookies,
            "--cookie-jar",
            download_cookies,
            "--output",
            output
        ]
        headers = {"Content-length": "0"}
        self.add_curl_headers(dl_curl_opts, headers)
        self.download_with_curl(
            prepped_curl_cmd + base_curl_opts + dl_curl_opts
        )
        self.env["download_cookies"] = download_cookies
        try:
            with open(output) as f:
                # Verify this can be successfully loaded this as JSON and that credentials were not rejected
                login_attempt = json.load(f)
                if result_string := login_attempt.get("resultString"):
                    if "your session has expired" in result_string.lower():
                        raise DownloadCookieError(login_attempt)
        except IOError as error:
            raise ProcessorError(
                "Unable to load the listDownloads.json file.") from error
        except DownloadCookieError as error:
            raise ProcessorError(error)
        except Exception as error:
            raise ProcessorError(
                f"Unknown error loading the list of downloads. Error:  {error}") from error
        self.output("Successfully acquired the download list")


if __name__ == "__main__":
    PROCESSOR = AppleCookieDownloader()
    PROCESSOR.execute_shell()
