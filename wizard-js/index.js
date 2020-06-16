'use strict';

const esprima = require('esprima');
const fs = require('fs');
const path = require('path');
const uniq = require('uniq');
const chalk = require('chalk');
const xml2json = require('xml2js').parseStringPromise;
const getStdin = require('get-stdin');

const testParser = require('./test-parser');
const testParserMisc = {
    fileWideInvocation: require('./test-parsers/core-misc/file-wide-invocation.js'),
    topLevelRegionTags: require('./test-parsers/core-misc/top-level-region-tag.js')
};

const sourceParser = require('./source-parser');
const fileUtils = require('./file-utils');

const parseSource = (sourcePath) => {
    const sourceProgram = fs.readFileSync(sourcePath).toString();
    const sourceTokens = esprima.parse(sourceProgram, { comment: true, loc: true })

    const methods = sourceParser.getTopLevelMethods(sourceTokens, sourcePath);
    const regionTags = sourceParser.getRegionTagRegions(sourceTokens);

    const cliCommands = sourceParser.getCliCommands(sourceTokens);

    sourceParser.addRegionTagsToMethods(methods, regionTags);
    sourceParser.addCliCommandsToMethods(methods, cliCommands);

    return methods;
};

const parseTest = (testPath, sourceMethods) => {
    const testProgram = fs.readFileSync(testPath).toString();
    const testTokens = esprima.parse(testProgram, { comment: true, loc: true })

    let describeClauses = testParser.getDescribeClauses(testTokens)
    if (describeClauses.length === 0) {
        // all 'it' clauses
        describeClauses = testTokens.body;
    }

    // Handle single-test, global-invocation files
    let fileWideInvocation;
    if (Object.values(describeClauses).length === 1) {
        fileWideInvocation = testParserMisc.fileWideInvocation(testTokens);  // for single-test test files
    }

    // Handle global region tags within tests
    const [topLevelRegionTag] = testParserMisc.topLevelRegionTags(testTokens);

    const describeChainMap = testParser.getDescribeChainMap(
        describeClauses,
        testPath,
        topLevelRegionTag);

    testParser.addDescribeChainToMethods(testPath, sourceMethods, describeChainMap, fileWideInvocation)
};

const analyzeDir = async (rootDir) => {
    const ALL_PATHS = fileUtils.getNodeJsFiles(rootDir);

    const SOURCE_PATHS = ALL_PATHS.filter(x => !x.includes('.test.'));
    const TEST_PATHS = ALL_PATHS.filter(x => x.includes('.test.'));

    let sourceMethods = [];
    SOURCE_PATHS.forEach(path => {
        sourceMethods = sourceMethods.concat(parseSource(path));
    });

    TEST_PATHS.forEach(path => {
        parseTest(path, sourceMethods);
    });

    let scriptRegionTags = [];
    sourceMethods.forEach(x => scriptRegionTags = scriptRegionTags.concat(x.drift.regionTags))
    scriptRegionTags = uniq(scriptRegionTags);

    let grepRegionTags = await fileUtils.getRegionTags(rootDir)

    return {
        grepRegionTags, scriptRegionTags, sourceMethods
    }
}
// '/Users/anassri/Desktop/nodejs-translate/samples'
require('yargs')
    .demand(1)
    .command(
        'list-region-tags <path>',
        'Lists region tags in a file or directory.',
        {
            tested: {
              alias: 't',
              type: 'boolean',
              default: 'true',
              requiresArg: true,
              description: 'Whether or not to display tested region tags',
            },
            untested: {
              alias: 'u',
              type: 'boolean',
              default: 'true',
              requiresArg: true,
              description: 'Whether or not to display un-tested region tags',
            },
            showFilenames: {
                alias: 'f',
                type: 'boolean',
                default: false,
                requiresArg: true,
                description: ''
            }
        },
        async opts => {
            const {sourceMethods, scriptRegionTags, grepRegionTags} = await analyzeDir(opts.path)

            if (opts.tested) {
                console.log(chalk.bold(`-- ${chalk.green('Tested')} region tags: --`))
                scriptRegionTags.forEach(t => {
                    let filename;
                    if (opts.showFilenames) {
                        filename = sourceMethods.filter(x => x.drift.regionTags.includes(t)).sourcePath;
                    } else {
                        console.log(t);
                    }
                })
            }

            if (opts.untested) {
                console.log(chalk.bold(`-- ${chalk.red('Untested')} region tags: --`))
                grepRegionTags.filter(t => !scriptRegionTags.includes(t)).forEach(t => {
                    console.log(t);
                })
            }
        }
    )
    .command(
        'list-source-files <path>',
        'Lists snippet source file paths in a file or directory.',
        {
            testedMethods: {
              alias: 't',
              type: 'string',
              default: '*',
              requiresArg: true,
              choices: ['all', 'some', 'none', '*'],
              description: 'Display files where ({all, some, no}) methods are tested)',
            },
        },
        async opts => {
            let {sourceMethods, grepRegionTags, scriptRegionTags} = await analyzeDir(opts.path)

            if (opts.testedMethods === 'all') {
                sourceMethods = sourceMethods.filter(x => x => x.drift.testData.some(y => 
                    y.testPaths.length > 0
                )); 

                const tagsMissed = grepRegionTags.filter(t => !scriptRegionTags.includes(t));
                sourceMethods = sourceMethods.filter(m => {
                    return m.drift.regionTags.some(x => tagsMissed.includes(x));
                });
            }

            if (opts.testedMethods === 'some') {
                sourceMethods = sourceMethods.filter(x => x.drift.testData.some(y => 
                    y.testPaths.length > 0
                )); 
            }

            uniq(sourceMethods.map(x => x.drift.sourcePath)).forEach(x => console.log(x))
        }
    )
    .command(
        'inject-snippet-mapping <rootDir>',
        'Adds snippet mapping to XUnit output',
        {},
        async opts => {
            const xunitInput = await getStdin();
            const xunitJson = await xml2json(xunitInput);

            const testCases = xunitJson.testsuite.testcase;
            testCases.forEach(outer => {
                const inner = outer['$'];
                inner.fullName = `${inner.classname}:${inner.name}`;
            });

            let {sourceMethods, grepRegionTags, scriptRegionTags} = await analyzeDir(opts.rootDir)

            const testedMethods = sourceMethods.map(x => x.drift).filter(x => x.testData.length > 0);

            // Build test-to-region-tag map + inject it into XUnit output
            let xunitOutput = xunitInput;
            testCases.forEach(xunitTest => {
                const testChain = xunitTest['$'].fullName;

                const [testMethod] = testedMethods.filter(m => {
                    const methodChains = m.testData.map(x => x.describeChain.join(":"))
                    return methodChains.includes(testChain);
                });

                if (testMethod) {
                    testMethod.regionTags.forEach(tag => {
                        let testChainReplaceStr = testChain.split(':').slice(1).join(':')
                        testChainReplaceStr = `name="${testChainReplaceStr}"`

                        const regionTagStr = testMethod.regionTags.join(',');

                        xunitOutput = xunitOutput.replace(
                            testChainReplaceStr,
                            testChainReplaceStr + ` customProperty="${regionTagStr}"`
                        )
                    })
                }
            })

            console.log(xunitOutput)
        }
    )
    .recommendCommands()
    .help()
    .strict().argv
