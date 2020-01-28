// Initial cmd: mocha --reporter=xunit --reporter-option="output: test.xml"

// nyc --all --reporter=lcov mocha

// Import standard modules (to enable proxyquire overrides)
const console = require('console');
const process = require('process');

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

const queryXmlFile = (filename, xpath) => {
	const fileContents = fs.readFileSync(filename, 'utf-8');
	const doc = new DOMParser().parseFromString(fileContents)
	const nodes = xpathJs(doc, xpath).sort((a, b) => a.lineNumber - b.lineNumber || a.columnNumber - b.columnNumber); // preserve order
	return nodes.map(n => n.value)
}

// Constants
const generateAndLinkToCloverReports = async (language, baseDir, allTestsXml) => {
	let testFilters;
	if (language === 'NODEJS' || language === 'RUBY') {
		testFilters = queryXmlFile(allTestsXml, '//testcase/@name')
		testFilters = testFilters
			.filter(x => !x.includes('" hook '))
			.map(x => x.replace(/\"/g,'\\\"').replace(/'/,"\'"))

		// Check for test filters that map to multiple tests
		const overloadedTestFilters = testFilters
			.map(a => {
				return {
					filter: a,
					overloadedFilters: testFilters.filter(b => a.length > b.length && a.includes(b))
				}
			})
			.filter(({_, overloadedFilters}) => overloadedFilters.length);

		overloadedTestFilters.forEach(({filter, overloadedFilters}) => {
			console.log(`${chalk.bold.yellow('ERR')} filter ${chalk.bold(filter)} overloads other filter(s): ${overloadedFilters}`)
		});

	} else if (language === 'PYTHON') {
		const xunitNames = queryXmlFile(allTestsXml, '//testcase/@name')
		const xunitClassNames = queryXmlFile(allTestsXml, '//testcase/@classname').map(x => x.split('.').slice(-1)[0])
		testFilters = xunitNames.map((name, idx) => `${xunitClassNames[idx]} and ${name}`)
	} else if (language === 'PHP') {
		const xunitNames = queryXmlFile(allTestsXml, '//testcase/@name')
		const xunitClassNames = queryXmlFile(allTestsXml, '//testcase/@class')
		const xunitFileNames = queryXmlFile(allTestsXml, '//testcase/@file')
		testFilters = xunitNames.map((name, idx) => `${name} '${xunitClassNames[idx]}' ${xunitFileNames[idx]}`)
	}

	// PHP: handle @depends annotations
	if (language === 'PHP') {
		const xunitFileNames = queryXmlFile(allTestsXml, '//testcase/@file')
		xunitFileNames.forEach(testFilename => {
			let testContents = fs.readFileSync(testFilename, 'utf-8');
			const testLines = testContents.split('\n');

			// ASSUMPTION: any other tests that a test depends on will be above it in the file
			// Breaking this assumption will result in tests being ran out-of-order
			const dependsLines = _getMatchingLineNums(testLines, x => x.includes('@depends'));
			dependsLines.forEach(dependsLineNum => {
				const testName = testLines[dependsLineNum - 1].split(' ').slice(-1)[0];
				const testLineNums = _getMatchingLineNums(testLines, x => x.includes(` ${testName}(`));

				if (testLineNums.some(x => x > dependsLineNum)) {
					console.log(`${chalk.yellow.bold('WARN')} test ${chalk.bold(testName)} in file ${chalk.italic(testFilename)} should be moved ${chalk.bold('below')} tests it @depends on.`);
				}
			});

			// Disable @depends annotations
			testContents = testContents
				.replace('* @depends', '* !depends')
				.replace('// @depends', '// !depends');
			fs.writeFileSync(testFilename, testContents);
		})
	}

	// Ruby: remove common prefixes between test filters
	if (language === 'RUBY') {
		let rubyRemovedStrings = [];
		for (let i = 0; i < testFilters.length - 1; i++) {
			const wordsA = testFilters[i].split(' ');
			const wordsB = testFilters[i+1].split(' ');

			let commonWords = 0;
			while (wordsA[commonWords] == wordsB[commonWords]) { commonWords += 1; }

			const removedPrefix = wordsA.slice(0, commonWords).join(' ');
			if (removedPrefix && !rubyRemovedStrings.includes(removedPrefix)) {
				rubyRemovedStrings.push(removedPrefix);
			}
		}

		testFilters = testFilters.map(filter => {
			rubyRemovedStrings.forEach(removed => {
				filter = filter.replace(removed + ' ', '');
			})
			return filter;
		})
	}

	let testFilterDirs = testFilters.map(x => slugify(x.replace(/\W+/g, ' ')).toLowerCase())
	if (language === 'PHP') {
		// Shorten PHP's super-long directories
		testFilterDirs = testFilterDirs.map(x => x.split('-').slice(0, 1).join('-'))
	}
	for (const bannedChar of [/:/g, /\'/g, /"/g, /!/g]) {
		testFilterDirs = testFilterDirs.map(dir => dir.replace(bannedChar, ''));
	}

	if (language === 'RUBY' && !process.env.RUBY_REPO_DIR) {
		console.log(`${chalk.yellow.bold('WARN')} Set ${chalk.bold('RUBY_REPO_DIR')} before running these commands.`)
	}

	let covCmds = []
	for (let i = 0; i < testFilters.length; i++) {
		// Skip dirs that exist
		if (fs.existsSync(path.join(baseDir, `test-${testFilterDirs[i]}`))) {
			//continue;
		}

		const coverageDir = `test-${testFilterDirs[i]}`;
		if (language === 'NODEJS') {
			covCmds.push(`${chalk.red.bold('nyc')} --all --reporter=clover --report-dir="test-${testFilterDirs[i]}" ${chalk.green.bold('mocha')} --grep "${testFilters[i]}" --timeout 20000 --exit`);
		} else if (language === 'RUBY') {
			covCmds.push(`bundle exec "${chalk.red.bold('rspec')} --require=\"$RUBY_REPO_DIR/spec/helpers.rb\" spec/*.rb -e \\"${testFilters[i]}\\"" && ${chalk.green.bold('mkdir')} ${coverageDir} && sleep 5 && ${chalk.green.bold('mv')} coverage/coverage.xml ${coverageDir}/clover.xml`);
		} else if (language === 'PYTHON') {
			covCmds.push(`${chalk.red.bold('pytest')} --cov=. --cov-report xml -k "${testFilters[i]}" && ${chalk.green.bold('mkdir')} ${coverageDir} && sleep 5 && ${chalk.green.bold('mv')} coverage.xml ${coverageDir}/clover.xml`)
		} else if (language === 'PHP') {
			covCmds.push(`${chalk.red.bold('../testing/vendor/bin/phpunit')} --verbose --coverage-clover "${coverageDir}/coverage.xml" -c phpunit.xml.dist ${chalk.italic.green('--filter')} ${testFilters[i]}`)
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

const _findCoveredCodeLines = (language, sourcePath, cloverReportPath) => {
	// Find valid code lines (indented ones)
	const sourceLines = fs.readFileSync(sourcePath, 'utf-8').split('\n');
	const sourceLineNums = _getMatchingLineNums(sourceLines, line => line.match(/^\s/))

	// Find lines covered in Clover report
	let cloverLineSelector;
	if (language === 'NODEJS') {
		cloverLineSelector = '//line[not(@count = \'0\')]/@num';
	} else if (language === 'PYTHON' || language == 'RUBY') {
		cloverLineSelector = `//class[@filename = '${path.basename(sourcePath)}']//line[not(@hits = '0')]/@number`;
	} else if (language === 'PHP') {
		cloverLineSelector = `//file[@name = "${sourcePath}"]//line[not(@count = \'0\') and @type=\'stmt\']/@num`;
	}

	const cloverLines = queryXmlFile(cloverReportPath, cloverLineSelector).map(x => parseInt(x))
	if (cloverLines.length == 0) {
		console.log(`${chalk.red.bold('ERR')} Bad Clover output, ensure test passes: ${chalk.bold(cloverReportPath)}`);
		return []
	}

	// Find intersection of (covered lines, valid code lines)
	const coveredCodeLines = cloverLines
		.filter(line => sourceLineNums.includes(line))
		.sort((x, y) => x - y);

	return coveredCodeLines;
}

const _findRegionTagsAndRanges = (language, sourcePath) => {
	const sourceLines = fs.readFileSync(sourcePath, 'utf-8').split('\n');

	// Find region tag blocks
	let startRegionTagLines = _getMatchingLineNums(sourceLines, line => line.includes('[START '))
	let endRegionTagLines = _getMatchingLineNums(sourceLines, line => line.includes('[END '))

	// Map region tags to method invocations
	const regionTagRanges = startRegionTagLines.map(startLine => {
		let tag = sourceLines[startLine - 1]
		tag = tag.substring(tag.indexOf('START') + 6).replace(']', '')

		let endLine = endRegionTagLines.filter(endLine => {
			return startLine < endLine && sourceLines[endLine - 1].endsWith(tag + ']')
		})[0];

		if (!endLine) {
			console.log(`${chalk.red.bold('WARNING')} unclosed region tag (report to sample owner): ${chalk.bold(tag)}`)
		}

		return [startLine, endLine];
	});

	let regionTagsAndRanges = regionTagRanges.map(range => {
		let tag = sourceLines[range[0] - 1]
		tag = tag.substring(tag.indexOf('START') + 6).replace(']', '')

		const out = {}
		out[tag] = range;
		return out;
	});

	// Ignore common (useless) region tag names
	regionTagsAndRanges = regionTagsAndRanges.filter(tagAndRange => !['app'].includes(Object.keys(tagAndRange)[0]));

	// Identify + delete (obvious) "helper method" region tags
	// (Helper method detection is imperfect, and relies on optional per-language idioms)
	if (language === 'PYTHON' || language === 'NODEJS') {
		regionTagsAndRanges = regionTagsAndRanges.filter(tagAndRange => {
			const range = Object.values(tagAndRange)[0]
			const rangeLines = sourceLines.slice(range[0], range[1])

			// Return TRUE if range contains an actual snippet (and not just snippet helper methods)
			return rangeLines.some(line => {
				if (language === 'NODEJS' && (line.startsWith('exports.') || (line.startsWith('app.') && line.includes('(req,')))) {
					// NODEJS: Non-helper methods must be 'export'ed OR have an HTTP-handler-like signature
					return true;
				} else if (language === 'PYTHON' && line.match(/\s*def/) && !line.match(/\s*def\s_/)) {
					// PYTHON: Helper methods begin with an underscore (_)
					return true;
				} else {
					return false;
				}
			})
		})
	}

	return regionTagsAndRanges
}

const getRegionTagsHitByTest = (language, baseDir, cloverReportPath) => {
	let cloverSelector;
	if (language === 'NODEJS') {
		cloverSelector = '//file/@path';
	} else if (language === 'PYTHON' || language === 'RUBY') {
		cloverSelector = '//class/@filename';
	}

	let testFileMarker; // no-op: "string".includes(null) -> false
	if (language === 'PYTHON') {
		testFileMarker = '_test.py';
	} else if (language === 'RUBY') {
		testFileMarker = '_spec.rb';
	} else if (language === 'PHP') {
		testFileMarker = 'Test.php'
	}

	let sourcePathList = queryXmlFile(cloverReportPath, cloverSelector);
	sourcePathList = sourcePathList.filter(x => !x.includes('loadable')); // Remove blacklisted file names
	sourcePathList = sourcePathList.filter(x => !x.includes(testFileMarker)); // Remove non-test files
	sourcePathList = sourcePathList.filter(x => !path.isAbsolute(x) || x.includes(baseDir)); // Remove files not in baseDir (if possible)

	if (sourcePathList.length > 1) {
		console.log(`${chalk.bold('WARN')} Multiple matching source files detected! Using ${chalk.bold(sourcePathList[0])}`)
	}

	let sourcePath = sourcePathList[0];
	if (language === 'PYTHON' || language === 'RUBY') {
		// Convert filenames into absolute paths
		sourcePath = path.join(baseDir, sourcePath.split('/').slice(-1)[0]);
	}

	const sourceLines = fs.readFileSync(sourcePath, 'utf-8').split('\n');

	const coveredCodeLines = _findCoveredCodeLines(language, sourcePath, cloverReportPath);
	const regionTagsAndRanges = _findRegionTagsAndRanges(language, sourcePath);

	if (regionTagsAndRanges.length === 0) {
		console.log(`${chalk.yellow.bold('WARN')} source file ${chalk.bold(sourcePath)} has no region tags!`);
	}

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

const _findClosingBlock = (language, sourceLines, startLineNum) => {
	const startLine = sourceLines[startLineNum - 1];

	let bracket;
	if (language === 'NODEJS') {
		bracket = "});"
	} else if (language === 'RUBY') {
		bracket = 'end'
	} else {
		throw new Error(`Language not supported: ${language}`);
	}

	return _getMatchingLineNums(sourceLines, (line, lineNum) => {
		return line.endsWith(bracket) && startLineNum < lineNum && __numSpaces(line) === __numSpaces(startLine)
	}).sort((x, y) => x - y)[0] || null;
}

const _findPrecedingBlock = (language, sourceLines, startLineNum) => {
	const startLine = sourceLines[startLineNum - 1];

	let bracket;
	if (language === 'NODEJS') {
		bracket = "});"
	} else if (language === 'RUBY') {
		bracket = 'end'
	} else {
		throw new Error(`Language not supported: ${language}`);
	}

	return _getMatchingLineNums(sourceLines, (line, lineNum) => {
		return line.endsWith(bracket) && startLineNum > lineNum + 1 && __numSpaces(line) === __numSpaces(startLine)
	}).sort((x, y) => y - x)[0] || null;
}

const wrapIndividualTestInRegionTag = async (language, testPath, testFilterName, regionsAndTags) => {
	const tagList = uniq(regionsAndTags.map(tag => Object.keys(tag)[0]));

	let tagJoinString;
	if (language === 'NODEJS' || language === 'RUBY') {
		tagJoinString = ' '
	} else if (language === 'PYTHON') {
		tagJoinString = 'And'
	} else if (language === 'PHP') {
		tagJoinString = '_AND_';
	}

	const tagString = tagList.sort().join(tagJoinString)
	let testLines = fs.readFileSync(testPath, 'utf-8').split('\n');

	console.log(`  Wrapping test: ${chalk.bold.cyan(testFilterName)} --> ${chalk.bold.green(tagString)}`)

	// Detect test starting line (and check for existing region tag)
	let regionTagStartLine;
	if (language === 'NODEJS') {
		regionTagStartLine =`describe('${tagString}', () => {`;
	} else if (language === 'PYTHON') {
		regionTagStartLine = `class Test${camelcase(tagString, {pascalCase: true})}(unittest.TestCase):`;
	} else if (language === 'RUBY') {
		regionTagStartLine =`describe "${tagString}" do`;
	} else if (language === 'PHP') {
		regionTagStartLine = `function test_${tagString}`; // followed by 'should', 'does', or '()'
	}

	let testStartLineNum = _getMatchingLineNums(testLines, line => line.includes(testFilterName))[0]
	if (!testStartLineNum) {
		throw new Error('No matching test filter!');
	}

	let regionTagDescriptorRegex;
	if (language === 'NODEJS') {
		regionTagDescriptorRegex = /(describe|it)\(/;
	} else if (language === 'PYTHON') {
		regionTagDescriptorRegex = '/class/\s'
	} else if (language === 'RUBY') {
		regionTagDescriptorRegex = /describe\s/;
	} else if (language === 'PHP') {
		regionTagDescriptorRegex = /function\stest/
	}

	let regionTagLine = testStartLineNum - 1;
	const testBlockSpaces = __numSpaces(testLines[testStartLineNum - 1]);
	while (regionTagLine > 0 &&
				(!testLines[regionTagLine].length ||
				testLines[regionTagLine].match(regionTagDescriptorRegex) ||
				testBlockSpaces <= __numSpaces(testLines[regionTagLine]))
	) {
		// Exact match
		if (testLines[regionTagLine].endsWith(regionTagStartLine)) {
			console.log(`    ${chalk.blue('INFO')} Exact region tag already present, skipping.`);
			return; // Desired region tag already present
		}

		// Fuzzy match
		if (tagList.some(tag => tag.includes('_') && testLines[regionTagLine].includes(tag))) {
			console.log(`${chalk.red.bold('ERR')} Different region tags present, ${chalk.bold('label manually!')}`);
			console.log(`    Proposed tag: ${chalk.bold(tagString)}`);
			return;
		}

		regionTagLine -= 1;
	}

	if (language === 'NODEJS' || language === 'RUBY') {
		// Add end line (closing brackets)
		let closingBracket;
		if (language === 'NODEJS') {
			closingBracket = '});'
		} else if (language === 'RUBY') {
			closingBracket = 'end'
		}

		const testEndLine = _findClosingBlock(language, testLines, testStartLineNum)
		testLines.splice(testEndLine, 0, closingBracket)

		// Add test start line (describe(...))
		testLines.splice(testStartLineNum - 1, 0, regionTagStartLine)

	} else if (language === 'PYTHON') {
		// Find 'def' line (ignoring decorators)
		while (testLines[testStartLineNum - 1].match(/@\w/g)) {
			testStartLineNum -= 1
		}
		const defLine = testLines[testStartLineNum - 1]

		// Check for existing wrapping class
		if (defLine.match(/^\s/)) {
			console.log(`${chalk.bold.red('ERR')} Python test is already in an indented block!`)
			return;
		}

		// Add 'self' param to 'def' statements
		if (!defLine.includes('self')) {
			if (defLine.includes('()')) {
				testLines[testStartLineNum - 1] = defLine.replace('()', '(self)')
			} else {
				testLines[testStartLineNum - 1] = defLine.replace('(', '(self, ')
			}
		}

		// Determine affected lines' indentation settings	
		const testStartIndentCount = __numSpaces(testLines[testStartLineNum - 1]);

		const indentOffset = __numSpaces(testLines[testStartLineNum]) - __numSpaces(testLines[testStartLineNum - 1]);
		const whitespaceChar = testLines.some(l => l.startsWith('\t')) ? '\t' : ' ';

		while (testLines[testStartLineNum - 2].match(/@\w/g)) {
			testStartLineNum -= 1 // Add decorators to indented block
		}

		// Insert region-tag line
		testLines.splice(testStartLineNum - 1, 0, regionTagStartLine) 

		// Indent affected lines
		let i = testStartLineNum;
		let withinBlock = false;
		do {
			if (testLines[i].length > 0) { // Ignore whitespace
				testLines[i] = whitespaceChar.repeat(indentOffset) + testLines[i];
			}
		
			if (testLines[i].match(/^(class|def)/)) {
				if (!withinBlock) {
					withinBlock = true;
				} else {
					break; // after indented block
				}
			}
			i += 1;
		} while (i < testLines.length);
	} else if (language === 'PHP') {
		// Replace existing method name with target method name
		testLines = testLines.map(line => line.replace(
			`function ${testFilterName}(`, `function test_${tagString}_SHOULD_${testFilterName}(`));
	}

	let output = testLines.join('\n');

	// PHP: re-enable @depends annotations
	if (language === 'PHP') {
		output = output
					.replace('* !depends', '* @depends')
					.replace('// !depends', '// @depends');
	}

	fs.writeFileSync(testPath, output);
}

const dedupeRegionTags = async (language, testFile) => {
	const DUPLICATE_LINE_STR = 'DUPLICATE_PLEASE_REMOVE_ME'
	let regionTagDescriptorRegex, regionTerminatorStr;
	if (language === 'NODEJS') {
		regionTagDescriptorRegex = /describe\(/;
		regionTerminatorRegex = /\s?\}\)/;
	} else if (language === 'PYTHON') {
		regionTagDescriptorRegex = /^class\s.+\(\)/
	} else if (language === 'RUBY') {
		regionTagDescriptorRegex = /describe\s/;
		regionTerminatorRegex = /\s*end/;
	}

	let testLines = fs.readFileSync(testFile, 'utf-8').split('\n');
	const regionTagLineNums = _getMatchingLineNums(testLines, line => line.match(regionTagDescriptorRegex))

	// Remove duplicate region tags from *contiguous* code blocks
	// (Non-contiguous blocks will each have their own region tag label)
	let duplicateTagLines = [];
	for (let i = 1; i < regionTagLineNums.length; i++) {
		if (testLines[regionTagLineNums[i] - 1] === testLines[regionTagLineNums[i-1] - 1]) {
			duplicateTagLines.push(regionTagLineNums[i])
		}
	}

	for (let duplicateLineNum of duplicateTagLines) {
		const regionNumSpaces = __numSpaces(testLines[duplicateLineNum - 1]);
		testLines[duplicateLineNum - 1] = DUPLICATE_LINE_STR;

		// Remove preceding region terminator (Node / Ruby)
		// If no preceding terminator is present, wrap around the file and remove the succeeding one instead
		if (language === 'NODEJS' || language === 'RUBY') {
			let terminatorLineNum;

			let tempLineNum = duplicateLineNum - 1;
			let tempLineSpaces = __numSpaces(testLines[tempLineNum]);

			while (tempLineNum != duplicateLineNum && tempLineSpaces >= regionNumSpaces) {
				if (testLines[tempLineNum].match(regionTerminatorRegex) && tempLineSpaces === regionNumSpaces) {
					terminatorLineNum = tempLineNum;
					break;
				}

				tempLineNum -= 1;
				if (tempLineNum === 0) {
					// Wrap around if no preceding terminator found
					tempLineNum = testLines.length - 1
				}

				tempLineSpaces = __numSpaces(testLines[tempLineNum]);
			}

			// Remove marked region terminator
			if (terminatorLineNum) {
				testLines[terminatorLineNum] = DUPLICATE_LINE_STR;
			}
		}
	}

	testLines = testLines.filter(x => x !== DUPLICATE_LINE_STR);

	fs.writeFileSync(testFile, testLines.join('\n'));
};

const generateTestList = async (language, baseDir) => {
	if (language == 'NODEJS') {
		await execPromise(`mocha --reporter xunit --timeout 30s --exit --reporter-option="output=all-tests.xml"`, {cwd: baseDir});
	} else if (language === 'PYTHON') {
		await execPromise(`pytest --junitxml=all-tests.xml --cov=. --cov-report xml`, {cwd: baseDir});
	} else if (language === 'RUBY') {
		await execPromise(`bundle exec "rspec --format RspecJunitFormatter --out all-tests.xml"`, {cwd: baseDir});
	} else if (language === 'PHP') {
		await execPromise(`~/.composer/vendor/bin/phpunit ${baseDir}/test --verbose --log-junit ${baseDir}/all-tests.xml`, {cwd: path.dirname(baseDir)});
	}
}

const _getLanguageForDirectory = (dir) => {
	for (const lang of ['NODEJS', 'PYTHON', 'RUBY', 'PHP']) {
		if (dir.toUpperCase().includes(lang)) {
			return lang;
		}
	}

	// No match
	return null;
}

const perDirMain = async (baseDir) => {
	// Auto-detect language
	const language = _getLanguageForDirectory(baseDir)
	if (!language) {
		console.log(`${chalk.red('ERR')} Language auto-detection failed for directory: ${baseDir}`);
		return
	}

	const allTestsXml = path.join(baseDir, 'all-tests.xml')
	if (!fs.existsSync(allTestsXml)) {
		console.log(`Generating test list in: ${baseDir}`);
		await generateTestList(language, baseDir);
		return;
	}


	console.log(`Generating Clover reports in: ${chalk.bold(baseDir)} (${chalk.cyan('language')}: ${chalk.bold(language)})`)
	const {testFilters, testFilterDirs} = await generateAndLinkToCloverReports(language, baseDir, allTestsXml);

	const testPaths = [];

	// Wrap region tags
	console.log(`--------------------`);
	for (let i = 0; i < testFilters.length; i++) {
		const testRawFilter = testFilters[i];
		const testFilterDir = testFilterDirs[i];

		const cloverReportPath = path.join(baseDir, `test-${testFilterDir}/clover.xml`)
		const regionsAndTags = await getRegionTagsHitByTest(language, baseDir, cloverReportPath)

		if (regionsAndTags.length != 0) {
			let testFilter = testRawFilter;
			if (language === 'PYTHON') {
				testFilter = testRawFilter.split(' and ').slice(-1)[0]
			}

			// Get path to file containing specified test
			let testPath;
			if (language === 'NODEJS') {
				testPath = (await _grep(testFilter, path.join(baseDir, '*est'))).filepath;
			} else if (language === 'RUBY') {
				testPath = (await _grep(testFilter, path.join(baseDir, '*pec'))).filepath;
			} else if (language === 'PYTHON') {
				testPath = path.join(baseDir, `${testRawFilter.split(' and ')[0]}.py`)
			}

			await wrapIndividualTestInRegionTag(language, testPath, testFilter, regionsAndTags)

			if (!testPaths.includes(testPath)) {
				testPaths.push(testPath)
			}
		}
	}

	console.log(chalk.bold('--- De-duping region tags ---'));
	testPaths.forEach(path => dedupeRegionTags(language, path));
}

const main = async (dirs) => {
	console.log(chalk.bold('Run these commands if you need to install sub-directory dependencies'));
	dirs.forEach(async dir => {
		let installCmd;
		const language = _getLanguageForDirectory(dir);
		if (language === 'NODEJS') {
			installCmd = `${chalk.bold.green('npm')} install`;
		} else if (language === 'PYTHON') {
			installCmd = `${chalk.bold.green('pip')} install -r requirements.txt`;
		} else if (language === 'RUBY') {
			installCmd = `${chalk.bold.green('bundle')} exec`;
		} else if (language === 'PHP') {
			installCmd = `${chalk.bold.green('composer')} install`;
		}
		console.log(`  ${chalk.cyan.bold('cd')} ${dir} && ${installCmd}`);
	});

	console.log(`--------------------`);
	dirs.forEach(async dir => {
		await perDirMain(dir);
	});
}

// --- HELPFUL BASH COMMANDS ---
// Generate dir list:
//   Node.js
//     find "$(pwd -P)" -type d -name test -not -path "*/node_modules/*" -exec dirname {} \; | awk '{print "\""$0"\","}' | sort
//   Python
//     find "$(pwd -P)" -type f -name "*test.py" -exec dirname {} \; | awk '{print "\""$0"\","}' | sort | uniq
//   Ruby
//     find "$(pwd -P)" -type f -name "Gemfile" -exec dirname {} \; | awk '{print "\""$0"\","}' | sort | uniq
//   PHP
//     find "$(pwd -P)" -type f -name "*Test.php" -not -path "*/vendor/*" -exec dirname {} \; | xargs -I{} dirname {} | awk '{print "\""$0"\","}' | sort | uniq
// Find bad code-coverage files (fix: rerun the tests):
//   grep -L -e "count=\"[2-9]\"" **/clover.xml
// Find mismatched region tags (between tests and sample code):
//   diff <(grep "\[START" *.js | cut -d':' -f2 | egrep -o '([a-z]|_)+' | sort | uniq) <(grep "(\\'" test/*.js | grep '_' | egrep -o '([a-z]|_)+' | grep '_' | sort | uniq) | grep '_' | sort
// Find duplicate region tag `describe`s in a file
//   grep describe\( *.js | perl -pe 's/^[[:space:]]+//g' | sort | uniq -d
const dirs = [
	"/Users/anassri/Desktop/php-docs-samples/storage"
]

if (require.main === module) {
	main(dirs);
}

// Export methods (for easier testing)
exports.generateAndLinkToCloverReports = generateAndLinkToCloverReports;
exports.getRegionTagsHitByTest = getRegionTagsHitByTest;
exports.wrapIndividualTestInRegionTag = wrapIndividualTestInRegionTag;
exports.dedupeRegionTags = dedupeRegionTags;
exports.generateTestList = generateTestList;
exports.perDirMain = perDirMain;

exports._findCoveredCodeLines = _findCoveredCodeLines;
exports._findRegionTagsAndRanges = _findRegionTagsAndRanges;
exports._findClosingBlock = _findClosingBlock
exports._findPrecedingBlock = _findPrecedingBlock
exports._getLanguageForDirectory = _getLanguageForDirectory;


