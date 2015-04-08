#Yo Postprocessor

This is based on Shea Craig's Yo utility, which generates notifications via the Terminal.

This is a shared AutoPkg postprocessor, and will generate a notification anytime an item is imported into the Munki repo.

See the documentation for details on [shared AutoPkg processors](https://github.com/autopkg/autopkg/wiki/Processor-Locations#shared-recipe-processors).

It can be called on your autopkg runs with the `--post` or `--postprocessor` switch:

```
autopkg run VLC.munki --post=com.github.nmcspadden.shared/Yo
```

If will trigger after each recipe.  It will *only* generate notifications with .munki recipes (i.e. recipes that call MunkiImporter as the last processor).  Other recipes will not cause the Yo postprocessor to generate notifications.

By default, yo.app is placed into /Applications/Utilities, but you can override this default and place yo.app anywhere by using the `-k` or `--key` switch with the `yo_path` key:

```
autopkg run VLC.munki --post=com.github.nmcspadden.shared/Yo -k yo_path="/Users/nick/Desktop/yo.app"
```

Yes, I know, this is kind of useless, but who cares, I was bored on a plane with no WiFi.