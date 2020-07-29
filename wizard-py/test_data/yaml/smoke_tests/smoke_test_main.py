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


# [START undetectable_tag]
# This tag won't be detected by source parsers,
# but will be picked up by grep operations
# [END undetectable_tag]


# [START no_explicit_tests]
def no_explicit_tests():
    return 'no explicit tests'
# [END no_explicit_tests]


# [START constituent_tests]
# This method is tested by other methods' tests
def constituent_tests():
    return 'constituent tests'
# [END constituent_tests]
