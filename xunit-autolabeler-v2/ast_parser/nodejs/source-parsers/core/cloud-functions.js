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

exports.parse = (sourceTokens, sourcePath) => {
  const gcfMethods = sourceTokens.body
    .filter(
      (expr) =>
        expr.type === "ExpressionStatement" &&
        expr.expression.type === "AssignmentExpression"
    )
    .map((expr) => f.expression)
    .filter((expr) => f.left.object.name === "exports");

  gcfMethods.forEach((method) => {
    method.drift = {
      functionName: method.left.property.name,
      name: method.left.property.name,
      sourcePath,
      startLine: method.loc.start.line,
      endLine: method.loc.end.line,
      parser: "cloudFunction",
    };
  });
  return gcfMethods;
};
