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

'use strict'

exports.parse = (testStatements, commandToDescribeMap, describeChain, testPaths) => {
    // GCF Functions Framework tests (HTTP requests)
    // TODO this will NOT detect URLs that are part of template strings,
    //      or those specified as a "url" property
    //      (those will likely require recursion, or simply throw an error)`
    testStatements.forEach(statement => {
        if (statement.type === 'VariableDeclaration') {
            const httpInvocationExpr = statement.declarations[0].init;
            let httpFunctionUrls = httpInvocationExpr.argument
                && httpInvocationExpr.argument.arguments
                && httpInvocationExpr.argument.arguments[0];

            // Handle template strings and objects
            if (httpFunctionUrls && httpFunctionUrls.type === 'TemplateLiteral') {
                httpFunctionUrls = httpFunctionUrls.quasis;
            }

            if (httpFunctionUrls && Array.isArray(httpFunctionUrls)) {
                httpFunctionUrls = httpFunctionUrls
                    .filter(x => x.value && x.value.raw !== '')
                    .map(x => x.value.raw || x.value)
                    .map(x => x.split('?')[0].replace(/(^\/)|(\/$)/g, ''));

                httpFunctionUrls.forEach(url => {
                    const key = url.toLowerCase;
                    commandToDescribeMap[key] = commandToDescribeMap[key] || [];
                    commandToDescribeMap[key].push({
                        describeChain,
                        testPaths
                    })
                });
            }
        }
    })
}
