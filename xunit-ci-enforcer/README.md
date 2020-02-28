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

## Caveats
The script is **not currently** recursive. To scan an entire repository, you must _explicitly_ specify the directories to be scanned.

(We plan to add recursive functionality in the future if there is enough interest.)