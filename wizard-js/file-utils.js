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

const fs = require('fs');
const path = require('path');
const execa = require('execa');
const uniq = require('uniq');

const { REGION_TAG_GREP_ARGS } = require('./constants');

const __getFiles = (dir, predicate) => {
    let paths = fs.readdirSync(dir, { withFileTypes: true });
    const folders = paths.filter(p => p.isDirectory() && p.name !== 'node_modules');
    
    let files = paths
        .filter(predicate)
        .map(p => path.join(dir, p.name));
    folders.forEach(f => {
        const subdir = path.join(dir, f.name);
        files = files.concat(__getFiles(subdir, predicate));
    })

    return files || [];
}

const getNodeJsFiles = (dir) => {
    return __getFiles(dir, p => !p.name.startsWith('.') && p.name.endsWith('.js'))
}

const getYamlFiles = (dir) => {
    return __getFiles(dir, p => p.name === '.drift-data.yml')
}

const getRegionTags = async (dir) => {
    const {stdout} = await execa('grep', [...REGION_TAG_GREP_ARGS, dir], {shell: true});
    const regionTags = uniq(stdout.split('\n').map(x => x.trim().slice(10, -1)));
    
    return regionTags;
}

exports.getNodeJsFiles = getNodeJsFiles;
exports.getYamlFiles = getYamlFiles;
exports.getRegionTags = getRegionTags;
