#!/bin/sh

#VerifyMinecraftEdu

mcpath="/Library/Application Support/minecraftedu"
homepath="$HOME/Library/Application Support/"
endpath="$HOME/Library/Application Support/minecraftedu/"

if [[ -e "$mcpath" ]]
then
	if [[ ! -e "$endpath" ]]
	then
		cp -R "$mcpath" "$homepath"
		chown -R $USER:staff "$endpath"
	fi
else
	echo "Didn't find MinecraftEDU in /Library/Application Support/."
fi
