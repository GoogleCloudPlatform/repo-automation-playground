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


import os
import constants
import subprocess


def __getFiles(root_dir, predicate):
    # Ignore 'lib' and dot-folders (e.g. '.nox', '.github', etc.)
    paths = [os.path.join(root_dir, p) for p in os.listdir(root_dir)
             if p != 'lib' and
             (p.startswith('.drift-data') or not p.startswith('.'))]

    folders = [p for p in paths if not os.path.isfile(p)]

    files = [p for p in paths if os.path.isfile(p)
             and predicate(os.path.basename(p))]

    for f in folders:
        files += __getFiles(f, predicate)

    return files


def get_python_files(root_dir):
    return __getFiles(root_dir, lambda p: p.endswith('.py'))


def get_yaml_files(root_dir):
    return __getFiles(root_dir, lambda p: p == '.drift-data.yml')


def get_region_tags(root_dir):
    proc = subprocess.Popen(
        constants.REGION_TAG_GREP_ARGS,
        stdout=subprocess.PIPE,
        cwd=root_dir)
    region_tags = proc.stdout.read().decode().split('\n')
    region_tags = [x.strip()[9:-1] for x in region_tags]
    region_tags = [x for x in region_tags if len(x) > 1]

    return list(set(region_tags))
