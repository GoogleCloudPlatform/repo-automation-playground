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

"""
This file contains string descriptions of YAML validation errors. These
errors are represented as classes to a) make message modification easier
and b) enable direct isinstance() checks.
"""

import dataclasses


@dataclasses.dataclass(repr=False)
class InvalidAttributeViolation:
    attr: str
    yaml_path: str
    region_tag: str
    actual_value: str
    expected_value: str

    def __str__(self):
        return (
            f'Invalid {self.attr} value in file {self.yaml_path} for tag '
            f'{self.region_tag}: {self.actual_value}, expected '
            f'{self.expected_value} (or omission)'
        )


@dataclasses.dataclass(repr=False)
class AdditionsKeyNotAListViolation:
    region_tag: str
    yaml_path: str

    def __str__(self):
        return (
            f'Additions key for {self.region_tag} in {self.yaml_path} is not a'
            ' list!'
        )


@dataclasses.dataclass(repr=False)
class UnusedRegionTagViolation:
    region_tag: str
    yaml_path: str

    def __str__(self):
        return (
            f'Yaml file {self.yaml_path} contains region tag not used in '
            f'source files: {self.region_tag}'
        )


@dataclasses.dataclass(repr=False)
class MissingTestFileViolation:
    test_path: str
    yaml_path: str

    def __str__(self):
        return (
            f'Test file {self.test_path} used in {self.yaml_path} not found!'
        )


@dataclasses.dataclass(repr=False)
class UnparsedRegionTagViolation:
    region_tag: str
    yaml_path: str

    def __str__(self):
        return (
            f'Yaml file {self.yaml_path} contains '
            f'unparsed region tag: {self.region_tag}.'
            f'  Remove it, or label it with "tested: false".'
        )


@dataclasses.dataclass(repr=False)
class DetectedTagMarkedUndetectedViolation:
    region_tag: str
    yaml_path: str

    def __str__(self):
        return (
            f'Parsed tag {self.region_tag} in file {self.yaml_path} marked'
            ' untested!'
        )


@dataclasses.dataclass(repr=False)
class RepeatedTagViolation:
    region_tag: str

    def __str__(self):
        return (
            f'Region tag {self.region_tag} is used multiple '
            'times in .drift-data.yml files!'
        )
