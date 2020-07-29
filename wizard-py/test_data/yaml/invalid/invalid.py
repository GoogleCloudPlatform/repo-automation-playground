# Copyright 2016 Google Inc.
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


# [START detectable_tag]
def method_1():
    return 'method 1'
# [END detectable_tag]


# [START another_detectable_tag]
def method_2():
    return 'method 2'
# [END another_detectable_tag]


# [START overwritten_tag]
# [START constituent_tag]
# [START undetectable_tag]
# These tags won't be detected by source parsers,
# but will be picked up by grep operations
# [END undetectable_tag]
# [END constituent_tag]
# [END overwritten_tag]
