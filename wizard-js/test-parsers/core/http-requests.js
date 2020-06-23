'use strict';

const  { EXPRESS_METHOD_NAMES } = require('../../constants')

exports.parse = (testStatements, commandToDescribeMap, describeChain, testPaths) => {
    // HTTP request tests
    testStatements.forEach(statement => {
        if (statement.type === 'ExpressionStatement') {
            let httpMethodStmt = statement.expression.argument && statement.expression.argument.callee;

            while (httpMethodStmt && httpMethodStmt.object && httpMethodStmt.object.callee) {
                const httpMethod = httpMethodStmt.object.callee.property &&
                                   httpMethodStmt.object.callee.property.name.toLowerCase();
                let httpRoute = httpMethodStmt.object.arguments[0];
                httpRoute = typeof httpRoute.value === 'string' && httpRoute.value.toLowerCase();

                if (!httpRoute) {
                    return;
                }

                // TODO: disambiguate between snippets with the same URL
                // e.g. separate POST requests
                if (EXPRESS_METHOD_NAMES.includes(httpMethod)) {
                    commandToDescribeMap[httpRoute] = commandToDescribeMap[httpRoute] || {};
                    commandToDescribeMap[httpRoute][httpMethod] = commandToDescribeMap[httpRoute][httpMethod] || [];
                    commandToDescribeMap[httpRoute][httpMethod].push({
                        describeChain,
                        testPaths
                    });
                }

                httpMethodStmt = httpMethodStmt.object.callee;
            }
        }
    });
}
