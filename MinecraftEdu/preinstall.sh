#!/bin/bash

mcpath="/Library/Application Support/minecraftedu"

if [[ -e "$mcpath" ]]
then
	/bin/rm -rf "$mcpath"
fi