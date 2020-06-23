'use strict';

const { EXPRESS_METHOD_NAMES } = require('../../constants')

exports.parse = (sourceTokens, sourcePath) => {
    const expressMethods = sourceTokens.body
        .filter(f => f.type === 'ExpressionStatement' && f.expression.callee)
        .map(f => f.expression)
        .filter(f => EXPRESS_METHOD_NAMES.includes(f.callee.property && f.callee.property.name))

    expressMethods.forEach(method => {
        method.drift = {
            httpMethod: method.callee.property.name,
            urlPath: method.arguments[0].value,
            sourcePath
        }
    });

    return expressMethods;
}
