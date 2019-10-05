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
const camelcase = require('camelcase');

// const language = 'NODEJS';
const language = 'PYTHON';

const queryXmlFile = (filename, xpath) => {
	const fileContents = fs.readFileSync(filename, 'utf-8');
	const doc = new DOMParser().parseFromString(fileContents)    
	const nodes = xpathJs(doc, xpath)
	return nodes.map(n => n.value)
}

// Constants
const generateAndLinkToCloverReports = async (baseDir, allTestsXml) => {
	let testFilters;
	if (language === 'NODEJS') {
		testFilters = queryXmlFile(allTestsXml, '//testcase/@name')
		testFilters = testFilters
			.filter(x => !x.includes('" hook '))
			.map(x => x.replace(/\"/g,'\\\"').replace(/'/,"\'"))
	} else if (language === 'PYTHON') {
		const xunitNames = queryXmlFile(allTestsXml, '//testcase/@name')
		const xunitClassNames = queryXmlFile(allTestsXml, '//testcase/@classname').map(x => x.split('.').slice(-1)[0])
		testFilters = xunitNames.map((name, idx) => `${xunitClassNames[idx]} and ${name}`)
	}

	let testFilterDirs = testFilters.map(x => slugify(x).toLowerCase())
	for (const bannedChar of [/:/g, /\'/g, /"/g]) {
		testFilterDirs = testFilterDirs.map(dir => dir.replace(bannedChar, ''));
	}

	console.log(`TF`, testFilters)
	console.log(`TF-D`, testFilterDirs)

	let covCmds = []
	for (let i = 0; i < testFilters.length; i++) {
		// Skip dirs that exist
		if (fs.existsSync(path.join(baseDir, `test-${testFilterDirs[i]}`))) {
			//continue;
		}

		if (language === 'NODEJS') {
			covCmds.push(`${chalk.red.bold('nyc')} --all --reporter=clover --report-dir="test-${testFilterDirs[i]}" ${chalk.green.bold('mocha')} --grep "${testFilters[i]}" --timeout 20000 --exit`);
		} else if (language === 'PYTHON') {
			const coverageDir = `test-${testFilterDirs[i]}`;
			covCmds.push(`${chalk.red.bold('pytest')} --cov=. --cov-report xml -k "${testFilters[i]}" && ${chalk.green.bold('mkdir')} ${coverageDir} && ${chalk.green.bold('mv')} coverage.xml ${coverageDir}/clover.xml`)
		}
	}

	console.log(chalk.bold('Execute these commands manually + ensure tests pass...'))
	for (const cmd of covCmds) {
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
	let cloverLineSelector;
	if (language === 'NODEJS') {
		cloverLineSelector = '//line[not(@count = \'0\')]/@num';
	} else if (language === 'PYTHON') {
		cloverLineSelector = `//class[@filename = '${path.basename(sourcePath)}']//line[not(@hits = '0')]/@number`;
	}
	const cloverLines = queryXmlFile(cloverReportPath, cloverLineSelector).map(x => parseInt(x))
	if (cloverLines.length == 0) {
		console.log(chalk.red.bold('ERR') + ' Bad Clover output, ensure test passes: ' + chalk.bold(cloverReportPath));
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

const getRegionTagsForTest = (baseDir, cloverReportPath) => {
	let cloverSelector;
	if (language === 'NODEJS') {
		cloverSelector = '//file/@path';
	} else if (language === 'PYTHON') {
		cloverSelector = '//class/@filename'
	}

	let sourcePath = queryXmlFile(cloverReportPath, cloverSelector).filter(x => !x.includes('loadable') && !x.includes('_test'))[0];
	if (language === 'PYTHON') {
		sourcePath = path.join(baseDir, sourcePath.split('/').slice(-1)[0]);
	}

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

const wrapIndividualTestInRegionTag = async (testPath, testFilterName, cloverReportPath, regionTag) => {
	const testLines = fs.readFileSync(testPath, 'utf-8').split('\n');

	// Detect test starting line (and check for existing region tag)
	let regionTagStartLine;
	if (language === 'NODEJS') {
		regionTagStartLine =`describe('${regionTag}', () => {`;
	} else if (language === 'PYTHON') {
		regionTagStartLine = `class ${camelcase(regionTag, {pascalCase: true})}():`;
	}

	const testStartLineNum = _getMatchingLineNums(testLines, line => line.includes(testFilterName))[0]
	const testStartLine = testLines[testStartLineNum - 1];


	let regionTagDescriptorRegex;
	if (language === 'NODEJS') {
		regionTagDescriptorRegex = /(describe|it)\(/;
	} else if (language === 'PYTHON') {
		regionTagDescriptorRegex = '/class/\s'
	}
	
	let regionTagLine = testStartLineNum - 2;
	while (regionTagLine > 0 && testLines[regionTagLine].match(regionTagDescriptorRegex)) {
		if (testLines[regionTagLine].endsWith(regionTagStartLine)) {
			return; // Desired region tag already present
		}
		regionTagLine -= 1;
	}

	if (language === 'NODEJS') {
		// Add end line (closing brackets)
		const testEndLine = _findClosingParenthesis(testLines, testStartLineNum)
		testLines.splice(testEndLine, 0, `});`)

		// Add start line (describe(...)) if necessary
		testLines.splice(testStartLineNum - 1, 0, regionTagStartLine)

	} else if (language === 'PYTHON') {
		// Add start line (describe(...)) if necessary
		testLines.splice(testStartLineNum - 1, 0, regionTagStartLine)

		// Indent affected lines
		let i = testStartLineNum;
		const testStartIndentCount = __numSpaces(testLines[testStartLineNum - 1]);
		const indentOffset = __numSpaces(testLines[testStartLineNum + 1]) - __numSpaces(testLines[testStartLineNum]);
		do {
			if (testLines[i].length > 0) { // Ignore whitespace
				testLines[i] = ' '.repeat(indentOffset) + testLines[i];
			}
			i += 1;
		} while (i < testLines.length && !testLines[i].match(/^(class|def)/))
	}

	// Save to file
	const output = testLines.join('\n');
	fs.writeFileSync(testPath, output);
}

const dedupeRegionTags = async (testFile) => {
	const DUPLICATE_LINE_STR = 'DUPLICATE_PLEASE_REMOVE_ME'
	let regionTagDescriptorRegex;
	if (language === 'NODEJS') {
		regionTagDescriptorRegex = /(describe|it)\(/;
	} else if (language === 'PYTHON') {
		regionTagDescriptorRegex = /^class\s.+\(\)/
	}

	let testLines = fs.readFileSync(testFile, 'utf-8').split('\n');
	const regionTagLineNums = _getMatchingLineNums(testLines, line => line.match(regionTagDescriptorRegex))

	// Remove any region tag line that matches the previous region tag line
	let duplicateTagLines = [];
	for (let i = 1; i < regionTagLineNums.length; i++) {
		if (testLines[regionTagLineNums[i] - 1] === testLines[regionTagLineNums[i-1] - 1]) {
			duplicateTagLines.push(regionTagLineNums[i])
		}
	}
	for (let duplicateLineNum of duplicateTagLines) {
		testLines[duplicateLineNum - 1] = DUPLICATE_LINE_STR;
	}
	testLines = testLines.filter(x => x !== DUPLICATE_LINE_STR);

	fs.writeFileSync(testFile, testLines.join('\n'));
};

const generateTestList = async (baseDir) => {
	if (language == 'NODEJS') {
		await execPromise(`mocha --reporter xunit > all-tests.xml`, {cwd: baseDir});
	} else if (language === 'PYTHON') {
		await execPromise(`pytest --junitxml=all-tests.xml --cov=. --cov-report xml`, {cwd: baseDir});
	}
}

// ASSUMPTION: all repeats of a region tag are contiguous
const perDirMain = async (baseDir) => {
	console.log(`--------------------`)
	const allTestsXml = path.join(baseDir, 'all-tests.xml')
	if (!fs.existsSync(allTestsXml)) {
		console.log(`Generating test list in: ${baseDir}`);
		await generateTestList(baseDir);
		return;
	}

	console.log(`Generating Clover reports in: ${chalk.bold(baseDir)}`)
	const {testFilters, testFilterDirs} = await generateAndLinkToCloverReports(baseDir, allTestsXml);

	const testPaths = [];

	// Wrap region tags
	console.log(`--------------------`)
	for (let i = 0; i < testFilters.length; i++) {
		const testRawFilter = testFilters[i];
		const testFilterDir = testFilterDirs[i];

		const cloverReportPath = path.join(baseDir, `test-${testFilterDir}/clover.xml`)

		const tags = await getRegionTagsForTest(baseDir, cloverReportPath)
		let tagString = uniq(tags.map(tag => Object.keys(tag)).sort(), true).join(' ')

		if (tags.length != 0) {
			let testFilter = testRawFilter;
			if (language === 'PYTHON') {
				testFilter = testRawFilter.split(' and ').slice(-1)[0]
				tagString = camelcase(tagString, {pascalCase: true});
			}
			console.log(`  Wrapping test: ${chalk.bold.cyan(testFilter)} --> ${chalk.bold.green(tagString)}`)

			let testPath;
			if (language === 'NODEJS') {
				testPath = (await _grep(testFilter, path.join(baseDir, '*est'))).filepath;
			} else if (language === 'PYTHON') {
				testPath = path.join(baseDir, `${testRawFilter.split(' and ')[0]}.py`)
			}

			await wrapIndividualTestInRegionTag(testPath, testFilter, cloverReportPath, tagString)

			if (!testPaths.includes(testPath)) {
				testPaths.push(testPath)
			}
		}
	}

	console.log(chalk.bold('--- De-duping region tags ---'));
	testPaths.forEach(path => dedupeRegionTags(path));
}

const main = async (dirs) => {
	dirs.forEach(async dir => {
		await perDirMain(dir);
	});
}

// --- HELPFUL BASH COMMANDS ---
// Generate dir list:
//   Node.js: find "$(pwd -P)" -type d -name test -not -path "*/node_modules/*" -exec dirname {} \; | awk '{print "\""$0"\","}' | sort
//   Python: find "$(pwd -P)" -type f -name "*test.py" -exec dirname {} \; | awk '{print "\""$0"\","}' | sort | uniq
// Find empty 'all-tests.xml' files (generated by mocha failures):
//   ls -l */*/all-tests.xml | egrep "group.+0 " | cut -d' ' -f15
// Find bad code-coverage files:
//   grep -L -e "count=\"[2-9]\"" **/clover.xml
// Find mismatched region tags (between tests and sample code):
//   diff <(grep "\[START" *.js | cut -d':' -f2 | egrep -o '([a-z]|_)+') <(grep "(\\'" test/*.js | grep '_' | egrep -o '([a-z]|_)+' | grep '_' | sort | uniq) | grep '_' | sort
const dirs2 = [
	"/Users/anassri/Desktop/python-docs-samples/functions/billing",
	"/Users/anassri/Desktop/python-docs-samples/functions/composer",
	"/Users/anassri/Desktop/python-docs-samples/functions/concepts",
	"/Users/anassri/Desktop/python-docs-samples/functions/env_vars",
	"/Users/anassri/Desktop/python-docs-samples/functions/firebase",
	"/Users/anassri/Desktop/python-docs-samples/functions/gcs",
	"/Users/anassri/Desktop/python-docs-samples/functions/helloworld",
	"/Users/anassri/Desktop/python-docs-samples/functions/http",
	"/Users/anassri/Desktop/python-docs-samples/functions/imagemagick",
	"/Users/anassri/Desktop/python-docs-samples/functions/log",
	"/Users/anassri/Desktop/python-docs-samples/functions/ocr/app",
	"/Users/anassri/Desktop/python-docs-samples/functions/slack",
	"/Users/anassri/Desktop/python-docs-samples/functions/spanner",
	"/Users/anassri/Desktop/python-docs-samples/functions/sql",
	"/Users/anassri/Desktop/python-docs-samples/functions/sql",
	"/Users/anassri/Desktop/python-docs-samples/functions/tips"
]
const dirs = ["/Users/anassri/Desktop/python-docs-samples/functions/helloworld"]
main(dirs);

