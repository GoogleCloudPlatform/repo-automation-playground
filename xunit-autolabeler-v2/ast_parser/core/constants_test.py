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

from ast_parser.core import constants

import pytest


@pytest.mark.parametrize(
    'region_tag_line,expected',
    [
        ('[START foo]', 'foo'),
        ('[END foo]', 'foo'),
        ('[START foo_bar]', 'foo_bar'),
        ('[START foo-bar]', 'foo-bar'),
        ('// [START foo]', 'foo'),
        ('# [START foo]', 'foo')
    ],
    ids=[
        'basic_start_tag',
        'basic_end_tag',
        'underscore_tag',
        'hyphen_tag',
        'slash_comment',
        'pound_comment'
    ]
)
def test_detects_region_tag(region_tag_line, expected):
    result = constants.REGION_TAG_ONLY_REGEX.search(region_tag_line)
    assert result is not None
    assert expected in result.group(0)
