'use strict';

exports.parse = (sourceTokens, sourcePath) => {
    let snippetMethods = sourceTokens.body.map(x => x.declarations && x.declarations[0] || x);
    snippetMethods = snippetMethods.filter(f => f.id && f.id.name && f.id.name !== 'main');
    snippetMethods = snippetMethods.filter(f => !f.init || f.init.type === 'ArrowFunctionExpression')

    snippetMethods.forEach(m => m.drift = {
        methodName: m.id.name,
        name: m.id.name,
        sourcePath
    });

    return snippetMethods;
}
