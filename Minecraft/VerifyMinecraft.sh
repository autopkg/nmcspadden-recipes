#!/bin/sh

#VerifyMinecraft

mcpath="/Library/Application Support/minecraft"
homepath="$HOME/Library/Application Support/"
endpath="$HOME/Library/Application Support/minecraft/"

if [[ -e "$mcpath" ]]
then
	if [[ ! -e "$endpath" ]]
	then
		cp -R "$mcpath" "$homepath"
		chown -R $USER:staff "$endpath"
	fi
else
	echo "Didn't find Minecraft in /Library/Application Support/."
fi
