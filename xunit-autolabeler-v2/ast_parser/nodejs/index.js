// Copyright 2020 Google LLC. All Rights Reserved.
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

const espree = require("espree");
const fs = require("fs");
const path = require("path");
const uniq = require("uniq");
const chalk = require("chalk");
const xml2json = require("xml2js").parseStringPromise;
const getStdin = require("get-stdin");

const { TEST_FILEPATH_FILTER } = require("./constants");

const testParser = require("./test-parser");
const testParserMisc = {
  fileWideInvocation: require("./test-parsers/core-misc/file-wide-invocation.js"),
  topLevelRegionTags: require("./test-parsers/core-misc/top-level-region-tag.js"),
};

const sourceParser = require("./source-parser");
const fileUtils = require("./file-utils");

const __parseFile = (filePath) => {
  const program = fs.readFileSync(filePath).toString();
  const tokens = espree.parse(program, {
    ecmaVersion: 12,
    comment: true,
    loc: true,
  });

  return tokens;
};

const parseSource = (sourcePath) => {
  const sourceTokens = __parseFile(sourcePath);

  const methods = sourceParser.getTopLevelMethods(sourceTokens, sourcePath);

  const cliCommands = sourceParser.getCliCommands(sourceTokens);

  sourceParser.addCliCommandsToMethods(methods, cliCommands);

  return methods;
};

const parseTest = (testPath, sourceMethods) => {
  const testTokens = __parseFile(testPath);

  let describeClauses = testParser.getDescribeClauses(testTokens);
  if (describeClauses.length === 0) {
    // all 'it' clauses
    describeClauses = testTokens.body;
  }

  // Handle single-test, global-invocation files
  let fileWideInvocation;
  if (Object.values(describeClauses).length === 1) {
    fileWideInvocation = testParserMisc.fileWideInvocation(testTokens); // for single-test test files
  }

  // Handle global region tags within tests
  const [topLevelRegionTag] = testParserMisc.topLevelRegionTags(testTokens);

  const describeChainMap = testParser.getDescribeChainMap(
    describeClauses,
    testPath,
    topLevelRegionTag
  );

  testParser.addDescribeChainToMethods(
    testPath,
    sourceMethods,
    describeChainMap,
    fileWideInvocation
  );
};

const analyzeDir = async (rootDir) => {
  console.log(`Generating language data for directory: ${rootDir}`);

  const ALL_PATHS = fileUtils.getNodeJsFiles(rootDir);

  const __isTest = (path) => path.includes(TEST_FILEPATH_FILTER);

  const SOURCE_PATHS = ALL_PATHS.filter((x) => !__isTest(x));
  const TEST_PATHS = ALL_PATHS.filter((x) => __isTest(x));

  let sourceMethods = [];
  SOURCE_PATHS.forEach((path) => {
    sourceMethods = sourceMethods.concat(parseSource(path));
  });

  TEST_PATHS.forEach((path) => {
    parseTest(path, sourceMethods);
  });

  // Write parsed data to file
  const repoJsonPath = path.join(rootDir, "repo.json");
  console.log(`Writing language data to file: ${repoJsonPath}`);

  const repoJson = JSON.stringify(sourceMethods.map((m) => m.drift));
  fs.writeFileSync(repoJsonPath, repoJson);

  console.log("JSON write complete. Do not move this file!");
};

if (process.argv.length == 3) {
    analyzeDir(process.argv[2]);
} else {
    console.error('Please specify exactly one root directory')
}
