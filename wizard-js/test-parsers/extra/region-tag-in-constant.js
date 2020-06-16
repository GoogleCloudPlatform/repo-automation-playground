'use strict';

const execSyncParser = require('../core/exec-sync.js');

exports.parse = (
    testStatements, 
    commandToDescribeMap, 
    describeChain, 
    testPaths, 
    topLevelRegionTag
) => {
    execSyncParser.parse(testStatements, commandToDescribeMap, describeChain, testPaths);
    return;
    // Get properties for the specified region tag
    const describeElements = commandToDescribeMap
        .filter(x => x.describeChain.includes(topLevelRegionTag))

    const describeChains = describeElements.map(x => x.describeChain);
    const describePaths = describeElements.map(x => x.testPaths)

    // Concatenate relevant properties together

    console.log('DEC', describeChains);
}
