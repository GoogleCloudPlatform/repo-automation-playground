// Initial cmd: mocha --reporter=xunit --reporter-option="output: test.xml"

// nyc --all --reporter=lcov mocha

const path = require('path');
const fs = require('fs');
const xpathJs = require('xpath.js');
const {DOMParser} = require('xmldom');
const slugify = require('slugify');
const delay = require('delay');
const uniq = require('uniq');
const execPromise = require('child-process-promise').exec;
const chalk = require('chalk');

const queryXmlFile = (filename, xpath) => {
	const fileContents = fs.readFileSync(filename, 'utf-8');
	const doc = new DOMParser().parseFromString(fileContents)    
	const nodes = xpathJs(doc, xpath)
	return nodes.map(n => n.value)
}

// Constants
const generateAndLinkToCloverReports = async (baseDir, allTestsXml) => {
	let testFilters = queryXmlFile(allTestsXml, '//testcase/@name')
	testFilters = testFilters
		.filter(x => !x.includes('" hook '))
		.map(x => x.replace(/\"/g,'\\\"').replace(/'/,"\'"))

	let testFilterDirs = testFilters.map(x => slugify(x).toLowerCase())
	for (const bannedChar of [/:/g, /\'/g, /"/g]) {
		testFilterDirs = testFilterDirs.map(dir => dir.replace(bannedChar, ''));
	}

	let nycCmds = []
	for (let i = 0; i < testFilters.length; i++) {
		// Skip dirs that exist
		if (fs.existsSync(path.join(baseDir, `test-${testFilterDirs[i]}`))) {
			//continue;
		}

		nycCmds.push(`${chalk.red.bold('nyc')} --all --reporter=clover --report-dir="test-${testFilterDirs[i]}" ${chalk.green.bold('mocha')} --grep "${testFilters[i]}" --timeout 20000 --exit`);
	}

	console.log(chalk.bold('Execute these commands manually + ensure tests pass...'))
	for (const cmd of nycCmds) {
		try {
			console.log(`  ${chalk.cyan.bold('cd')} ${baseDir} && ${cmd}`)
			//await delay(500);
			//await execPromise(cmd, {cwd: baseDir});
			//await delay(500); // avoid NYC race conditions
		} catch (e) {
			/* swallow test errors */
			//console.error('ERROR', e)
			//await delay(500);
		}
	}
	
	return {testFilters, testFilterDirs}
}
	
const _getMatchingLineNums = (sourceLines, predicate) => {
	// "lineNum + 1" makes lines 1-indexed (consistent with Clover reports)
	return sourceLines.map((line, lineNum) => predicate(line, lineNum) && (lineNum + 1))
				  .filter(x => x)
				  .sort((x, y) => x - y);
}

const _findCoveredCodeLines = (sourcePath, cloverReportPath) => {
	// Find valid code lines (non-top-level ones)
	const sourceLines = fs.readFileSync(sourcePath, 'utf-8').split('\n');
	const sourceLineNums = _getMatchingLineNums(sourceLines, line => line.startsWith('  '))

	// Find lines covered in Clover report
	const cloverLines = queryXmlFile(cloverReportPath, '//line[not(@count = \'0\')]/@num').map(x => parseInt(x))
	if (cloverLines.length == 0) {
		console.log(chalk.red('ERR') + 'Bad Clover output, ensure test passes: ' + chalk.bold(cloverReportPath));
		return []
	}

	// Find intersection of (covered lines, valid code lines)
	const coveredCodeLines = cloverLines
		.filter(line => sourceLineNums.includes(line))
		.sort((x, y) => x - y);

	return coveredCodeLines;
}

const _findRegionTagsAndRanges = (sourcePath) => {
	const sourceLines = fs.readFileSync(sourcePath, 'utf-8').split('\n');

	// Find region tag blocks
	const startRegionTagLines = _getMatchingLineNums(sourceLines, line => line.includes('[START '))
	const endRegionTagLines = _getMatchingLineNums(sourceLines, line => line.includes('[END '))

	// Map region tags to method invocations
	const regionTagRanges = startRegionTagLines.map((start, idx) => [start, endRegionTagLines[idx]]);
	const regionTagsAndRanges = regionTagRanges.map(range => {
		let tag = sourceLines[range[0] - 1]
		tag = tag.substring(tag.indexOf('START') + 6).replace(']', '')

		const out = {}
		out[tag] = range;
		return out;
	});
	return regionTagsAndRanges
}

const getRegionTagsForTest = (cloverReportPath) => {
	const sourcePath = queryXmlFile(cloverReportPath, '//file/@path').filter(x => !x.includes('loadable'))[0];
	const sourceLines = fs.readFileSync(sourcePath, 'utf-8').split('\n');

	const coveredCodeLines = _findCoveredCodeLines(sourcePath, cloverReportPath);
	const regionTagsAndRanges = _findRegionTagsAndRanges(sourcePath)

	const hitRegionTags = regionTagsAndRanges.filter(tagAndRange => {
		const tag = Object.keys(tagAndRange)[0]
		const range = Object.values(tagAndRange)[0]
		return coveredCodeLines.some(codeLine => range[0] <= codeLine && codeLine <= range[1])
	})

	return hitRegionTags;
}

const _grep = async (term, path) => {
	const {stdout} = await execPromise(`grep -nri "${term}" ${path}`);
	const [filepath, lineNum] = stdout.split(':');
	await delay(10); // Avoid exec issues with grep
	return {filepath, lineNum}
}

const __numSpaces = (x) => (x.match(/^\s+/g) || [''])[0].length;

const _findClosingParenthesis = (sourceLines, startLineNum) => {
	const startLine = sourceLines[startLineNum - 1];

	return _getMatchingLineNums(sourceLines, (line, lineNum) => {
		return line.endsWith('});') && startLineNum < lineNum && __numSpaces(line) === __numSpaces(startLine)
	}).sort((x, y) => x - y)[0]
}

const _findPrecedingParenthesis = (sourceLines, startLineNum) => {
	const startLine = sourceLines[startLineNum - 1];

	const lineNums = _getMatchingLineNums(sourceLines, (line, lineNum) => {
		return line.endsWith('});') && startLineNum > lineNum && __numSpaces(line) === __numSpaces(startLine)
	}).sort((x, y) => x - y);
	return lineNums[lineNums.length - 1];
}

const wrapIndividualTestInRegionTag = async (baseDir, testFilterName, cloverReportPath, regionTag) => {
	const testPath = (await _grep(testFilterName, path.join(baseDir, '*est'))).filepath;
	const testLines = fs.readFileSync(testPath, 'utf-8').split('\n');

	// Detect test starting line (and check for existing region tag)
	const regionTagStartLine = `describe('${regionTag}', () => {`;
	const testStartLineNum = _getMatchingLineNums(testLines, line => line.includes(testFilterName))
	const testStartLine = testLines[testStartLineNum - 1];

	let describeLine = testStartLineNum - 2;
	while (describeLine > 0 && testLines[describeLine].match(/(describe|it)\(/)) {
		if (testLines[describeLine].endsWith(regionTagStartLine)) {
			return; // Desired region tag already present
		}
		describeLine -= 1;
	}

	// Add end line (closing brackets)
	const testEndLine = _findClosingParenthesis(testLines, testStartLineNum)
	testLines.splice(testEndLine, 0, `});`)

	// Add start line (describe(...)) if necessary
	testLines.splice(testStartLineNum - 1, 0, regionTagStartLine)

	// Save to file
	const output = testLines.join('\n');
	fs.writeFileSync(testPath, output);
}

const generateTestList = async (baseDir) => {
	await execPromise(`mocha --reporter xunit > all-tests.xml`, {cwd: baseDir});
}

// ASSUMPTION: all repeats of a region tag are contiguous
const perDirMain = async (baseDir) => {
	console.log(`--------------------`)
	const allTestsXml = path.join(baseDir, 'all-tests.xml')
	if (!fs.existsSync(allTestsXml)) {
		//console.log(`Generating test list in: ${baseDir}`);
		await generateTestList(baseDir);
		return;
	}

	console.log(`Generating Clover reports in: ${chalk.bold(baseDir)}`)
	const {testFilters, testFilterDirs} = await generateAndLinkToCloverReports(baseDir, allTestsXml);

	const testPaths = [];

	// Wrap region tags
	console.log(`--------------------`)
	for (let i = 0; i < testFilters.length; i++) {
		const testFilter = testFilters[i];
		const testFilterDir = testFilterDirs[i];
		const cloverReportPath = path.join(baseDir, `test-${testFilterDir}/clover.xml`)

		const tags = await getRegionTagsForTest(cloverReportPath)
		const tagString = uniq(tags.map(tag => Object.keys(tag)).sort(), true).join(' ')

		if (tags.length != 0) {
			console.log(`  Wrapping test: ${chalk.bold.cyan(testFilter)} --> ${chalk.bold.green(tagString)}`)
			await wrapIndividualTestInRegionTag(baseDir, testFilter, cloverReportPath, tagString)

			const testPath = (await _grep(testFilter, path.join(baseDir, '*est'))).filepath;
			if (!testPaths.includes(testPath)) {
				testPaths.push(testPath)
			}
		}
	}
}

const main = async (dirs) => {
	dirs.forEach(async dir => {
		await perDirMain(dir);
	})
}

// --- HELPFUL BASH COMMANDS ---
// Generate dir list:
//   find "$(pwd -P)" -type d -name test -not -path "*/node_modules/*" -exec dirname {} \; | awk '{print "\""$0"\","}'
// Find empty 'all-tests.xml' files (generated by mocha failures):
//   ls -l */*/all-tests.xml | egrep "group.+0 " | cut -d' ' -f15
// Find bad code-coverage files (fix: rerun the tests):
//   grep -L -e "count=\"[2-9]\"" **/clover.xml
// Find mismatched region tags (between tests and sample code):
//   diff <(grep "\[START" *.js | cut -d':' -f2 | egrep -o '([a-z]|_)+' | sort | uniq) <(grep "(\\'" test/*.js | grep '_' | egrep -o '([a-z]|_)+' | grep '_' | sort | uniq) | grep '_' | sort
// Find duplicate region tag `describe`s in a file
//   grep describe\( *.js | perl -pe 's/^[[:space:]]+//g' | sort | uniq -d
const dirs = [
	"YOUR_DIRS_HERE"
]
main(dirs);

