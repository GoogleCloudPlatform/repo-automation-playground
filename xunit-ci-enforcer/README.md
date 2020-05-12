# XUnit CI Enforcer

## Overview
The `region_tag_enforcer.sh` script checks to make sure all region tags used in your code snippets are used in your tests, and vice versa.

## Running
The following command will check all samples in a given directory:

```
./region_tag_enforcer <YOUR_SAMPLE_DIRECTORY>
```

The script can also accept a list of directories:

```
./region_tag_enforcer <YOUR_SAMPLE_DIRECTORY> <ANOTHER_SAMPLE_DIRECTORY> ...
```

### Running recursively
Though the script itself is not recursive, we can use the UNIX `find` command to provide recursive-like functionality:

Below is an example `find` command invocation for Node.js. (Note the `node_modules` exclusion, and how `-name *est` checks for `test` and `system-test` directories.)

```
./region_tag_enforcer $(find . -type d -name "*est" -not -path "*/node_modules/*" | xargs -I @ dirname @)
```
