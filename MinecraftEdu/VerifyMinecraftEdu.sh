#!/bin/sh

#VerifyMinecraftEdu

mcpath="/Library/Application Support/minecraftedu"
homepath="$HOME/Library/Application Support/"
endpath="$HOME/Library/Application Support/minecraftedu/"
#the rsync command below will not behave as expected if the trailing slashes are missing!

if [[ -e "$mcpath" ]]
then
	/usr/bin/rsync -rtuc "$homepath" "$endpath"
	#r - recursive
	#t - preserve modification dates
	#u - update the folder, don't copy unchanged files
	#c - calculate checksum of each file to determine if it's changed
else
	echo "Didn't find MinecraftEDU in /Library/Application Support/."
fi
