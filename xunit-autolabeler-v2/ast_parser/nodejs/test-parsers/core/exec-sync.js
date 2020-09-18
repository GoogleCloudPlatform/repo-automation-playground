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

exports.parse = (
  testStatements,
  commandToDescribeMap,
  describeChain,
  testPaths
) => {
  testStatements.forEach((statement) => {
    let entireCmd;

    if (statement.type === "VariableDeclaration") {
      let execStmt = statement.declarations[0].init;
      execStmt = execStmt.argument || execStmt;

      if (execStmt.callee && execStmt.callee.name === "execSync") {
        entireCmd = execStmt.arguments[0];
      }
    } else if (
      statement.expression &&
      statement.expression.type === "AssignmentExpression" &&
      statement.expression.right.arguments
    ) {
      entireCmd = statement.expression.right.arguments[0];
    }

    if (entireCmd) {
      entireCmd = entireCmd.quasis || [entireCmd];

      const [subCmd] = entireCmd
        .filter((cmdPart) => cmdPart.value)
        .map(
          (cmdPart) =>
            (cmdPart.value.raw === undefined ? cmdPart.value : cmdPart.value.raw)
              .replace("/", " ") // HACK: some snippets (e.g. nodejs-vision) use slashes in weird places
              .replace(/(^\s+|\s+$)/g, "")
              .replace(/(^node\s|\.js)/g, "") // for e.g. `node file.js` instead of `node file cmd``
              .split(" ")[0]
        )
        .filter((cmdPart) => cmdPart);

      if (!subCmd) {
        return;
      }

      // file paths are case-insensitive (at least on OS X)
      const key = subCmd.toLowerCase();
      commandToDescribeMap[key] = commandToDescribeMap[key] || [];
      commandToDescribeMap[key].push({
        describeChain,
        testPaths,
      });
    }
  });
};
