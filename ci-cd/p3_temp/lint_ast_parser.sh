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


# Generic lint
flake8

# Type hints
#   Must be separate commands to avoid duplicate module error
#   See https://github.com/python/mypy/issues/4008#issuecomment-332032784
mypy */*.py --ignore-missing-imports
mypy */*/*.py --ignore-missing-imports
