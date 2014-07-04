recipes
=======

My own collection of recipes for Autopkg

AppStoreApp Recipe
--------------

This recipe allows you to override it with an App Store app, optionally check your local downloaded copy for updates against the App Store, and then either directly import into Munki or package it up (and then import it into Munki).

In order to benefit from the actual update check, you need to install pyasn1: sudo pip install git+https://github.com/geertj/python-asn1.git#egg=pyasn1.

How to use it with Keynote, as an example:

1. `autopkg make-override AppStoreApp.munki -n MAS-Keynote.munki`
2. Edit the MAS-Keynote.munki recipe.  Replace the NAME variable with "Keynote". It will automatically assume that your app is in /Applications, and set the PATH to be /Applications/Keynote.app.  The NAME should always correspond to whatever comes before the ".app" in the app name.  This should always point to a locally downloaded copy of the App Store App.
3. `autopkg run -vvvv MAS-Keynote.munki`

What actually happens when you run the Munki recipe:

1. **If pyasn1 is installed**, check the local app's version and compare it to what the App Store reports is the most recent version.  If the versions do not match (i.e. the App Store is newer), it will stop the recipe (*update_available == YES* resolves to true).  If you are running with at least one level of verbosity (`autopkg run -v MAS-Keynote.munki`), the version mismatch will be printed to the standard output.
2. **Check to see if we already processed this version.** It uses a processor called LastVersionProvider that reads the receipt in the AutoPkg cache to see if it successfully imported the same exact App Store version previously.  If it did so, it assumes that we don't need to do anything because it's already in the repo and then aborts the run (*last_version == version* resolves to true).
	- *NOTE:* This may result in unexpected behavior if the munkiimport operation fails, as the receipt left behind may indicate a version number which the processor will assume was correct.  If you are not getting expected behavior here, delete the Receipts folder for that recipe and run it again.
2. **Copy the app from /Applications into the cache directory.**
3. **Create a DMG for Munki.**
4. **Create the Munki pkginfo.**
5. **Import into Munki.**
6. **Delete the copy of the app from the cache directory.**

The .pkg recipe and .pkg.munki recipe perform similar checks, but create a package to be installed rather than a DMG.

To check multiple apps, create one new override for each app you want to check:
`autopkg make-override AppStoreApp.munki -n MAS-iPhoto.munki`
`autopkg make-override AppStoreApp.munki -n MAS-GarageBand.munki`
`autopkg make-override AppStoreApp.munki -n MAS-iMovie.munki`

**Important Note:**
This recipe does *not* download updates for AppStore apps.  It only checks to see if your copy is up to date or not, and then notifies you via standard output. The admin is still responsible for downloading the update from the App Store, either automatically (via the System Preferences option) or manually (via the App Store).
