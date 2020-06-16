const fs = require('fs');
const path = require('path');
const execa = require('execa');
const uniq = require('uniq');

const { REGION_TAG_GREP_ARGS } = require('./constants');

const getNodeJsFiles = (dir) => {
    let paths = fs.readdirSync(dir, { withFileTypes: true });
    const folders = paths.filter(p => p.isDirectory() && p.name !== 'node_modules');
    
    let nodeFiles = paths
        .filter(p => !p.name.startsWith('.') && p.name.endsWith('.js'))
        .map(p => path.join(dir, p.name));
    folders.forEach(f => {
        nodeFiles = nodeFiles.concat(getNodeJsFiles(path.join(dir, f.name)));
    })

    return nodeFiles;
}

const getRegionTags = async (dir) => {
    const {stdout} = await execa('grep', [...REGION_TAG_GREP_ARGS, dir], {shell: true});
    const regionTags = uniq(stdout.split('\n').map(x => x.trim().slice(10, -1)));
    
    return regionTags;
}

exports.getNodeJsFiles = getNodeJsFiles;
exports.getRegionTags = getRegionTags;
