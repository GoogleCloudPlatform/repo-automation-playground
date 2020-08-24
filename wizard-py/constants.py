# Copyright 2020 Google LLC. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


IGNORED_METHOD_NAMES = [
    'run_command',
    'parse_command_line_args',
    'main'
]

HTTP_CLASS_NAMES = [
    'app',
    'client'
]

HTTP_METHOD_NAMES = [
    'get',
    'post',
    'put',
    'patch',
    'delete',
    'options'
]

TAG_LINE_RANGE = 8

# Per https://flask.palletsprojects.com/en/1.1.x/quickstart/#http-methods
FLASK_DEFAULT_METHODS = ['get']

REGION_TAG_GREP_ARGS = \
    'grep -hr START . --include=*.py --exclude=*/lib/*'.split(' ')

TEST_FILE_MARKER = 'test.py'

RESERVED_YAML_KEYS = set(['tested', 'overwrite', 'ignore', 'additions'])

SOURCE_REQUIRED_FOR_KEYS = set(['overwrite'])
SOURCE_BANNED_FOR_KEYS_WITHOUT_OVERWRITE = set(['tested'])

REQUIRED_KEY_VALUES = {
    'tested': False,
    'overwrite': True,
    'ignore': True
}

# region tags that don't uniquely identify a sample
IGNORED_REGION_TAGS = ['app', 'all']
