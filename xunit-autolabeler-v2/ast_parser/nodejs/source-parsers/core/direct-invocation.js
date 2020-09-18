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
  let snippetMethods = sourceTokens.body.map(
    (expr) => (expr.declarations && expr.declarations[0]) || expr
  );
  snippetMethods = snippetMethods.filter(
    (expr) => expr.id && expr.id.name && expr.id.name !== "main"
  );
  snippetMethods = snippetMethods.filter(
    (expr) => !expr.init || expr.init.type === "ArrowFunctionExpression"
  );

  snippetMethods.forEach(
    (method) =>
      (method.drift = {
        methodName: method.id.name,
        name: method.id.name,
        sourcePath,
        startLine: method.loc.start.line,
        endLine: method.loc.end.line,
        parser: "directInvocation",
      })
  );

  return snippetMethods;
};
