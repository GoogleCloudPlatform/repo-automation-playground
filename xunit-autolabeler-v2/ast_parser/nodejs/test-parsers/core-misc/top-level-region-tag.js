// Copyright 2020 Google LLC.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

"use strict";

module.exports = (testTokens) => {
  let topLevelRegionTags = testTokens.body
    .filter((s) => s.type === "VariableDeclaration")
    .map((s) => s.declarations[0].init)
    .filter((i) => i && i.type.endsWith("Literal"));

  topLevelRegionTags = topLevelRegionTags.map((x) =>
    x.quasis ? x.quasis[0].value.raw : x.value
  );
  return topLevelRegionTags;
};
