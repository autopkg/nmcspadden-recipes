# recipes

My own collection of recipes for Autopkg.

**NOTE: Several recipes are deprecated are left purely for historical reasons.**

## AppStoreApp Recipe

This recipe is designed to include an App Store app in Autopkg checks.  It optionally
checks your local downloaded copy for updates against the App Store, and
then either directly imports into Munki or packages it up (which can then be imported into Munki or any other package-based deployment system).

**You must override this recipe for each App Store app you want to include.  This set of recipes does nothing useful by itself!**

How to use it with Keynote, as an example:

1.  `autopkg make-override AppStoreApp.munki -n MAS-Keynote.munki`

2.  Edit the MAS-Keynote.munki recipe. Replace the NAME variable with
    "Keynote". It will automatically assume that your app is in
    /Applications, and set the PATH to be /Applications/Keynote.app. The
    NAME should always correspond to whatever comes before the ".app" in
    the app name. This should always point to a locally downloaded copy
    of the App Store App.

3.  `autopkg run -vvvv MAS-Keynote.munki`

What actually happens when you run the Munki recipe:

1.  Copy the app from /Applications into the cache directory.

2.  Create a DMG for Munki.

3.  Create the Munki pkginfo.

4.  Import into Munki if the local app is newer.

5.  Delete the copy of the app from the cache directory.

The .pkg recipe functions similarly:

1.  Determine the version of the local app.

2.  Build a pkg from the local app if there is not one already built for that version.

To check multiple apps, create one new override for each app you want to
check:
`autopkg make-override AppStoreApp.munki -n MAS-iPhoto.munki autopkg make-override AppStoreApp.munki -n MAS-GarageBand.munki autopkg make-override AppStoreApp.munki -n MAS-iMovie.munki`

**Important Note:** This recipe does *not* download updates for AppStore
apps. It only checks to see if your copy is up to date or not, and then
notifies you via standard output. The admin is still responsible for
downloading the update from the App Store, either automatically (via the
System Preferences option) or manually (via the App Store).
