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
"""See docstring for AppleDataGatherer class"""


# Disabling warnings for env members and imports that only affect recipe-
# specific processors.
# pylint: disable=e1101,f0401

import os

from urllib.parse import quote

from autopkglib import Processor, ProcessorError


__all__ = ["AppleDataGatherer"]


class AppleDataGatherer(Processor):
    """Gather Xcode-specific curl data payloads into a file on disk."""

    description = __doc__
    input_variables = {
        "apple_id": {
            "description": "AppleID that can log into the Apple dev portal.",
            "required": True
        },
        "password": {
            "description": (
                "Password for AppleID that can log into Apple dev portal."
            ),
            "required": False
        },
        "password_file": {
            "description": (
                "A path to a file to read the password from. Using "
                "this will ignore the 'password' argument."
            ),
            "required": False
        },
        "appID_key": {
            "description": "App ID key to log into.",
            "required": True
        }
    }
    output_variables = {
        "data_pathname": {
            "description": "Path to the data file."
        }
    }


    def main(self):
        """Store the login data file."""
        if not self.env.get("password") and not self.env.get("password_file"):
            raise ProcessorError(
                "You must provide either a password, or a password_file argument."
            )
        password = self.env.get("password")
        if self.env.get("password_file"):
            with open(self.env["password_file"]) as f:
                password = f.read()

        appleIDstring = f"appleId={quote(self.env['apple_id'])}&"
        appIDKeystring = f"appIdKey={self.env['appID_key']}&"
        passwordstring = f"accountPassword={password}"

        login_data = appleIDstring + appIDKeystring + passwordstring
        download_dir = os.path.join(self.env["RECIPE_CACHE_DIR"], "downloads")
        filename = "login_data"
        # create download_dir if needed
        if not os.path.exists(download_dir):
            try:
                os.makedirs(download_dir)
            except OSError as err:
                raise ProcessorError(
                    f"Can't create {download_dir}: {err.strerror}"
                )
        self.output("Writing data to file")
        self.env["data_pathname"] = os.path.join(download_dir, filename)
        with open(self.env["data_pathname"], "w") as f:
            f.write(login_data)


if __name__ == "__main__":
    PROCESSOR = AppleDataGatherer()
    PROCESSOR.execute_shell()
