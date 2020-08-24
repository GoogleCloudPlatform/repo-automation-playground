# Python AST snippet parser

## What this does
This tool extracts region tags from Python snippets [such as these](https://github.com/googlecloudplatform/python-docs-samples), and matches those region tags to those snippets' tests.

## How it works
Most snippets written by Cloud DPEs are written in one of a few different formats. This tool parses snippets written in those formats to determine which region tags and tests (if any) are related to them. The tool then combines this information to determine which tests correspond to a given region tag. 

It can display this information to the user via a CLI, or inject it into a `pytest`-generated `XUnit` output file supplied via `stdin`. Results are sent to `stdout` by default, but region tag/test mapping injection (via the `inject-snippet-mapping` command) supports writing output to a file via an optional `--output-file` argument.

## Help
```
usage: cli.py [-h]
              {list-region-tags,list-source-files,inject-snippet-mapping,validate-yaml}
              ... root_dir

positional arguments:
  {list-region-tags,list-source-files,inject-snippet-mapping,validate-yaml}
    list-region-tags
    list-source-files
    inject-snippet-mapping
    validate-yaml
  root_dir              Root directory

optional arguments:
  -h, --help            show this help message and exit
```

**Note:** the `inject-snippet-mapping` command expects an XUnit file to be supplied via `stdin`.

### Example usage
```
cat test_data/parser/edge_cases/xunit_example.xml | python cli.py inject-snippet-mapping --output-file "xunit_example_labelled.xml" test_data/parser/edge_cases
```
