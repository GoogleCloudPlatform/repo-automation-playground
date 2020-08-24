// Copyright 2020 Google LLC. All Rights Reserved.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

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
const yamlUtils = require('./yaml-utils');

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

    let grepRegionTags = await fileUtils.getRegionTags(rootDir)

    let ignoredRegionTags = yamlUtils.getUntestedRegionTags(rootDir);

    yamlUtils.addYamlDataToSourceMethods(sourceMethods, rootDir);

    // Compute final script region tags (including YAML aliases)
    let scriptRegionTags = [];
    sourceMethods.forEach(x => scriptRegionTags = scriptRegionTags.concat(x.drift.regionTags))
    scriptRegionTags = uniq(scriptRegionTags);

    return {
        grepRegionTags, scriptRegionTags, sourceMethods, ignoredRegionTags
    }
}
// '/Users/anassri/Desktop/nodejs-translate/samples'
require('yargs')
    .demand(1)
    .command(
        'list-region-tags <path>',
        'Lists region tags in a file or directory.',
        {
            detected: {
              alias: 'd',
              type: 'boolean',
              default: 'true',
              requiresArg: true,
              description: 'Display region tags detected by the AST parser',
            },
            undetected: {
              alias: 'u',
              type: 'boolean',
              default: 'true',
              requiresArg: true,
              description: 'Display region tags NOT detected by the AST parser',
            },
            showTestCounts: {
                alias: 'c',
                type: 'boolean',
                default: false,
                description: 'Show test counts for each region tag',
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
            const {sourceMethods, scriptRegionTags, grepRegionTags, ignoredRegionTags} = await analyzeDir(opts.path)

            const getTestCounts = (regionTag) => {
                const testDataMatches = sourceMethods
                    .filter(x => x.drift.regionTags.includes(regionTag))
                    .map(x => x.drift.testData)
                    .reduce((x, acc) => acc = acc.concat(x));

                return testDataMatches.length;
            }

            if (opts.detected) {
                console.log(chalk.bold(`-- ${chalk.green('Detected')} region tags: --`))
                scriptRegionTags.forEach(t => {
                    let outputStr = t;

                    let filename;

                    if (opts.showTestCounts) {
                        outputStr += ` (${getTestCounts(t) || chalk.red('0')} test set(s))`;
                    }

                    if (opts.showFilenames) {
                        filename = sourceMethods.filter(x => x.drift.regionTags.includes(t)).sourcePath;
                        outputStr += ` (Test path: ${chalk.bold(filename)})`
                    }

                    console.log(outputStr);
                })
            }

            if (opts.undetected) {
                console.log(chalk.bold(`-- ${chalk.red('Undetected')} region tags: --`))
                grepRegionTags
                    .filter(t => !scriptRegionTags.includes(t))
                    .filter(t => !ignoredRegionTags.includes(t))
                    .forEach(t => console.log(t));
            }

            if (ignoredRegionTags.length > 0) {
                console.log(chalk.bold(`-- ${chalk.yellow('Ignored')} region tags: --`))
                ignoredRegionTags.forEach(t => console.log(t));
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

            // Warn if some tests weren't labeled
            const xunitOutputParsed = await xml2json(xunitOutput);
            const unlabeledTests = xunitOutputParsed.testsuite.testcase.filter(x => !x['$'].customProperty);
            if (unlabeledTests.length > 0) {
                console.log(`The following tests have ${chalk.bold('no associated region tags:')}`);
                unlabeledTests.forEach(t => {
                    console.log(`  ${t['$'].classname}:${t['$'].name}`)
                })
            }
            console.log(xunitOutput)
        }
    )
    .command(
        'validate-yaml <rootDir>',
        'Validates .drift-data.yml files in a directory',
        {},
        async opts => {
            const {sourceMethods, grepRegionTags, scriptRegionTags} = await analyzeDir(opts.rootDir);

            if (yamlUtils.validateYamlSyntax(opts.rootDir, grepRegionTags)) {
                console.log(`Yaml files valid!`);
            } else {
                console.log(`Yaml files ${chalk.bold('not')} valid!`);
            }
        }
    )
    .recommendCommands()
    .help()
    .strict().argv
