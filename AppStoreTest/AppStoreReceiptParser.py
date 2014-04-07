#!/usr/bin/env python
#
# Copyright 2014 Nick McSpadden
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

import urllib2
import plistlib
import sys

from autopkglib import Processor, ProcessorError

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
# 	Permission is hereby granted, free of charge, to any person
# 	obtaining a copy of this software and associated documentation files
# 	(the "Software"), to deal in the Software without restriction,
# 	including without limitation the rights to use, copy, modify, merge,
# 	publish, distribute, sublicense, and/or sell copies of the Software,
# 	and to permit persons to whom the Software is furnished to do so,
# 	subject to the following conditions:
# 
# 	The above copyright notice and this permission notice shall be
# 	included in all copies or substantial portions of the Software.
# 
# 	THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# 	EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# 	MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# 	NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# 	BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# 	ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# 	CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# 	SOFTWARE.

try:
	import asn1
except ImportError:
	raise ProcessorError("asn1 not found.  Please install asn1 from https://github.com/geertj/python-asn1")
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

__all__ = ["AppStoreReceiptParser"]


class AppStoreReceiptParser(Processor):
	description = "Check a given Mac App Store app for updates."
	input_variables = {
		"path": {
			"required": True,
			"description": "Path to a Mac App Store app.",
		}
	}
	output_variables = {
		"bundleid": {
			"description": "Bundleid for the App Store app.",
		},
		"version": {
			"description": "Version of the App Store app.",
		},
		"appname": {
			"description": "Name of the App Store app (without path).",
		}
	}
	
	__doc__ = description

	def main(self):
		# Assign variables
		path = self.env.get("path")	
		try:
	#		decoded_receipt = pyMASreceipt.get_app_receipt(path)
			decoded_receipt = get_app_receipt(path)
		except IOError, e:
			raise ProcessorError("Invalid app_path %s: %s" % (app_path, e))
		details = { t.type: t.value for t in decoded_receipt }
		self.env["bundleid"] = details['Bundle Identifier'] + '.pkg'
		self.env["version"] = details['Application Version']
		self.env["appname"] = os.path.basename(path.rstrip(os.sep).rstrip(".app"))
		
# TO DO:
# 1. Provide an unescaped path for use in recipes
# 2. Some kind of logic to make sure we don't repackage things that are already packaged
# 3. Leave a receipt plist behind in the cache to indicate last packaged version
# 4. If last packaged version is older than current packaged version, repackage

if __name__ == '__main__':
	processor = AppStoreReceiptParser()
	processor.execute_shell()
	
