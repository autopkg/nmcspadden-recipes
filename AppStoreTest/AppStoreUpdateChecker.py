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

try:
	import asn1
except ImportError:
	raise ProcessorError("No asn1!")

try:
	import pyMASreceipt
except ImportError:
	raise ProcessorError("No pyMASreceipt!")



__all__ = ["AppStoreUpdateChecker"]


class AppStoreUpdateChecker(Processor):
	description = "Check a given Mac App Store app for updates."
	input_variables = {
		"app_item": {
			"required": True,
			"description": "Either an adam-id of an App Store app, or a path to a local Mac App Store app.",
		}
	}
	output_variables = {
		"update_available": {
			"description": ("Boolean value indicating true if an update is available from the version on disk. "
							"Always true if only an adam-id is passed.")
		},
		"update_version": {
			"description": "Latest version found in the App Store.",
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

	def check_app_updates(self, app_info_list, raw_result=False):
		# This function expects a list of dicts with, at a minimum, the 'adam-id' key set
		# This ID is the unique product identifier for an app on the App Store and can be found in the store URL
		# when viewing the app's page in a web browser, like so:
		# https://itunes.apple.com/us/app/evernote/id406056744
		#											 ^^^^^^^^^
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

			
def main(self):
	# Assign variables
	app_item = self.env.get("app_item")
	
	# 1) We either have an adam_id that we want to use, or a path to a local app
	# 2) If we have a local app, we parse the receipt for its info
	# 3) If we have an adam_id, we check directly.
	# 4) If we have neither, ABORT
	# 5) If we have both, pick adam_id
	
	installer_version_identifier = 0
	
	#Assumption: all App Store app paths will contain ".app" in the name.  Probably a safe one.		
	if ".app" in app_item:
		try:
			decoded_receipt = pyMASreceipt.get_app_receipt(app_path)
			## WARNING: THIS MAY NOT ALWAYS WORK.  RETHINK THIS.
			#decoded_receipt[7].value = adam-id
			#decoded_receipt[0].value = "App Store Installer Version ID" 
			app_item = decoded_receipt[7].value
			installer_version_identifier = decoded_receipt[9].value
		except IOError, e:
			raise ProcessorError("Invalid app_path %s: %s" % (app_path, e))
	
	# If it was an .app path, the app_item gets set to an actual adam-id. 
	# Otherwise, if it wasn't an .app path, we assume it already is an adam-id and
	# try to use it.
	app_details = []
	app_dict = {}
	app_dict['adam-id'] = app_item
	app_dict['installer-version-identifier'] = installer_version_identifier
	app_details.append(app_dict)
	try:
		item_details = check_app_updates(app_details)
	except HTTPError, e:
		raise ProcessorError("Invalid adam-id %s: %s" % (app_item, e))
	# If item_details contains a key 'incompatible-items', it means the version we have is not up to date.
	# If installer-version-identifier wasn't set (and was 0), we'll always get 'incompatible-items'.
	# So now we can check for the presence of 'incompatible-items' and then report that there's an update available with a specific version
	# If that key isn't there, then the app is up to date.
	
	if 'incompatible-items' in item_details:
		self.env["update_version"] = item_details['incompatible-items'][0]['current-version']
		self.env["update_available"] = True
		self.output("App store version: %s" % item_details['incompatible-items'][0]['current-version'])
	else: 
		#no update available, we're up to date
		self.env["update_version"] = installer_version_identifier
		self.env["update_available"] = False
		self.output("%s is up to date: %s" % (self.env.get("app_item"), installer_version_identifier))
	# end

if __name__ == '__main__':
	processor = AppStoreUpdateChecker()
	processor.execute_shell()
	
