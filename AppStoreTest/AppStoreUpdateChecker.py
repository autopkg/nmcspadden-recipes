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


import os
import subprocess
import shutil

try:
	import asn1
except ImportError:
	print "No asn1!"

try:
	import pyMASreceipt
except ImportError:
	print "No pyMASreceipt!"

from autopkglib import Processor, ProcessorError


__all__ = ["AppStoreUpdateChecker"]


class AppStoreUpdateChecker(Processor):
	description = "Check a given Mac App Store app for updates."
	input_variables = {
		"adam_id": {
			"required": False,
			"description": "The identifier for a Mac App Store app as found in the store URL.  Recipe will fail if neither is specified."
		},
		"app_path": {
			"required": False,
			"description": "Path to an App Store app on the local machine that is being checked. Recipe will fail if neither is specified."
		}
	}
	output_variables = {
		"update_available": {
			"description": "Boolean value indicating true if an update is available from the version on disk."
		},
		"update_version": {
			"description": "Latest version found in the App Store."
		}
	}
	
	__doc__ = description

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
			raise ProcessorError(
				"Invalid adam-id %s"
				% e)
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

			
	def main(self):
		# Assign variables
		adam_id = self.env.get("adam_id")
		app_path = self.env.get("app_path")

		app_details = []
		if (adam_id):
			app_dict = {}
			app_dict['adam-id'] = adam_id
			app_details.append(app_dict)
			try:
				check_app_updates(app_details)
			except HTTPError, e:
				raise ProcessorError(
					"Invalid adam-id %s: %s"
					% (adam_id, e))
		
		# if we get here, there was no adam_id specified
		if not app_path:
			raise ProcessorError("No adam-id or app_path specified.  Aborting.")
		
		# if we get here, there's an app_path
		try:
			decoded_receipt = pyMASreceipt.get_app_receipt(app_path)
		except IOError, e:
			raise ProcessorError("Invalid app_path %s: %s" % (app_path, e))
		
		

# 1) We either have an adam_id that we want to use, or a path to a local app
# 2) If we have a local app, we parse the receipt for its info
# 3) If we have an adam_id, we check directly.
# 4) If we have neither, ABORT
# 5) If we have both, pick adam_id

		app_dict= {}
		app_dict['CFBundleIdentifier'] = "com.fail.fake"
		app_dict['CFBundleShortVersionString'] = 'fail'
		app_dict['adam-id'] = adam_id
		app_dict['installed-version-identifier'] = int(number)
		# see if version exists in /Applications
		# if not found on disk, assume that there's an update available
		# if found in /Applications, compare version
		# if version from store matches disk, compare to munki
		
		self.output("Unarchived %s to %s" 
					% (archive_path, destination_path))

if __name__ == '__main__':
	processor = AppStoreUpdateChecker()
	processor.execute_shell()
	