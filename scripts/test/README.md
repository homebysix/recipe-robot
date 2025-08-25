# Recipe Robot Tests

These modules use `unittest` to test various functionalities of Recipe Robot. If used regularly, this would allow us to detect and resolve errors in Recipe Robot before making new releases available to the public.

## Requirements

Install the `coverage` tool for recording test coverage:

```bash
/usr/local/autopkg/python -m pip install -U coverage
```

Check Recipe Robot's config to make sure download, pkg, and munki recipes are enabled. Also turn on the "strip developer suffixes".

```bash
defaults write com.elliotjordan.recipe-robot RecipeIdentifierPrefix "com.github.foo"
defaults write com.elliotjordan.recipe-robot RecipeCreateLocation "~/Library/AutoPkg/RecipeRobotTestOutput"
defaults write com.elliotjordan.recipe-robot RecipeTypes -array "download" "pkg" "munki" "install"
defaults write com.elliotjordan.recipe-robot RecipeFormat "plist"
defaults write com.elliotjordan.recipe-robot StripDeveloperSuffixes -bool true
```

Make sure your working directory is the root of this repo.

## Steps

1. Once you've met the above requirements, run the tests with this command:

    ```bash
    /usr/local/autopkg/python -m coverage run -m unittest discover -vs scripts
    ```

    "OK" will be displayed in the output if the tests passed.

1. **Optional: Run functional tests** (actually build and run real recipes using a subset of sample data — can be time-consuming):

    ```bash
    RUN_FUNCTIONAL_TESTS=1 /usr/local/autopkg/python -m coverage run -m unittest discover -vs scripts
    ```

    By default, functional tests are skipped to speed up regular test runs. Set the `RUN_FUNCTIONAL_TESTS=true` environment variable to enable them.

1. To build a coverage report:

    ```bash
    /usr/local/autopkg/python -m coverage report
    /usr/local/autopkg/python -m coverage html
    ```
