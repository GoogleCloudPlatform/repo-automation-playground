# Node.js AST snippet labeler

This script parses Node.js snippets, and takes advantage of DPE idioms to automatically map tests to their respective snippets.

## Usage

List region tags in a directory
```
node index.js list-region-tags <path> 
```

List snippet source files in a directory
```
node index.js list-source-files <path>
```

Inject snippet mapping into XUnit output
```
# Using an XUnit output file
cat xunit-output.xml | index.js inject-snippet-mapping <rootDir>

# Using XUnit output from a test runner
mocha <rootDir> --reporter=xunit | index.js inject-snippet-mapping <rootDir>
```
