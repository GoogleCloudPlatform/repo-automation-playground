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

'use strict';

const {
    EXPRESS_METHOD_NAMES,
    REGION_TAG_CONSTANT_REGEX
} = require('./constants')

const uniq = require('uniq');
const deepEqual = require('deep-equal');
const path = require('path');

const parsers = {
    cloudFunction: require('./test-parsers/core/cloud-functions.js'),
    httpRequest: require('./test-parsers/core/http-requests.js'),
    directInvocation: require('./test-parsers/core/direct-invocation.js'),
    execSync: require('./test-parsers/core/exec-sync.js'),
    regionTagInConstant: require('./test-parsers/extra/region-tag-in-constant.js')
};

exports.getDescribeClauses = (testTokens) => {
    const clauses = testTokens.body.filter(s => s.expression && s.expression.callee && s.expression.callee.name === 'describe');
    return clauses;
};

const parseItClause = (itClause, describeChain, testPath, topLevelRegionTag) => {
    // Ignore non-"it" clauses (e.g. "before", "after")
    if (!itClause.expression || !itClause.expression.callee || itClause.expression.callee.name !== 'it') {
        return {};
    }

    // Process "it" clauses
    // ASSUMPTION: test is always 2nd argument of "it" clause
    const itClauseArgs = itClause.expression.arguments;

    // Compute final describe chain
    describeChain = describeChain.concat(itClauseArgs[0].value);

    let testStatements = itClauseArgs[1].body.body;
    const testPaths = [testPath];
    const commandToDescribeMap = {}

    // Collapse "try" statements
    testStatements = testStatements.map(t => t.block && t.block.body[0] || t)

    // Parse tests
    parsers.httpRequest.parse(testStatements, commandToDescribeMap, describeChain, testPaths);
    parsers.cloudFunction.parse(testStatements, commandToDescribeMap, describeChain, testPaths);
    parsers.directInvocation.parse(testStatements, commandToDescribeMap, describeChain, testPaths);
    parsers.execSync.parse(testStatements, commandToDescribeMap, describeChain, testPaths);
    parsers.regionTagInConstant.parse(
        testStatements, 
        commandToDescribeMap, 
        describeChain, 
        testPaths,
        topLevelRegionTag);

    return commandToDescribeMap;
}

exports.getDescribeChainMap = (describeClauses, testPath, topLevelRegionTag, describeChain) => {
    describeChain = describeChain || [];

    // Parse child describe clauses
    const aggregateCliMap = {};
    describeClauses.forEach(c => {
        let resultCliMap;
        if (c.expression && c.expression.callee && c.expression.callee.name === 'describe') {
            // ASSUMPTION:
            //   description will always be 1st argument of describe()
            //   test function will always be 2nd argument of describe()
            const children = c.expression.arguments[1].body.body;

            let description = c.expression.arguments[0];

            // Handle "region tag in constant" tests (e.g. nodejs-translate)
            description = description.value || description.name;
            if (topLevelRegionTag && description.match(REGION_TAG_CONSTANT_REGEX)) {
                description = topLevelRegionTag;
            }

            const newDescribeChain = describeChain.concat(description);
            resultCliMap = exports.getDescribeChainMap(
                children, 
                testPath, 
                topLevelRegionTag, 
                newDescribeChain);
        } else {
            resultCliMap = parseItClause(c, describeChain, testPath, topLevelRegionTag);
        }

        // Aggregate recursive results
        Object.keys(resultCliMap).forEach(key => {
            aggregateCliMap[key] = (aggregateCliMap[key] || []).concat(resultCliMap[key]);
        });
    }); 

    return aggregateCliMap;
}

exports.addDescribeChainToMethods = (testPath, methodsWithDriftData, describeChainMap, fileWideInvocation) => {
    // Initialize default values used in test parsing
    methodsWithDriftData.map(m => m.drift).forEach(d => {
        d.testData = d.testData || [];
    })

    methodsWithDriftData.forEach(method => {
        const d = method.drift;

        let describeObjs;
        const sourcePathNoExtension = path.parse(d.sourcePath).name.toLowerCase();
        if (d.cliInvocation) {
            describeObjs = describeChainMap[d.cliInvocation.toLowerCase()]
        } else if (d.urlPath && describeChainMap[d.urlPath.toLowerCase()]) {
            describeObjs = describeChainMap[d.urlPath.toLowerCase()][d.httpMethod.toLowerCase()];
        } else if (d.name && describeChainMap[d.name.toLowerCase()]) {
            // Directly-invoked method (or Cloud Function)
            describeObjs = describeChainMap[d.name.toLowerCase()]
        } else if (d.functionName && describeChainMap['/' + d.functionName.toLowerCase()]) {
            // URL-invoked Cloud Function
            // (Ignores HTTP methods!)
            const mapEntry = describeChainMap['/' + d.functionName.toLowerCase()];
            describeObjs = {};
            Object.values(mapEntry).map(v => Object.assign(describeObjs, v))
        } else if (path.basename(d.sourcePath) === fileWideInvocation) {
            // Single-test test files
            describeObjs = Object.values(describeChainMap)[0]
        } else if (describeChainMap[sourcePathNoExtension]) {
            // Single-snippet source files, referenced by name (e.g. `snippetName.js`)
            describeObjs = describeChainMap[sourcePathNoExtension]
        } else if (d.sourcePath.includes('quickstart')) {
            describeObjs = describeChainMap[d.sourcePath.toLowerCase()];
        }

        if (describeObjs) {
            d.testData = d.testData.concat(describeObjs);
        }
    })

    // Remove duplicates
    methodsWithDriftData.map(m => m.drift).forEach(d => {
        d.testData = uniq(d.testData, (x, y) => deepEqual(x, y) ? 0 : 1);
    })
}
