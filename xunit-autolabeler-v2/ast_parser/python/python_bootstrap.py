# Copyright 2020 Google LLC.
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
import sys

from python import invoker

if len(sys.argv) != 2:
    raise ValueError('Please specify exactly one [root] directory.')

root_dir = sys.argv[1]
output_file = os.path.join(root_dir, 'repo.json')

json_out = invoker.get_json_for_dir(root_dir)
with open(output_file, 'w') as f:
    f.write(json_out + '\n')

print(f'JSON written to: {output_file}')
print('Do not move this file!')
