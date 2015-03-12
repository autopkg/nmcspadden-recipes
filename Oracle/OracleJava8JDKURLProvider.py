#!/usr/bin/env python
#
# Copyright 2013 Greg Neagle, Jeremy Reichman
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

import re
import urllib2
import urlparse
import os

from autopkglib import Processor, ProcessorError


__all__ = ["OracleJava8JDKURLProvider"]

# URL to find the Java 8 JDK download
BASE_URL = "".join([
    'http://www.oracle.com/technetwork/java/javase/downloads',
    '/jdk8-downloads-2133151.html',
])

# URL to find the Java 8 JDK download cookie
cookie_source_url = "".join([
    'http://stackoverflow.com/questions/10268583/how-to-automate-',
    'download-and-instalation-of-java-jdk-on-linux',
])

# ['jdk-8u40-macosx-x64.dmg'] = { "title":"Mac OS X x64", "size":"221.89 MB",
# "filepath":"http://download.oracle.com/otn-pub/java/jdk/8u40-b25/jdk-8u40-macosx-x64.dmg"};
jre_download_link = re.compile(
    r'\"filepath\":\"(?P<url>http://download.oracle.com/otn-pub/java/jdk'
    r'/8u\d+-\w+/jdk-8u\d+-macosx-x64.dmg)\"'
)


class OracleJava8JDKURLProvider(Processor):
    """Provides a download URL for the latest Oracle Java 8 JRE release."""
    input_variables = {
        "base_url": {
            "required": False,
            "description": "Default is %s" % BASE_URL,
        },
    }
    output_variables = {
        "url": {
            "description": "URL to the latest Oracle Java 8 JDK release.",
        },
        "request_headers": {
            "description": "Additional headers for the Oralce Java 8 JDK download.",
        },
    }
    description = __doc__

    def get_java_download_cookie(self, cookie_source_url):
        """"Find a string representing the cookie that allows for the Java 8 JDK
        download to proceed."""

        # Create a regular expression object to match the working cookie string
        # The "cookie" named group within the pattern is the string of interest
        download_cookie_string = re.compile(
            r'--header \"Cookie: '
            r'(?P<cookie>g.+\.com)\"'
        )

        # Request the URL that shows a working cookie string
        # and read the resulting HTML page
        try:
            opener = urllib2.build_opener()
            f = opener.open(cookie_source_url)
            html = f.read()
            f.close()
        except BaseException as err:
            raise ProcessorError("Can't download %s: %s" % (cookie_source_url, err))

        # Search the HTML for the cookie string regular expression
        m = download_cookie_string.search(html)

        # If nothing matches the regular expression, raise an exception
        # Otherwise, find get the named group "cookie" from the regular expression
        # match and return that
        if not m:
            raise ProcessorError(
                "Couldn't find cookie string in %s" % cookie_source_url)
        download_cookie = m.group("cookie")
        return download_cookie

    def get_java_dmg_url(self, base_url):
        """Finds a download URL for latest Oracle Java 8 JDK release."""

        # Read HTML from base URL
        try:
            opener = urllib2.build_opener()
            f = opener.open(base_url)
            html = f.read()
            f.close()
        except BaseException as err:
            raise ProcessorError("Can't download %s: %s" % (base_url, err))

        # Search for JDK downloads link in the HTML
        m = jre_download_link.search(html)

        # If nothing matches the regular expression, raise an exception
        # Otherwise, find get the named group "url" from the regular expression
        # match and return that
        if not m:
            raise ProcessorError(
                "Couldn't find JRE download link in %s" % base_url)
        download_url = m.group("url")
        return download_url

    def get_java_download_version(self, download_url):
        """Output the version string for the Java 8 JDK download."""

        # Split the URL, get the dirname
        url_split = urlparse.urlsplit(download_url)
        url_split_path = url_split.path
        download_dirname = os.path.dirname(url_split_path)

        # Find the version string in the last dirname component
        download_dir_version = os.path.basename(download_dirname)
        # Split on the non-numeric bits
        download_dir_version_split = re.split('\D+', download_dir_version)
        # Insert 1
        download_dir_version_split.insert(0, "1")
        # Reassemble by joining with periods
        download_version = ".".join(download_dir_version_split)
        return download_version

    def main(self):
        """Find and return a download URL along with needed request headers."""

        # Find the cookie string needed for the download
        download_cookie = self.get_java_download_cookie(cookie_source_url)

        # Add the cookie string the the request headers that will be passed to the
        # next step in the Processor for use during the actual JDK file download
        self.env["request_headers"] = {'Cookie': download_cookie}

        # Get the base URL and then use it it find the file download URL
        base_url = self.env.get("base_url", BASE_URL)
        download_url = self.get_java_dmg_url(base_url)
        self.env["url"] = download_url
        self.output("Found URL %s" % self.env["url"])

        # Get the string representing the requested DeployStudio version
        download_version = self.get_java_download_version(download_url)
        self.env["version"] = download_version
        self.output("Found version %s" % self.env["version"])


if __name__ == "__main__":
    processor = OracleJava8JDKURLProvider()
    processor.execute_shell()
