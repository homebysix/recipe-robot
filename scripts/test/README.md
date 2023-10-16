# Recipe Robot Tests

These modules use `nose` to test various functionalities of Recipe Robot. If used regularly, this would allow us to detect and resolve errors in Recipe Robot before making new releases available to the public.

## Requirements

You must have the `nose` tool installed (and probably `pip3` to install it).

```
/usr/local/autopkg/python -m pip install nose --user
```

Also check Recipe Robot's config to make sure download, pkg, and munki recipes are enabled. Also turn on the "strip developer suffixes".

```
defaults write com.elliotjordan.recipe-robot RecipeIdentifierPrefix "com.github.foo"
defaults write com.elliotjordan.recipe-robot RecipeCreateLocation "~/Library/AutoPkg/RecipeRobotTestOutput"
defaults write com.elliotjordan.recipe-robot RecipeTypes -array "download" "pkg" "munki" "install"
defaults write com.elliotjordan.recipe-robot RecipeFormat "plist"
defaults write com.elliotjordan.recipe-robot StripDeveloperSuffixes -bool true
```

Make sure your working directory is the **scripts** folder.

```
cd ./scripts
```

## Steps

Once you've met the above requirements, run the tests with this command:

```
/usr/local/autopkg/python -m nose -v test
```

"OK" will be displayed in the output if the tests passed.
