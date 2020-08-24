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

const deepEqual = require('deep-equal');
const uniq = require('uniq');
const { flatten } = require('array-flatten');

const parsers = {
    expressRoutes: require('./source-parsers/core/express-routes.js'),
    cloudFunction: require('./source-parsers/core/cloud-functions.js'),
    directInvocation: require('./source-parsers/core/direct-invocation.js'),
    wrappedMain: require('./source-parsers/extra/wrapped-main.js'),
    wrappedDirectInvocation: require('./source-parsers/extra/wrapped-direct-invocation.js')
};

const getMethodChildren = (method) => {
    if (!(method instanceof Object)) {
        return [];
    }

    let children = [];
    if (method.callee && method.callee.name) {
        children.push(method.callee.name);
    }

    const props = Object.keys(method);
    props.forEach((key) => {
        if (key === 'loc' || !method[key]) {
            return;
        }

        const value = method[key];
        if (Array.isArray(value)) {
            const newChildren = value.map(x => getMethodChildren(x))
            children = children.concat(flatten(newChildren));
        } else {
            children = children.concat(getMethodChildren(value));
        }
    })

    return children;
}

exports.getTopLevelMethods = (sourceTokens, sourcePath) => {
    const expressMethods = parsers.expressRoutes.parse(sourceTokens, sourcePath);
    const gcfMethods = parsers.cloudFunction.parse(sourceTokens, sourcePath);
    const snippetMethods = parsers.directInvocation.parse(sourceTokens, sourcePath);
    const wrappedMainMethods = parsers.wrappedMain.parse(sourceTokens, sourcePath);
    const wrappedDirectInvocationMethods = parsers.wrappedDirectInvocation.parse(sourceTokens, sourcePath);
    let allMethods = [
        ...snippetMethods, 
        ...expressMethods, 
        ...gcfMethods, 
        ...wrappedMainMethods,
        ...wrappedDirectInvocationMethods];

    // Remove duplicate methods
    allMethods = uniq(allMethods, (x, y) => deepEqual(x, y) ? 0 : 1);

    // Add (top-level) method children
    const allMethodNames = allMethods.map(m => m.drift.methodName || m.drift.functionName);
    allMethods.forEach(m => {
        m.drift.children = getMethodChildren(m).filter(c => allMethodNames.includes(c));
    })

    return allMethods;
}

exports.getRegionTagRegions = (sourceTokens) => {
    let startTags = sourceTokens.comments.filter(t => t.value.includes('[START'))
    let endTags = sourceTokens.comments.filter(t => t.value.includes('[END'))

    // Map to regions
    const regions = [];
    for (let i = 0; i < startTags.length; i++) {
        const tag = startTags[i].value.split(' ').slice(-1)[0].slice(0, -1)

        const start = startTags[i].loc.start.line
        const end = endTags[i].loc.start.line

        regions.push({tag, start, end});
    }

    return regions;
}

exports.getCliCommands = (sourceTokens) => {
    // ASSUMPTION: CLI statement is an expression at the end of the file
    let cliStatement;
    cliStatement = sourceTokens.body
        .filter(t => t.type === 'ExpressionStatement' || t.type === 'VariableDeclaration')
        .slice(-1)[0]
    if (cliStatement.declarations) {
        cliStatement = cliStatement.declarations[0].init;
    }

    let cmdExpression = cliStatement.expression || cliStatement.callee;
    if (!cmdExpression) {
        return {};  // No CLI command expression found
    } else if (cmdExpression.object) {
        cmdExpression = cmdExpression.object;
    }

    // Skip non-"command" functions ("example", "help", etc.)
    while (cmdExpression.callee &&
           cmdExpression.callee.property &&
           cmdExpression.callee.property.name !== 'command') {
        cmdExpression = cmdExpression.callee.object;
    }

    const cliCommands = {};

    // ASSUMPTION: all 'command' calls are in a contiguous
    //             block with no other lines separating them
    while (cmdExpression.callee &&
           cmdExpression.callee.property &&
           cmdExpression.callee.property.name === 'command') {
        const [methodCall] = cmdExpression.arguments.slice(-1);

        // ASSUMPTION: CLI statement is only one space-separated command deep
        //   OK  - node example.js command arg
        //   BAD - node example.js command subcommand arg



        let cliInvocation = cmdExpression.arguments[0];
        if (cliInvocation.quasis) {
            cliInvocation = cliInvocation.quasis[0].value.raw;
        } else {
            cliInvocation = cliInvocation.value;
        }
        cliInvocation = cliInvocation.split(' ')[0];

        if (methodCall.body &&
            methodCall.body.callee &&
            methodCall.body.callee.name) {
            cliCommands[methodCall.body.callee.name] = cliInvocation;
        }

        cmdExpression = cmdExpression.callee.object;
    }
    return cliCommands;
}

exports.addRegionTagsToMethods = (methods, regionTags) => {
    methods.forEach(method => {
        const m = {
            start: method.loc.start.line,
            end: method.loc.end.line,
        }

        const methodRegionTags = regionTags.filter(r => 
            (r.start < m.start && m.end < r.end) ||
            (m.start < r.start && r.end < m.end)
        ).map(r => r.tag)

        method.drift.regionTags = methodRegionTags
    })
}

exports.addCliCommandsToMethods = (methods, cliCommands) => {
    methods.forEach(method => {
        const methodName = method.id && method.id.name;
        if (methodName && cliCommands[methodName]) {
            method.drift.cliInvocation = cliCommands[methodName];
        }
    })
}
