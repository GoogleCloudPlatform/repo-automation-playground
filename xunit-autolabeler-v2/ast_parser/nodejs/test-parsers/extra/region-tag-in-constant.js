// Copyright 2020 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

"use strict";

const execSyncParser = require("../core/exec-sync.js");

exports.parse = (
  testStatements,
  commandToDescribeMap,
  describeChain,
  testPaths,
  topLevelRegionTag
) => {
  execSyncParser.parse(
    testStatements,
    commandToDescribeMap,
    describeChain,
    testPaths
  );
  return;
  // Get properties for the specified region tag
  const describeElements = commandToDescribeMap.filter((x) =>
    x.describeChain.includes(topLevelRegionTag)
  );

  const describeChains = describeElements.map((x) => x.describeChain);
  const describePaths = describeElements.map((x) => x.testPaths);

  // Concatenate relevant properties together

  console.log("DEC", describeChains);
};
