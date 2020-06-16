'use strict';

const directInvocation = require('../core/direct-invocation.js');

exports.parse = (sourceTokens, sourcePath) => {
    const [mainMethodContents] = sourceTokens.body.filter(x => x.type === 'FunctionDeclaration')
    if (mainMethodContents) {
        return directInvocation.parse(mainMethodContents.body, sourcePath);
    } else {
        return [];
    }
}
