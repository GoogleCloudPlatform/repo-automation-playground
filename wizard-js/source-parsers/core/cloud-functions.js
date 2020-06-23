'use strict';

exports.parse = (sourceTokens, sourcePath) => {
    const gcfMethods = sourceTokens.body
        .filter(f => f.type === 'ExpressionStatement' && f.expression.type === 'AssignmentExpression')
        .map(f => f.expression)
        .filter(f => f.left.object.name === 'exports')
    gcfMethods.forEach(m => {
        m.drift = {
            functionName: m.left.property.name,
            name: m.left.property.name,
            sourcePath
        }
    });
    return gcfMethods;
}
