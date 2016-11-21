# recipes

My own collection of recipes for Autopkg.

## AppStoreApp Recipe

This recipe is designed to include an App Store app in Autopkg checks.  It optionally
checks your local downloaded copy for updates against the App Store, and
then either directly imports into Munki or packages it up (which can then be imported into Munki or any other package-based deployment system).

**You must override this recipe for each App Store app you want to include.  This set of recipes does nothing useful by itself!**

In order to benefit from the actual update check, you need to install
[pyasn1][]. There are a couple of ways to do this [credit to [Timothy
Sutton][] for the suggestions]:

-   `pip install --user git+https://github.com/geertj/python-asn1.git#egg=pyasn1`
    which will install in the user's Python library, which is by default
    part of the search path on OS X. This will need to be run from the
    same user account that runs Autopkg. *This is the recommended way.*

-   Since pip is not a standard part of OS X, you can instead use
    `easy_install`:
    -	`mkdir -p ~/Library/Python/2.7/lib/python/site-packages`

    -   `easy_install --install-dir="$HOME/Library/Python/2.7/lib/python/site-packages" https://github.com/geertj/python-asn1/archive/master.zip`

    -   This install is slightly different, packaging the module into an
        egg (zipfile) and adding loader commands to a .pth file, which
        Python knows to look for.

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

1.  **If pyasn1 is installed**, check the local app's version and
    compare it to what the App Store reports is the most recent version.
    If the versions do not match (i.e. the App Store is newer), it will
    stop the recipe (*update\_available == YES* resolves to true). If
    you are running with at least one level of verbosity
    (`autopkg run -v MAS-Keynote.munki`), the version mismatch will be
    printed to the standard output.

3.  **Copy the app from /Applications into the cache directory.**

4.  **Create a DMG for Munki.**

5.  **Create the Munki pkginfo.**

6.  **Import into Munki.**

7.  **Delete the copy of the app from the cache directory.**

The .pkg recipe and .pkg.munki recipe perform similar checks, but create
a package to be installed rather than a DMG.

To check multiple apps, create one new override for each app you want to
check:
`autopkg make-override AppStoreApp.munki -n MAS-iPhoto.munki autopkg make-override AppStoreApp.munki -n MAS-GarageBand.munki autopkg make-override AppStoreApp.munki -n MAS-iMovie.munki`

**Important Note:** This recipe does *not* download updates for AppStore
apps. It only checks to see if your copy is up to date or not, and then
notifies you via standard output. The admin is still responsible for
downloading the update from the App Store, either automatically (via the
System Preferences option) or manually (via the App Store).

  [pyasn1]: https://github.com/geertj/python-asn1
  [Timothy Sutton]: https://github.com/timsutton
