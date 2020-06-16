'use strict'

exports.parse = (testStatements, commandToDescribeMap, describeChain, testPaths) => {
    // Direct/Mocked method invocation tests
    testStatements.forEach(statement => {
        const base = (statement.expression && statement.expression.argument) || statement.expression;
        if (base && base.callee) {
            const callee = base.callee;
            const methodName = callee.name || callee.property.name;

            const key = methodName.toLowerCase();
            if (methodName) {
                commandToDescribeMap[key] = (commandToDescribeMap[key] || []);
                commandToDescribeMap[key].push({ describeChain, testPaths });
            }
        };
    });
};
