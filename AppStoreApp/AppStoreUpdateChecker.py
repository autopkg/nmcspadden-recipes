#!/usr/bin/env python
#
# Copyright 2014 Nick McSpadden
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

import urllib2
import plistlib
import sys

from autopkglib import Processor, ProcessorError
from Foundation import NSData, NSPropertyListSerialization, NSPropertyListMutableContainers

# pyMASreceipt - python module for parsing the contents of _MASReceipt/receipt file inside a Mac App Store .app
#
# pyMASreceipt is a python module for parsing the receipt contents of a Mac App Store app (located within the application bundle: Contents/Resources/_MASReceipt/receipt).
#
# It is a best guess at contents, following the documentation provided by Apple at: http://developer.apple.com/library/mac/#releasenotes/General/ValidateAppStoreReceipt/_index.html
#
# This module depends on the module 'python-asn1' by Geert Jansen (geertj@github), available here: https://github.com/geertj/python-asn1
#
# Credits
#
# - pyMASreceipt is written by pudquick@github
# - python-asn1 is written by geertj@github
#
# License
#
# pyMASreceipt is released under a standard MIT license.
#
#   Permission is hereby granted, free of charge, to any person
#   obtaining a copy of this software and associated documentation files
#   (the "Software"), to deal in the Software without restriction,
#   including without limitation the rights to use, copy, modify, merge,
#   publish, distribute, sublicense, and/or sell copies of the Software,
#   and to permit persons to whom the Software is furnished to do so,
#   subject to the following conditions:
#
#   The above copyright notice and this permission notice shall be
#   included in all copies or substantial portions of the Software.
#
#   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
#   EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
#   MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
#   NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
#   BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
#   ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
#   CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#   SOFTWARE.

try:
    import asn1
    pymasreceipt_avail = True
except ImportError:
    pymasreceipt_avail = False
    #raise ProcessorError("asn1 not found.  Please install asn1 from https://github.com/geertj/python-asn1")
import os
from collections import namedtuple
MASattr = namedtuple('MASattr', 'type version value')

# The following attributes were determined from looking at the JSON attributes for a MAS app and the output
# of mdls /path/to/the.app and comparing values to the receipt dump:
#
# 0x01: Product ID - can be used with: http://itunes.apple.com/WebObjects/MZStore.woa/wa/viewSoftware?id=PRODUCTID&mt=8
# 0x04: Opaque Value = Unique Mac App Store compatible numeric mapping to AppleID
#                      as discovered by MagerValp here: http://magervalp.github.com/2013/03/19/poking-around-in-masreceipts.html
#                      Also used in: com.apple.storeagent
# 0x05: SHA-1 Hahsh = This is the hash that's a checksum of the machine GUID, Apple ID (Opaque Value), and the bundle ID
#                     for the application.
#                     Calculation method for the hash: https://developer.apple.com/library/ios/releasenotes/General/ValidateAppStoreReceipt/Chapters/ValidateLocally.html#//apple_ref/doc/uid/TP40010573-CH1-SW10
#                     Under the section "Listing 1-7  Compute the hash of the GUID"
# 0x08: Purchase Date
# 0x0A: Parental Content Rating
# 0x10: kMDItemAppStoreInstallerVersionID
#
# Additional material for reading: http://www.mactech.com/sites/default/files/Jalkut-Would_You_Like_a_Receipt_With_That.pdf
# Seems to indicate a few new types:
# 0x00: Receipt type
# 0x0C: LastAuthTime as seen in com.apple.storeagent (likely set at time of download?)
#
# Apple documentation:
# https://developer.apple.com/library/mac/releasenotes/General/ValidateAppStoreReceipt/Chapters/ReceiptFields.html
# 0x13: Original version number of application purchased
# 0x15: Receipt expiration date
#
# More are listed in the Apple documentation regarding In-App purchases
#
# More examples from here: https://github.com/robotmedia/RMStore/blob/master/RMStore/Optional/RMAppReceipt.m#L28
#
# InAppPurchaseReceipt = 17;            //   0x11
# Quantity = 1701;                      // 0x06A5
# ProductIdentifier = 1702;             // 0x06A6
# TransactionIdentifier = 1703;         // 0x06A7
# PurchaseDate = 1704;                  // 0x06A8
# OriginalTransactionIdentifier = 1705; // 0x06A9
# OriginalPurchaseDate = 1706;          // 0x06AA
# SubscriptionExpirationDate = 1708;    // 0x06AC
# WebOrderLineItemID = 1711;            // 0X06AF
# CancellationDate = 1712;              // 0x06B0

MAS_types = { 1: 'Product ID',
              2: 'Bundle Identifier',
              3: 'Application Version',
              4: 'Opaque Value',
              5: 'SHA-1 Hash',
              8: 'Purchase Date',
             10: 'Parental Content Rating',
             16: 'App Store Installer Version ID',
             17: 'In-App Purchase Receipt' }

def unwind(input):
    ret_val = []
    while not input.eof():
        tag = input.peek()
        if tag[1] == asn1.TypePrimitive:
            tag, value = input.read()
            ret_val.append((tag[2], tag[0], value))
        elif tag[1] == asn1.TypeConstructed:
            ret_val.append((tag[2], tag[0]))
            input.enter()
            ret_val.append(unwind(input))
            input.leave()
    return ret_val

def extract_data(asn1_seq):
    ret_val = []
    for i,x in enumerate(asn1_seq):
        if (type(x) is tuple):
            if len(x) == 3:
                if x[2] == '1.2.840.113549.1.7.1':
                    ret_val.append(asn1_seq[i+2][0][2])
        elif (type(x) is list):
            sub_val = extract_data(x)
            if (type(sub_val) is list):
                ret_val.extend(sub_val)
            else:
                ret_val.append(sub_val)
    if len(ret_val) == 1:
        return ret_val[0]
    return ret_val

def parse_receipt(rec):
    ret_val = []
    for y in [z for z in rec if type(z) is list]:
        try:
            dec = asn1.Decoder()
            dec.start(y[2][2])
            ret_val.append(MASattr(MAS_types.get(y[0][2], '0x%02X' % y[0][2]), y[1][2], unwind(dec)[0][-1]))
        except:
            ret_val.append(MASattr(MAS_types.get(y[0][2], '0x%02X' % y[0][2]), y[1][2], y[2][2]))
    return ret_val

def get_app_receipt(path_to_MAS_app):
    receipt_path = os.path.join(path_to_MAS_app, "Contents/_MASReceipt/receipt")
    dec1 = asn1.Decoder()
    dec1.start(open(receipt_path, 'rb').read())
    payload = extract_data(unwind(dec1))
    dec2 = asn1.Decoder()
    dec2.start(payload)
    return parse_receipt(unwind(dec2)[1])

#
# End of pyMASreceipt code.
#

## Code by pudquick: https://gist.github.com/pudquick/7785749
###
# This function uses the Mac App Store update checker mechanism.
# It can accept a batch collection of apps to lookup information for.
# It works best with information directly from the receipts and bundle of the application itself.
# Specifically, if it can extract the App Store installed version identifier, a response for that application
# will only be generated if the version is older than (or not found in) the newest version in the version history
# known by the App Store.
# For information on extracting this from the receipts of apps, check my project here:
# https://github.com/pudquick/pyMASreceipt/blob/master/pyMASreceipt.py
# If you pass '0' for the installed-version-identifier, you will always get a result for the app from the App Store
# update mechanism, which includes the latest installed-version-identifier (and all prior ones)

def check_app_updates(app_info_list, raw_result=False):
    # This function expects a list of dicts with, at a minimum, the 'adam-id' key set
    # This ID is the unique product identifier for an app on the App Store and can be found in the store URL
    # when viewing the app's page in a web browser, like so:
    # https://itunes.apple.com/us/app/evernote/id406056744
    #                                            ^^^^^^^^^
    # The other 3 keys that will be passed in the search are: CFBundleIdentifier, CFBundleShortVersionString, and
    # installed-version-identifier (explained earlier). Lack of any of these keys will result in a filler value
    # being provided which, as long as the adam-id is present, the App Store update mechanism doesn't seem to
    # care about.
    update_url = 'https://su.itunes.apple.com/WebObjects/MZSoftwareUpdate.woa/wa/availableSoftwareUpdatesExtended'
    request = urllib2.Request(update_url)
    # Headers #
    # This sets us to the US store. See:
    # http://blogs.oreilly.com/iphone/2008/08/scraping-appstore-reviews.html
    # http://secrets.blacktree.com/edit?id=129761
    request.add_header('X-Apple-Store-Front', '143441-1,13')
    # This indicates we're sending an XML plist
    request.add_header('Content-Type', 'application/x-apple-plist')
    # This seems to be the minimum string to be recognized as a valid app store update checker
    # Normally, it's of the form: User-Agent: MacAppStore/1.3 (Macintosh; OS X 10.9) AppleWebKit/537.71
    request.add_header('User-Agent', 'MacAppStore')
    # Build up the plist
    local_software = []
    for an_app in app_info_list:
        app_entry = {'CFBundleIdentifier': an_app.get('CFBundleIdentifier', '.'),
                     'CFBundleShortVersionString': an_app.get('CFBundleShortVersionString', '0'),
                     'adam-id': an_app['adam-id'],
                     'installed-version-identifier': an_app.get('installed-version-identifier', 0)}
        local_software.append(app_entry)
    plist_dict = {'local-software': local_software}
    plist_str = plistlib.writePlistToString(plist_dict)
    request.add_data(plist_str)
    # Build the connection
    response_handle = urllib2.urlopen(request)
    try:
        response = response_handle.read()
    except HTTPError, e:
        raise ProcessorError("Invalid adam-id %s" % e)
    response_handle.close()
    # Currently returning the raw response
    # Initial analysis:
    # - It appears that applications that need updating will be under the 'incompatible-items' key
    # - 'version-external-identifiers' is a list of historical versions, in order
    # - 'version-external-identifier' is the current version
    # - 'current-version' is the CFBundleShortVersionString
    # - 'bundle-id' is the CFBundleIdentifier
    # - 'preflight' is a *very* interesting 'pfpkg'. See details at bottom.
    return plistlib.readPlistFromString(response)

#
# End of pudquick code
#

__all__ = ["AppStoreUpdateChecker"]


class AppStoreUpdateChecker(Processor):
    description = "Check a given Mac App Store app for updates."
    input_variables = {
        "app_item": {
            "required": True,
            "description": "Path to a local Mac App Store app.",
        }
    }
    output_variables = {
        "update_available": {
            "description": ("Boolean value indicating true if an update is available from the version on disk. "
                            "Always true if only an adam-id is passed.")
        },
        "bundleid" : {
            "description": "Bundle identifier for the App Store app.",
        },
        "version": {
            "description": "Version of the App Store app.",
        }
    }

    __doc__ = description

    def read_bundle_info(self, path):
        """Read Contents/Info.plist inside a bundle."""

        plistpath = os.path.join(path, "Contents", "Info.plist")
        if not (os.path.isfile(plistpath)):
			raise ProcessorError("File does not exist: %s" % plistpath)
        info, format, error = \
            NSPropertyListSerialization.propertyListFromData_mutabilityOption_format_errorDescription_(
                NSData.dataWithContentsOfFile_(plistpath),
                NSPropertyListMutableContainers,
                None,
                None
            )
        if error:
            raise ProcessorError("Can't read %s: %s" % (plistpath, error))

        return info

    def main(self):
        # Assign variables
        app_item = self.env.get("app_item")

        app_details = []
        app_dict = {}
        details = {}

        # Assumption: all App Store app paths will contain ".app" in the name.  Probably a safe one.
        if ".app" in app_item:
            #if pyMASreceipt is unavailable due to the lack of third party modules, we'll just assume it's up to date:
            if not pymasreceipt_avail:
                self.env["update_available"] = False
                # we need to get the version by actually looking at the app
                info = self.read_bundle_info(app_item)
                self.env["bundleid"] = info["CFBundleIdentifier"]
                self.env["version"] = info["CFBundleShortVersionString"]
                return
            try:
                decoded_receipt = get_app_receipt(app_item)
            except IOError, e:
                raise ProcessorError("Invalid path %s: %s" % (app_item, e))
            details = { t.type: t.value for t in decoded_receipt }
            app_dict['CFBundleIdentifier'] = details['Bundle Identifier']
            app_dict['installed-version-identifier'] = int(details['App Store Installer Version ID'])
            app_dict['adam-id'] = details['Product ID']
        else:
            # We got bad data
            raise ProcessorError("Invalid app_item: %s" % app_item)

        app_details.append(app_dict)
        try:
            item_details = check_app_updates(app_details)
        except urllib2.HTTPError, e:
            raise ProcessorError("Invalid adam-id %s: %s" % (app_item, e))
        # If item_details contains a key 'incompatible-items', it means the version we have is not up to date.
        # So now we can check for the presence of 'incompatible-items' and then report that there's an update available with a specific version
        # If that key isn't there, then the app is up to date.

        if 'incompatible-items' in item_details:
            self.env["version"] = item_details['incompatible-items'][0]['current-version']
            self.env["update_available"] = True
            self.output("App store version: %s" % item_details['incompatible-items'][0]['current-version'])
            self.output("Our version: %s" % details['Application Version'])
        else:
            #no update available, we're up to date
            self.env["version"] = str(details['Application Version'])
            self.env["update_available"] = False
            self.output("%s is up to date: %s" % (self.env.get("app_item"), details['Application Version']))
        self.env["bundleid"] = details['Bundle Identifier']
        # end

if __name__ == '__main__':
    processor = AppStoreUpdateChecker()
    processor.execute_shell()

