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

'use strict'

const uniq = require('uniq');
const fs = require('fs');
const yaml = require('yaml');
const chalk = require('chalk');
const fileUtils = require('./file-utils.js');

exports.getUntestedRegionTags = (rootDir) => {
    const yamlPaths = fileUtils.getYamlFiles(rootDir);
    let allUntestedTags = [];

    yamlPaths.forEach(path => {
        const yamlContents = fs.readFileSync(path).toString();
        const parsedYaml = yaml.parse(yamlContents) || {};

        const localUntestedTags = Object.keys(parsedYaml).filter(k => parsedYaml[k].tested === false)
        allUntestedTags = allUntestedTags.concat(localUntestedTags);
    })

    return uniq(allUntestedTags);
}

const _handleAliasedRegionTags = (sourceMethods, rootDir) => {
    const yamlPaths = fileUtils.getYamlFiles(rootDir);

    // Build alias'ed tag map
    let aliasedTagMap = {};
    yamlPaths.forEach(path => {
        const yamlContents = fs.readFileSync(path).toString();
        const parsedYaml = yaml.parse(yamlContents) || {};

        const rootTags = Object.keys(parsedYaml).filter(
            k => Array.isArray(parsedYaml[k].aliases));
        rootTags.forEach(rootTag => {
            const parsedJson = JSON.stringify(parsedYaml[rootTag]);
            parsedYaml[rootTag].aliases.forEach(aliasTag => {
                aliasedTagMap[aliasTag] = rootTag;
            })
        })
    })

    // Apply aliases
    sourceMethods.forEach(m => {
        let allRegionTags = m.drift.regionTags;
        m.drift.regionTags.forEach(tag => {
            allRegionTags = allRegionTags.concat(aliasedTagMap[tag] || [])
        })
        m.drift.regionTags = uniq(allRegionTags);
    });
}

const _handleManuallySpecifiedTests = (sourceMethods, rootDir) => {
    const yamlPaths = fileUtils.getYamlFiles(rootDir);

    yamlPaths.forEach(path => {
        const yamlContents = fs.readFileSync(path).toString();
        let parsedYaml = yaml.parse(yamlContents) || {};
        
        const testDataMap = {};
        Object.keys(parsedYaml).forEach(keyTag => {
            let testDataObjs = Object.values(parsedYaml[keyTag])
                .map(comment => Object.values(comment))
                .reduce((x, arr) => arr.concat(x))
                .filter(x => x.describeChain) // filter out 'alias' lines

            testDataMap[keyTag] = (testDataMap[keyTag] || []).concat(testDataObjs)
        })

        Object.keys(parsedYaml).forEach(regionTag => {
            const matchingMethods = sourceMethods.filter(m => m.drift.regionTags.includes(regionTag));

            if (matchingMethods.length > 0) {
                matchingMethods.forEach(m => {
                    m.drift.testData = m.drift.testData.concat(testDataMap[regionTag]);
                });
            } else {
                throw new Error(
                    `Tag ${regionTag} in file ${path} doesn't map to a snippet method!`)
            }
        })
    })
}

exports.validateYamlSyntax = (rootDir, grepRegionTags) => {
    let isValid = true;
    const yamlPaths = fileUtils.getYamlFiles(rootDir);

    yamlPaths.forEach(path => {
        const yamlContents = fs.readFileSync(path).toString();
        let parsedYaml = yaml.parse(yamlContents) || {};
        const yamlKeys = Object.keys(parsedYaml);

        // Verify all mentioned region tags exist in source code
        let invalidRegionTags = yamlKeys.filter(t => !grepRegionTags.includes(t));
        if (invalidRegionTags.length) {
            console.log(`Yaml file ${chalk.bold(path)} contains unused region tags:`)
            invalidRegionTags.forEach(t => console.log(`  ${t}`));
            isValid = false;
        }

        // Verify YAML entries have the correct layout
        yamlKeys.forEach(key => {
            const value = parsedYaml[key];

            if (value.tested === false) {
                return; // valid 'tested' switch
            } else if (value.tested) {
                console.log(`Invalid 'tested' setting for ${chalk.bold(key)} in yaml file ${chalk.bold(path)}!`)
                console.log(`  (Must be either ${chalk.bold('false')} or omitted entirely.)`)
                isValid = false;
                return;
            }

            if (Array.isArray(value.aliases) &&
                value.aliases.every(a => grepRegionTags.includes(a))) {
                return; // valid aliasing
            } else if (value.aliases) {
                console.log(`Invalid aliases for ${chalk.bold(key)} in yaml file ${chalk.bold(path)}!`)
                isValid = false;
                return;
            }
 
            const subvaluesAreValid = Object.values(value).every(subValues => {
                return Object.values(subValues).every(subValue => {
                    return Array.isArray(subValue.describeChain) &&
                           Array.isArray(subValue.testPaths);
                });
            });
            if (subvaluesAreValid) {
                return; // valid manually-specified test
            }

            // YAML entry is invalid
            console.log(`Yaml file ${path} contains badly-formatted entry: ${key}`);
            isValid = false;
        })
    })

    return isValid;
}

exports.addYamlDataToSourceMethods = (sourceMethods, rootDir) => {
    const yamlPaths = fileUtils.getYamlFiles(rootDir);

    _handleAliasedRegionTags(sourceMethods, rootDir);
    _handleManuallySpecifiedTests(sourceMethods, rootDir);
}


