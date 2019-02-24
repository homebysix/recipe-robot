# Recipe Robot Tests

These modules use `nose` to test various functionalities of Recipe Robot. If used regularly, this would allow us to detect and resolve errors in Recipe Robot before making new releases available to the public.

## Requirements

You must have the `nose` tool installed.

    pip install nose --user

Make sure your working directory is the __scripts__ folder.

    cd ./scripts

## Steps

To run the tests, use:

    nosetests test/test_functional.py
    nosetests test/test_processor.py
    nosetests test/test_recipe_generator.py

"OK" will be displayed in the output if the tests passed.
