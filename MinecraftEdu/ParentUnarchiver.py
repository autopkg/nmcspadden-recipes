#!/usr/bin/env python
#
# Copyright 2010 Per Olofsson
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


from __future__ import absolute_import
import os
import subprocess
import shutil

from autopkglib import Processor, ProcessorError


__all__ = ["ParentUnarchiver"]

EXTNS = {
	'zip': ['zip'],
	'tar_gzip': ['tar.gz', 'tgz'],
	'tar_bzip2': ['tar.bz2', 'tbz'],
	'tar': ['tar']
}

class ParentUnarchiver(Processor):
	description = "Archive decompressor for zip and common tar-compressed formats. Also searches parent recipes if relative path is given."
	input_variables = {
		"archive_path": {
			"required": False,
			"description": "Path to an archive. Defaults to contents of the 'pathname' "
						   "variable, for example as is set by URLDownloader.",
		},
		"destination_path": {
			"required": False,
			"description": ("Directory where archive will be unpacked, created if necessary. "
						   "Defaults to RECIPE_CACHE_DIR/NAME.")
		},
		"purge_destination": {
			"required": False,
			"description": "Whether the contents of the destination directory will be removed before unpacking.",
		},
		"archive_format": {
			"required": False,
			"description": ("The archive format. Currently supported: 'zip', 'tar_gzip', 'tar_bzip2'. "
						   "If omitted, the format will try to be guessed by the file extension.")
		}
	}
	output_variables = {
	}
	
	__doc__ = description

	def find_path_for_relpath(self, relpath):
		'''Searches for the relative path.
		Search order is:
			RECIPE_CACHE_DIR
			RECIPE_DIR
			PARENT_RECIPE directories'''
		cache_dir = self.env.get('RECIPE_CACHE_DIR')
		recipe_dir = self.env.get('RECIPE_DIR')
		search_dirs = [cache_dir, recipe_dir]
		if self.env.get("PARENT_RECIPES"):
			# also look in the directories containing the parent recipes
			parent_recipe_dirs = list(set([
				os.path.dirname(item)
				for item in self.env["PARENT_RECIPES"]]))
			search_dirs.extend(parent_recipe_dirs)
		for directory in search_dirs:
			test_item = os.path.join(directory, relpath)
			if os.path.exists(test_item):
				return os.path.normpath(test_item)

		raise ProcessorError("Can't find %s" % relpath)
			
	def get_archive_format(self, archive_path):
		for format, extns in EXTNS.items():
			for extn in extns:
				if archive_path.endswith(extn):
					return format
		# We found no known archive file extension if we got this far
		return None

	def main(self):
		# handle some defaults for archive_path and destination_path
		archive_path = self.env.get("archive_path", self.env.get("pathname"))
		if not archive_path:
			raise ProcessorError("Expected an 'archive_path' input variable but none is set!")
			
		# convert relative path into absolute path by stealing code from PkgCreator
		if archive_path and not archive_path.startswith("/"):
					# search for it
					archive_path = self.find_path_for_relpath(archive_path)
		
		
		destination_path = self.env.get("destination_path",
					os.path.join(self.env["RECIPE_CACHE_DIR"], self.env["NAME"]))

		# Create the directory if needed.
		if not os.path.exists(destination_path):
			try:
				os.mkdir(destination_path)
			except OSError as e:
				raise ProcessorError("Can't create %s: %s" % (path, e.strerror))
		elif self.env.get('purge_destination'):
			for entry in os.listdir(destination_path):
				path = os.path.join(destination_path, entry)
				try:
					if os.path.isdir(path) and not os.path.islink(path):
						shutil.rmtree(path)
					else:
						os.unlink(path)
				except OSError as e:
					raise ProcessorError("Can't remove %s: %s" % (path, e.strerror))
		
		fmt = self.env.get("archive_format")
		if fmt is None:
			fmt = self.get_archive_format(archive_path)
			if not fmt:
				raise ProcessorError("Can't guess archive format for filename %s" %
						os.path.basename(archive_path))
			self.output("Guessed archive format '%s' from filename %s" %
						(fmt, os.path.basename(archive_path)))
		elif fmt not in EXTNS.keys():
			raise ProcessorError("'%s' is not valid for the 'archive_format' variable. Must be one of %s." %
								(fmt, ", ".join(EXTNS.keys())))

		if fmt == "zip":
			cmd = ["/usr/bin/ditto",
				   "--noqtn",
				   "-x",
				   "-k",
				   archive_path,
				   destination_path]
		elif fmt.startswith("tar"):
			cmd = ["/usr/bin/tar",
				   "-x",
				   "-f",
				   archive_path,
				   "-C",
				   destination_path]
			if fmt.endswith("gzip"):
				cmd.append("-z")
			elif fmt.endswith("bzip2"):
				cmd.append("-j")

		# Call command.
		try:
			p = subprocess.Popen(cmd,
								 stdout=subprocess.PIPE,
								 stderr=subprocess.PIPE)
			(out, err) = p.communicate()
		except OSError as e:
			raise ProcessorError("%s execution failed with error code %d: %s" % (
								  os.path.basename(cmd[0]), e.errno, e.strerror))
		if p.returncode != 0:
			raise ProcessorError("Unarchiving %s with %s failed: %s" % (
								  archive_path, os.path.basename(cmd[0]), err))
		
		self.output("Unarchived %s to %s" 
					% (archive_path, destination_path))

if __name__ == '__main__':
	processor = ParentUnarchiver()
	processor.execute_shell()
	