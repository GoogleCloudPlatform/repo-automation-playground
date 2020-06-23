# Node.js AST snippet labeler

This script parses Node.js snippets, and takes advantage of DPE idioms to automatically map tests to their respective snippets.

**Googlers:** This is part of the "DRIFT test tracker" project.

## Idioms supported
The following testing idioms/file formats are supported:
 - `yargs`-based CLI samples invoked via `execSync()`
 - snippet methods directly invoked on a `require` (or `proxyquire`) result
 - snippets invoked by an `ExpressJS` HTTP route handler
 - Cloud Functions snippets (`exports.functionName = {...}`) invoked directly or via HTTP requests

This script also supports _direct snippet method invocations for snippets wrapped in a main method_ as a temporary workaround, but this capability may be removed in the future.

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

Validate .drift-data.yml files in a directory
```
node index.js validate-yaml <rootDir>
```
