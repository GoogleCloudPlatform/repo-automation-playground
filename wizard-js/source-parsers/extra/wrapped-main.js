'use strict';

exports.parse = (sourceTokens, sourcePath) => {
    let mainMethods = sourceTokens.body.map(x => x.declarations && x.declarations[0] || x);
    mainMethods = mainMethods.filter(f => f.id && f.id.name && f.id.name === 'main');

    mainMethods = mainMethods.map(f => {
        if (f.id.name === 'main') {  // HACK: some samples (e.g. nodejs-vision) wrap sample in a "main" method
            const subexpressions = (f.init || f).body.body.filter(x => x.id && x.id.name);
            if (subexpressions.length === 1) {
                return subexpressions[0];
            } else if (subexpressions.length > 1) {
                // main() methods should not have multiple subexpressions
                // (some files do though, and are handled by other parsers!)
                return null; 
            }
        }
        return f;
    }).filter(f => f);

    mainMethods.forEach(m => m.drift = {
        methodName: m.id.name,
        name: m.id.name,
        sourcePath
    });

    return mainMethods;
}
