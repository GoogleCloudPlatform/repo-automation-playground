# AST snippet parser - Python

## What this does
This tool extracts snippet data from Python snippets [such as these](https://github.com/googlecloudplatform/python-docs-samples), and serializes that data into a language-agnostic JSON format.

That data can then be used by the "meta-parser" in `ast_parser/core` to match test results with their associated snippets/region tags.

## Usage
Run the following command to generate a `repo.json` file for a specific directory:

```
python python_bootstrap.py YOUR_SAMPLE_DIR
```

**Do not** move the generated `repo.json` file, as this will break its stored filepaths.
