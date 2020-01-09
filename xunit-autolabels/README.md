# xunit-autolabels

## Purpose
This script automatically labels tests with their corresponding sample(s)' region tag(s).

#### Languages supported
This script supports the major *dynamically-typed* languages supported by GCP:

- Node.js
- Python
- PHP
- Ruby

The following languages are **not** supported, as they are *statically-typed* and thus a better fit for static-analysis-based tools:

- Java
- C#
- Go

#### Accuracy
The script is fairly accurate, but not perfect. Generally, it will notify you if any inaccuracy occurs (via warning and/or error messages).

If it does *not* warn you, please [create an issue](../../issues).

## Running
The script has *four phases* - and must be *run four times* (once per phase):

1. Installing dependencies
1. Identifying all tests (generating `all-tests.xml`)
1. Running individual tests (generating `test-*` folders)
1. Wrapping tests with the appropriate region tag(s)

Some of these phases (the first and third) print commands for you to run in your own terminal. (These commands *cannot* be executed programmatically due to race conditions and/or configuration issues, such as Python `virtualenv`s and environment variables like `GCLOUD_PROJECT`.)

#### Installing dependencies
Run `npm install` to install the script's dependencies.

#### Invoking the script
Run the script itself using `node index.js`.

*Note that you will have to run the script up to 4 times, as described above.*

## Testing
```sh
cd repo-automation-playground/xunit-autolabels
source test/data/*/gen_data.sh
npm test
```

## Support
This project is **experimental** and may be deprecated at any time without notice.

*This is not an official Google product.*