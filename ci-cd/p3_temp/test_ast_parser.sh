#!/usr/bin/env bash
# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# We'll be at the git root, so move to the target directory.
cd xunit-autolabeler-v2/ast_parser

# add user's pip binary path to PATH
export PATH="${HOME}/.local/bin:${PATH}"

pip install --user -r requirements.txt
pip install --user -r requirements-dev.txt

# Generate required polyglot_snippet_data.py files
./python_bootstrap.py core/test_data/cli/additions
./python_bootstrap.py core/test_data/cli/bad_region_tag
./python_bootstrap.py core/test_data/cli/dotfile_test
./python_bootstrap.py core/test_data/cli/dotfile_test/.dotfile
./python_bootstrap.py core/test_data/parser
./python_bootstrap.py core/test_data/parser/edge_cases
./python_bootstrap.py core/test_data/parser/exclude_tags
./python_bootstrap.py core/test_data/parser/flask
./python_bootstrap.py core/test_data/parser/http
./python_bootstrap.py core/test_data/parser/nested_tags
./python_bootstrap.py core/test_data/parser/snippet_invocation_methods
./python_bootstrap.py core/test_data/parser/webapp2
./python_bootstrap.py core/test_data/parser/duplicate_region_tag
./python_bootstrap.py core/test_data/yaml
./python_bootstrap.py core/test_data/yaml/explicit_tests
./python_bootstrap.py core/test_data/yaml/invalid
./python_bootstrap.py core/test_data/yaml/overwrite_tests
./python_bootstrap.py core/test_data/yaml/smoke_tests
./python_bootstrap.py python/source_parsers


pytest . \
    --ignore core/test_data \
    --ignore python/test_data \
    --ignore python/source_parsers/test_data
