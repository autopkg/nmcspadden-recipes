#!/usr/bin/env python
#
# Copyright 2010 Per Olofsson
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from __future__ import absolute_import

import os.path
import shutil
from glob import glob

from autopkglib import Processor, ProcessorError
from autopkglib.DmgMounter import DmgMounter

__all__ = ["ParentCopier"]


class ParentCopier(DmgMounter):
    description = "Copies source_path to destination_path."
    input_variables = {
        "source_path": {
            "required": True,
            "description": ("Path to a file or directory to copy. "
                "Can point to a path inside a .dmg which will be mounted. "
                "This path may also contain basic globbing characters such as "
                "the wildcard '*', but only the first result will be returned."),
        },
        "destination_path": {
            "required": True,
            "description": "Path to gdestination.",
        },
        "overwrite": {
            "required": False,
            "description": "Whether the destination will be overwritten if necessary.",
        },
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

    def copy(self, source_item, dest_item, overwrite=False):
        '''Copies source_item to dest_item, overwriting if allowed'''
        # Remove destination if needed.
        if os.path.exists(dest_item) and overwrite:
            try:
                if os.path.isdir(dest_item) and not os.path.islink(dest_item):
                    shutil.rmtree(dest_item)
                else:
                    os.unlink(dest_item)
            except OSError as err:
                raise ProcessorError(
                    "Can't remove %s: %s" % (dest_item, err.strerror))

        # Copy file or directory.
        try:
            if os.path.isdir(source_item):
                shutil.copytree(source_item, dest_item, symlinks=True)
            elif not os.path.isdir(dest_item):
                shutil.copyfile(source_item, dest_item)
            else:
                shutil.copy(source_item, dest_item)
            self.output("Copied %s to %s" % (source_item, dest_item))
        except BaseException as err:
            raise ProcessorError(
                "Can't copy %s to %s: %s" % (source_item, dest_item, err))

    def main(self):
        source_path = self.env['source_path']
        # Check if we're trying to copy something inside a dmg.
        (dmg_path, dmg,
         dmg_source_path) = source_path.partition(".dmg/")
        dmg_path += ".dmg"

        # Check to see if it's a relative path and can be found inside the parent recipes
        if source_path and not source_path.startswith("/"):
            # search for it
            source_path = self.find_path_for_relpath(source_path)

        try:
            if dmg:
                # Mount dmg and copy path inside.
                mount_point = self.mount(dmg_path)
                source_path = os.path.join(mount_point, dmg_source_path)
            # process path with glob.glob
            matches = glob(source_path)
            matched_source_path = matches[0]
            if len(matches) > 1:
                self.output("WARNING: Multiple paths match 'source_path' glob '%s':"
                    % source_path)
                for match in matches:
                    self.output("  - %s" % match)

            matched_source_path = glob(source_path)[0]
            if [c for c in '*?[]!' if c in source_path]:
                self.output("Using path '%s' matched from globbed '%s'."
                    % (matched_source_path, source_path))

            # do the copy
            self.copy(matched_source_path, self.env['destination_path'],
                      overwrite=self.env.get("overwrite"))
        finally:
            if dmg:
                self.unmount(dmg_path)


if __name__ == '__main__':
    processor = ParentCopier()
    processor.execute_shell()
