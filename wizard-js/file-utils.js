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
