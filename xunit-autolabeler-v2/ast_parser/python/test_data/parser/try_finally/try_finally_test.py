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

import try_finally


def test_try_finally():
    try:
        assert try_finally.try_method() == 'try method'
    except Exception:
        # This should NOT be detected by the AST parser.
        # (Exceptions should represent unintended behavior,
        #  and as such are deliberately ignored.)
        assert try_finally.exception_handler() == 'exception handler'
    finally:
        assert try_finally.final_method() == 'final method'
