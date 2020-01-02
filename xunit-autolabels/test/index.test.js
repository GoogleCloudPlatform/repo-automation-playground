const proxyquire = require('proxyquire').noPreserveCache();
const sinon = require('sinon');
const path = require('path');
const fs = require('fs');
const assert = require('assert');
const execPromise = require('child-process-promise').exec;

const createMocks = (disableExecPromise, cacheFileWrites) => {
	const consoleMock = {
		log: sinon.stub(),
		info: console.info // Used for debugging
	};

	const envMock = {};

	// Disable chalk
	const chalkMock = sinon.stub().returnsArg(0);
	chalkMock.bold = chalkMock;
	chalkMock.italic = chalkMock;
	chalkMock.cyan = chalkMock;
	chalkMock.blue = chalkMock;
	chalkMock.yellow = chalkMock;
	chalkMock.green = chalkMock;
	chalkMock.red = chalkMock;

	const proxyquireMocks = {
		console: consoleMock,
		chalk: chalkMock,
		process: {
			env: envMock
		}
	};

	// Mock execPromise
	const execPromiseStub = sinon.stub().resolves();
	if (disableExecPromise) {
		proxyquireMocks['child-process-promise'] = {
			exec: (cmd, cwd) => {
				// Don't disable grep
				if (cmd.startsWith('grep ')) {
					return execPromise(cmd, cwd);
				} else {
					return execPromiseStub(cmd, cwd);
				}
			}
		};
	}

	// Store modified files in memory
	let fileCache = {};
	let proxyquireFsMock = {}
	const writeFileSyncStub = sinon.stub();
	if (cacheFileWrites) {
		proxyquireFsMock = {
			readFileSync: (path, fmt) => fileCache[path] || fs.readFileSync(path, fmt),
			writeFileSync: (path, contents) => {
				fileCache[path] = contents;
				writeFileSyncStub(path, contents);
			}
		}
	} else {
		proxyquireFsMock.writeFileSync = writeFileSyncStub;
	}
	proxyquireMocks.fs = proxyquireFsMock;

	// Stub main program dependencies

	const program = proxyquire('..', proxyquireMocks)

	return {
		program: program,
		mocks: {
			fs: {
				writeFileSync: writeFileSyncStub
			},
			console: consoleMock,
			env: envMock,
			execPromise: execPromiseStub
		}
	};
}

describe('generateAndLinkToCloverReports', () => {
	describe('Per-language edge cases', () => {
		describe('PHP', () => {
			before('all-tests.xml files should be generated', () => {
				assert(fs.existsSync(path.resolve('./test/data/php/basic_test/all-tests.xml')));
				assert(fs.existsSync(path.resolve('./test/data/php/out_of_order_test/all-tests.xml')));
			})

			it('should replace @depends with !depends', async () => {
				const baseDir = path.resolve('./test/data/php/basic_test');
				const testPath = path.join(baseDir, 'basicTest.php');

				const testContents = fs.readFileSync(testPath, 'utf-8');
				const {program, mocks} = createMocks();
				
				await program.generateAndLinkToCloverReports('PHP', baseDir, path.join(baseDir, 'all-tests.xml'));

				assert.strictEqual(mocks.fs.writeFileSync.firstCall.args[1], testContents.replace('@depends', '!depends'));

				const testCmd1 = mocks.console.log.getCall(1).args[0];
				assert(testCmd1.includes(testPath));
				assert(testCmd1.includes('test-testone'));

				const testCmd2 = mocks.console.log.getCall(2).args[0];
				assert(testCmd2.includes(testPath));
				assert(testCmd2.includes('test-testtwo'));
			});

			it('should warn if tests dont execute from the top down', async () => {
				const baseDir = path.resolve('./test/data/php/out_of_order_test');
				const testPath =  path.join(baseDir, 'outOfOrderTest.php')

				const {program, mocks} = createMocks();

				await program.generateAndLinkToCloverReports('PHP', baseDir, path.join(baseDir, 'all-tests.xml'));

				assert(mocks.console.log.calledWith(
					`WARN test testOne in file ${testPath} should be moved below tests it @depends on.`
				));
			});
		});

		describe('Ruby', () => {
			before('all-tests.xml files should be generated', () => {
				assert(fs.existsSync(path.resolve('./test/data/ruby/basic_test/all-tests.xml')));
			})

			it('should warn on missing RUBY_REPO_DIR', async () => {
				const baseDir = path.resolve('./test/data/ruby/basic_test');
				const testPath =  path.join(baseDir, 'spec/basic_spec.rb')

				const {program, mocks} = createMocks();

				mocks.env.RUBY_REPO_DIR = '';

				await program.generateAndLinkToCloverReports('RUBY', baseDir, path.join(baseDir, 'all-tests.xml'));

				assert(mocks.console.log.calledWith('WARN Set RUBY_REPO_DIR before running these commands.'));
			});
		});

		describe('Node.js', () => {
			before('all-tests.xml files should be generated', async () => {
				assert(fs.existsSync(path.resolve('./test/data/nodejs/hook_test/all-tests.xml')));
			});

			it('should filter out hooks', async () => {
				const baseDir = path.resolve('./test/data/nodejs/hook_test');
				const testPath =  path.join(baseDir, 'hook.test.js')

				const {program, mocks} = createMocks();

				await program.generateAndLinkToCloverReports('NODEJS', baseDir, path.join(baseDir, 'all-tests.xml'));

				assert(mocks.console.log.callCount, 0);
			});

			it('should error if a test filter matches multiple tests', async () => {
				const baseDir = path.resolve('./test/data/nodejs/filter_overlap_test');
				const testPath =  path.join(baseDir, 'filter-overlap.test.js')

				const {program, mocks} = createMocks();

				await program.generateAndLinkToCloverReports('NODEJS', baseDir, path.join(baseDir, 'all-tests.xml'));

				assert(mocks.console.log.calledWith(
					'ERR filter overlapping filters overloads other filter(s): filters'
				));
			})
		});
	});

	describe('Command printing', () => {
		it('should print commands for PHP', async () => {
			const baseDir = path.resolve('./test/data/php/basic_test');
			const testPath = path.join(baseDir, 'basicTest.php');

			const {program, mocks} = createMocks();
			
			await program.generateAndLinkToCloverReports('PHP', baseDir, path.join(baseDir, 'all-tests.xml'));

			assert(mocks.console.log.calledWith('Execute these commands manually + ensure tests pass...'));

			// N.B: PHP *explicitly* supports ordered tests via @depends
			// Therefore, PHP test commands MUST be printed (and ran) in order
			const testCmd1 = mocks.console.log.getCall(1).args[0];
			assert(testCmd1.includes(`cd ${baseDir}`));
			assert(testCmd1.includes('phpunit'))
			assert(testCmd1.includes(testPath));
			assert(testCmd1.includes('test-testone'));

			const testCmd2 = mocks.console.log.getCall(2).args[0];
			assert(testCmd2.includes(`cd ${baseDir}`));
			assert(testCmd2.includes('phpunit'))
			assert(testCmd2.includes(testPath));
			assert(testCmd2.includes('test-testtwo'));
		});

		it('should print commands for Ruby', async () => {
			const baseDir = path.resolve('./test/data/ruby/basic_test');
			const testPath = path.join(baseDir, 'spec/basic_spec.rb');

			const {program, mocks} = createMocks();
			mocks.env.RUBY_REPO_DIR = __dirname;
			
			await program.generateAndLinkToCloverReports('RUBY', baseDir, path.join(baseDir, 'all-tests.xml'));

			assert(mocks.console.log.calledWith('Execute these commands manually + ensure tests pass...'));

			const testCmd1 = mocks.console.log.getCall(1).args[0];
			assert(testCmd1.includes(`cd ${baseDir}`));
			assert(testCmd1.includes('bundle exec "rspec'))
			assert(testCmd1.includes('-e \\"one\\"'));

			const testCmd2 = mocks.console.log.getCall(2).args[0];
			assert(testCmd2.includes(`cd ${baseDir}`));
			assert(testCmd2.includes('bundle exec "rspec'))
			assert(testCmd2.includes('-e \\"two\\"'));
		});

		it('should print commands for Python', async () => {
			const baseDir = path.resolve('./test/data/python/basic_test');
			const testPath = path.join(baseDir, 'basic_test.py');

			const {program, mocks} = createMocks();
			
			await program.generateAndLinkToCloverReports('PYTHON', baseDir, path.join(baseDir, 'all-tests.xml'));

			assert(mocks.console.log.calledWith('Execute these commands manually + ensure tests pass...'));

			const testCmd1 = mocks.console.log.getCall(1).args[0];
			assert(testCmd1.includes(`cd ${baseDir}`));
			assert(testCmd1.includes('pytest'))
			assert(testCmd1.includes('BasicTest and test_one'));

			const testCmd2 = mocks.console.log.getCall(2).args[0];
			assert(testCmd2.includes(`cd ${baseDir}`));
			assert(testCmd2.includes('pytest'))
			assert(testCmd2.includes('BasicTest and test_two'));
		});

		it('should print commands for Node.js', async () => {
			const baseDir = path.resolve('./test/data/nodejs/basic_test');
			const testPath = path.join(baseDir, 'basic.test.js');

			const {program, mocks} = createMocks();

			await program.generateAndLinkToCloverReports('NODEJS', baseDir, path.join(baseDir, 'all-tests.xml'));

			assert(mocks.console.log.calledWith('Execute these commands manually + ensure tests pass...'));

			const testCmd1 = mocks.console.log.getCall(1).args[0];
			assert(testCmd1.includes(`cd ${baseDir}`));
			assert(testCmd1.includes('mocha'))
			assert(testCmd1.includes('--grep "test one"'));

			const testCmd2 = mocks.console.log.getCall(2).args[0];
			assert(testCmd2.includes(`cd ${baseDir}`));
			assert(testCmd2.includes('mocha'))
			assert(testCmd2.includes('--grep "test two"'));
		});
	});
});

describe('_findCoveredCodeLines', () => {
	describe('Basic usage', () => {
		it('should find covered lines for PHP', async () => {
			const baseDir = path.resolve('./test/data/php/coverage_test');
			const sourcePath = path.join(baseDir, 'coverage.php');
			const coveragePath = path.join(baseDir, 'coverage.xml');

			const {program, mocks} = createMocks();

			const coveredLines = program._findCoveredCodeLines('PHP', sourcePath, coveragePath);

			assert(!coveredLines.includes(4), 'should exclude non-code lines');
			assert(!coveredLines.includes(9), 'should exclude non-code lines');

			assert(coveredLines.includes(6));
			assert(!coveredLines.includes(11), 'should exclude lines not covered');
		});

		it('should find covered lines for Python', async () => {
			const baseDir = path.resolve('./test/data/python/coverage_test');
			const sourcePath = path.join(baseDir, 'coverage_main.py');
			const coveragePath = path.join(baseDir, 'coverage.xml');

			const {program, mocks} = createMocks();

			const coveredLines = program._findCoveredCodeLines('PYTHON', sourcePath, coveragePath);

			assert(!coveredLines.includes(1), 'should exclude non-indented lines');
			assert(!coveredLines.includes(4), 'should exclude non-indented lines');

			assert(coveredLines.includes(2));
			assert(!coveredLines.includes(5), 'should exclude lines not covered');
		});

		it('should find covered lines for Ruby', async () => {
			const baseDir = path.resolve('./test/data/ruby/coverage_test');
			const sourcePath = path.join(baseDir, 'coverage.rb');
			const coveragePath = path.join(baseDir, 'coverage/coverage.xml');

			const {program, mocks} = createMocks();

			const coveredLines = program._findCoveredCodeLines('RUBY', sourcePath, coveragePath);

			assert(!coveredLines.includes(1), 'should exclude non-indented lines');
			assert(!coveredLines.includes(5), 'should exclude non-indented lines');

			assert(coveredLines.includes(2));
			assert(!coveredLines.includes(6), 'should exclude lines not covered');
		});

		it('should find covered lines for Node.js', async () => {
			const baseDir = path.resolve('./test/data/nodejs/coverage_test');
			const sourcePath = path.join(baseDir, 'index.js');
			const coveragePath = path.join(baseDir, 'test-test-one/clover.xml');

			const {program, mocks} = createMocks();

			const coveredLines = program._findCoveredCodeLines('NODEJS', sourcePath, coveragePath);

			assert(!coveredLines.includes(1), 'should exclude non-indented lines');
			assert(!coveredLines.includes(5), 'should exclude non-indented lines');

			assert(coveredLines.includes(2));
			assert(!coveredLines.includes(6), 'should exclude lines not covered');
		});
	});

	describe('Edge cases', () => {
		it('should detect code lines indented with tabs', () => {
			const baseDir = path.resolve('./test/data/nodejs/tabs_spaces_test');
			const sourcePath = path.join(baseDir, 'tabs.js');
			const coveragePath = path.join(baseDir, 'test-test-tabs/clover.xml');

			const {program, mocks} = createMocks();

			const coveredLines = program._findCoveredCodeLines('NODEJS', sourcePath, coveragePath);

			assert(coveredLines.includes(2));
		})
		it('should detect code lines indented with spaces', () => {
			const baseDir = path.resolve('./test/data/nodejs/tabs_spaces_test');
			const sourcePath = path.join(baseDir, 'spaces.js');
			const coveragePath = path.join(baseDir, 'test-test-spaces/clover.xml');

			const {program, mocks} = createMocks();

			const coveredLines = program._findCoveredCodeLines('NODEJS', sourcePath, coveragePath);

			assert(coveredLines.includes(2));
		})
	});
});

describe('_findRegionTagsAndRanges', () => {
	describe('language-agnostic functionality', () => {
		it('should find region tags and ranges', () => {
			const baseDir = path.resolve('./test/data/nodejs/region_tags_test');
			const sourcePath = path.join(baseDir, 'index.js');

			const {program, mocks} = createMocks();

			const tagsAndRanges = program._findRegionTagsAndRanges('NODEJS', sourcePath);

			assert.equal(tagsAndRanges['app'], null, 'should exclude useless region tags');
			assert.deepStrictEqual(tagsAndRanges, [
				{return_one: [1, 5]},
				{return_two: [7, 11]}
			]);
		});
	});

	describe('helper method detection', () => {
		it('should detect + ignore helper methods in Python', () => {
			const baseDir = path.resolve('./test/data/python/helper_methods_test');
			const sourcePath = path.join(baseDir, 'main.py');

			const {program, mocks} = createMocks();

			const tagsAndRanges = program._findRegionTagsAndRanges('PYTHON', sourcePath);

			assert.deepStrictEqual(tagsAndRanges, [
				{method_one: [8, 11]},
				{method_two: [13, 16]}
			]);
		});

		it('should detect + ignore standard helper methods in Node.js', () => {
			const baseDir = path.resolve('./test/data/nodejs/helper_methods_test');
			const sourcePath = path.join(baseDir, 'index.js');

			const {program, mocks} = createMocks();

			const tagsAndRanges = program._findRegionTagsAndRanges('NODEJS', sourcePath);

			assert.deepStrictEqual(tagsAndRanges, [
				{method_one: [10, 17]},
				{method_two: [19, 26]}
			]);
		});

		it('should detect + ignore ExpressJS helper methods in Node.js', () => {
			const baseDir = path.resolve('./test/data/nodejs/helper_methods_express_test');
			const sourcePath = path.join(baseDir, 'index.js');

			const {program, mocks} = createMocks();

			const tagsAndRanges = program._findRegionTagsAndRanges('NODEJS', sourcePath);

			assert.equal(tagsAndRanges['setup'], null, 'should exclude region tags without req/res handlers')
			assert.deepStrictEqual(tagsAndRanges, [
				{handle_request: [12, 16]},
			]);
		});
	});
});

describe('getRegionTagsHitByTest', () => {
	it('should ignore blacklisted test files', () => {
		const baseDir = path.resolve('./test/data/nodejs/filename_blacklist_test');

		const {program, mocks} = createMocks();

		const tags = program.getRegionTagsHitByTest('NODEJS', baseDir, path.join(baseDir, 'clover.xml'))
		
		assert.equal(tags['loadable'], null, '"loadable" file should be blacklisted')
		assert.deepStrictEqual(tags, [
			{ index: [1, 5] }
		])
	});

	it('should WARN if source file has no region tags', () => {
		const baseDir = path.resolve('./test/data/nodejs/coverage_test');
		const sourceFile = path.join(baseDir, 'index.js');
		const coverageFile = path.join(baseDir, 'test-test-one/clover.xml');

		const {program, mocks} = createMocks();

		const tags = program.getRegionTagsHitByTest('NODEJS', baseDir, coverageFile)
		
		assert(mocks.console.log.calledWith(`WARN source file ${sourceFile} has no region tags!`));
	});

	it('should WARN if multiple source files are found', () => {
		const baseDir = path.resolve('./test/data/nodejs/tabs_spaces_test');
		const coverageFile = path.join(baseDir, 'all/clover.xml');

		const {program, mocks} = createMocks();

		program.getRegionTagsHitByTest('NODEJS', baseDir, coverageFile)

		assert(mocks.console.log.firstCall.args[0].includes('Multiple matching source files detected'));
	})

	it('should get region tags hit by test', () => {
		const baseDir = path.resolve('./test/data/nodejs/region_tags_test');
		const sourceFile = path.join(baseDir, 'index.js');
		const coverageFile = path.join(baseDir, 'clover.xml');

		const {program, mocks} = createMocks();

		const tags = program.getRegionTagsHitByTest('NODEJS', baseDir, coverageFile)

		assert(tags.some(t => !!t['return_one']), 'should detect first region tag');
		assert(tags.some(t => !!t['return_two']), 'should detect second region tag');
	});
});

describe('findClosingLine', () => {
	it('should find closing line in Node.js', () => {
		const sourceFile = path.resolve('./test/data/nodejs/basic_test/basic.test.js');
		const sourceLines = fs.readFileSync(sourceFile, 'utf-8').split('\n');

		const {program} = createMocks();

		assert.equal(program._findClosingBlock('NODEJS', sourceLines, 4), 6)
	})

	it('should find closing line in Ruby', () => {
		const sourceFile = path.resolve('./test/data/ruby/basic_test/spec/basic_spec.rb');
		const sourceLines = fs.readFileSync(sourceFile, 'utf-8').split('\n');

		const {program} = createMocks();

		assert.equal(program._findClosingBlock('RUBY', sourceLines, 4), 6)
	})

	it('should return null if no matching line is found', () => {
		const sourceFile = path.resolve('./test/data/nodejs/basic_test/basic.test.js');
		const sourceLines = fs.readFileSync(sourceFile, 'utf-8').split('\n');

		const {program} = createMocks();

		assert.equal(program._findClosingBlock('NODEJS', sourceLines, 9), null)
	})

	it('should throw error on unsupported language (PHP)', () => {
		const sourceFile = path.resolve('./test/data/php/basic_test/basicTest.php');

		const {program, mocks} = createMocks();

		assert.throws(() => {
			program._findClosingBlock('PHP', [], 0);
		}, 'Language not supported: PHP');
	});
});

describe('findPrecedingLine', () => {
	it('should find preceding line in Node.js', () => {
		const sourceFile = path.resolve('./test/data/nodejs/basic_test/basic.test.js');
		const sourceLines = fs.readFileSync(sourceFile, 'utf-8').split('\n');

		const {program} = createMocks();

		assert.equal(program._findPrecedingBlock('NODEJS', sourceLines, 8), 6)
	})

	it('should find preceding line in Ruby', () => {
		const sourceFile = path.resolve('./test/data/ruby/basic_test/spec/basic_spec.rb');
		const sourceLines = fs.readFileSync(sourceFile, 'utf-8').split('\n');

		const {program} = createMocks();

		assert.equal(program._findPrecedingBlock('RUBY', sourceLines, 8), 6)
	})

	it('should return null if no matching line is found', () => {
		const sourceFile = path.resolve('./test/data/nodejs/basic_test/basic.test.js');
		const sourceLines = fs.readFileSync(sourceFile, 'utf-8').split('\n');

		const {program} = createMocks();

		assert.equal(program._findPrecedingBlock('NODEJS', sourceLines, 2), null)
	})

	it('should throw error on unsupported language (PHP)', () => {
		const sourceFile = path.resolve('./test/data/php/basic_test/basicTest.php');

		const {program} = createMocks();

		assert.throws(() => {
			program._findPrecedingBlock('PHP', [], 0);
		}, 'Language not supported: PHP');
	});
});

describe('wrapIndividualTestInRegionTag', () => {
	describe('Node.js', () => {
		it('should wrap test with region tag in Node.js', async () => {
			const baseDir = path.resolve('./test/data/nodejs/basic_test');
			const testPath = path.join(baseDir, 'basic.test.js');

			const {program, mocks} = createMocks();

			await program.wrapIndividualTestInRegionTag(
				'NODEJS', testPath, 'test one', [{'tag_one': [4, 6]}]);

			const writtenLines = mocks.fs.writeFileSync.firstCall.args[1].split('\n');

			const newTagIndex = writtenLines.indexOf('describe(\'tag_one\', () => {');
			assert(newTagIndex > 0, 'new region tag was added');
			assert.equal(writtenLines[newTagIndex + 4], '});', 'region tag block was closed');
		})

		it('should do nothing if test is wrapped with the same set of region tags', async () => {
			const baseDir = path.resolve('./test/data/nodejs/region_tags_test');
			const testPath = path.join(baseDir, 'index.test.js');

			const {program, mocks} = createMocks();

			await program.wrapIndividualTestInRegionTag(
				'NODEJS', testPath, 'return_one', [{'region_tag': [5, 13]}, {'test': [5, 13]}]);

			assert(mocks.console.log.calledWith('    INFO Exact region tag already present, skipping.'));
			assert(mocks.fs.writeFileSync.notCalled);
		})

		it('should error if test is wrapped with an overlapping set of region tags', async () => {
			const baseDir = path.resolve('./test/data/nodejs/region_tags_test');
			const testPath = path.join(baseDir, 'index.test.js');

			const {program, mocks} = createMocks();

			await program.wrapIndividualTestInRegionTag(
				'NODEJS', testPath, 'return_one', [{'region_tag': [5, 13]}]);

			assert(mocks.console.log.calledWith('ERR Different region tags present, label manually!'));
			assert(mocks.fs.writeFileSync.notCalled);
		})
	})

	describe('Python', () => {
		it('should wrap test with region tag in Python', async () => {
			const baseDir = path.resolve('./test/data/python/coverage_test');
			const testPath = path.join(baseDir, 'coverage_test.py');

			const {program, mocks} = createMocks();

			await program.wrapIndividualTestInRegionTag(
				'PYTHON', testPath, 'test_one', [{'tag_one': [6, 7]}]);

			const writtenLines = mocks.fs.writeFileSync.firstCall.args[1].split('\n');

			const newTagIndex = writtenLines.indexOf('class TestTagOne(unittest.TestCase):');
			assert(newTagIndex > 0, 'new region tag was added');
			assert.equal(writtenLines[newTagIndex + 1], '\tdef test_one(self):');
			assert(writtenLines[newTagIndex + 2].startsWith('\t\t'), 'block was indented correctly')
		})

		it('should include decorators in wrapped test', async () => {
			const baseDir = path.resolve('./test/data/python/coverage_test');
			const testPath = path.join(baseDir, 'coverage_test.py');

			const {program, mocks} = createMocks();

			// region should start on the 'def'-containing line (below any decorators)
			await program.wrapIndividualTestInRegionTag(
				'PYTHON', testPath, 'test_two', [{'tag_two': [10, 11]}]);

			const writtenLines = mocks.fs.writeFileSync.firstCall.args[1].split('\n');

			const newTagIndex = writtenLines.indexOf('class TestTagTwo(unittest.TestCase):');
			assert(newTagIndex > 0, 'new region tag was added');
			assert.equal(writtenLines[newTagIndex + 1], '\t@pytest.mark.skipif(False)');
			assert.equal(writtenLines[newTagIndex + 2], '\tdef test_two(self):');
		})

		it('should error if a test is already wrapped in a non-matching block', async () => {
			const baseDir = path.resolve('./test/data/python/basic_test');
			const testPath = path.join(baseDir, 'basic_test.py');

			const {program, mocks} = createMocks();

			// region should start on the 'def'-containing line (below any decorators)
			await program.wrapIndividualTestInRegionTag(
				'PYTHON', testPath, 'test_one', [{'tag_two': [5, 6]}]);

			assert(mocks.console.log.calledWith('ERR Python test is already in an indented block!'));
		})
	})

	describe('PHP', () => {
		it('should wrap test with region tag in PHP', async () => {
			const baseDir = path.resolve('./test/data/php/basic_test');
			const testPath = path.join(baseDir, 'basicTest.php');

			const {program, mocks} = createMocks();

			await program.wrapIndividualTestInRegionTag(
				'PHP', testPath, 'testOne', [{'tag_one': [4, 7]}]);

			const fileLines = fs.readFileSync(testPath, 'utf-8').split('\n');
			const writtenLines = mocks.fs.writeFileSync.firstCall.args[1].split('\n');

			const newTagIndex = writtenLines.some(l => l.endsWith('function test_tag_one_SHOULD_testOne()'));
			assert(newTagIndex > 0, 'new region tag was added');
			assert.equal(writtenLines.length, fileLines.length, 'no brackets were added');
		})

		it('should not modify an already-wrapped test', async () => {
			const baseDir = path.resolve('./test/data/php/coverage_test');
			const testPath = path.join(baseDir, 'coverageTest.php');

			const {program, mocks} = createMocks();

			await program.wrapIndividualTestInRegionTag(
				'PHP', testPath, 'test_tag_two_SHOULD_testTwo', [{'test_tag_two_SHOULD_testTwo': [17, 20]}]);

			assert(mocks.fs.writeFileSync.notCalled);
		});

		it('should error if a test is already wrapped in a non-matching class', async () => {
			const baseDir = path.resolve('./test/data/php/coverage_test');
			const testPath = path.join(baseDir, 'coverageTest.php');

			const {program, mocks} = createMocks();

			await program.wrapIndividualTestInRegionTag(
				'PHP', testPath, 'test_tag_two_SHOULD_testTwo', [{'tag_two': [17, 20]}, {'tag_one': [17, 20]}]);

			assert(mocks.console.log.calledWith('ERR Different region tags present, label manually!'));
			assert(mocks.fs.writeFileSync.notCalled);
		});
	})

	describe('Ruby', () => {
		it('should wrap test with region tag in Ruby', async () => {
			const baseDir = path.resolve('./test/data/ruby/basic_test');
			const testPath = path.join(baseDir, 'spec/basic_spec.rb');

			const {program, mocks} = createMocks();

			await program.wrapIndividualTestInRegionTag(
				'RUBY', testPath, 'test one', [{'tag_one': [4, 6]}]);

			const fileLines = fs.readFileSync(testPath, 'utf-8').split('\n');
			const writtenLines = mocks.fs.writeFileSync.firstCall.args[1].split('\n');

			const newTagIndex = writtenLines.indexOf('describe "tag_one" do');
			assert(newTagIndex > 0, 'new region tag was added');
			assert.equal(writtenLines.length, fileLines.length + 2, 'region tag block was closed'); 
		});
	})
})

describe('dedupeRegionTags', () => {
	describe('Basic functionality', () => {
		it('should remove nested duplicate region tags in Node', () => {
			const testPath = path.resolve('./test/data/nodejs/duplicate_tags_test/nested.test.js');

			const {program, mocks} = createMocks();

			program.dedupeRegionTags('NODEJS', testPath)

			const fileLines = fs.readFileSync(testPath, 'utf-8').split('\n');
			const writtenLines = mocks.fs.writeFileSync.firstCall.args[1].split('\n');
			
			const blockTerminatingLine = '});';
			assert.equal(writtenLines.filter(line => line.includes('describe(\'region_tag ')).length, 1)
			assert.equal(
				writtenLines.filter(l => l === blockTerminatingLine).length,
				fileLines.filter(l => l === blockTerminatingLine).length - 1,
				'should remove ending (top-level) bracket'
			);
		})

		it('should remove contiguous duplicate region tags', () => {
			const testPath = path.resolve('./test/data/nodejs/duplicate_tags_test/contiguous.test.js');

			const {program, mocks} = createMocks();

			program.dedupeRegionTags('NODEJS', testPath)

			const fileLines = fs.readFileSync(testPath, 'utf-8').split('\n');
			const writtenLines = mocks.fs.writeFileSync.firstCall.args[1].split('\n');
			
			const blockTerminatingLine = '});';
			assert.equal(writtenLines.filter(line => line.includes('describe(\'region_tag ')).length, 1)
			assert.equal(
				writtenLines.filter(l => l === blockTerminatingLine).length,
				fileLines.filter(l => l === blockTerminatingLine).length - 1,
				'should remove in-between (top-level) bracket'
			);
		})

		it('should ignore non-duplicate region tags', () => {
			const testPath = path.resolve('./test/data/nodejs/region_tags_test/index.test.js');

			const {program, mocks} = createMocks();

			program.dedupeRegionTags('NODEJS', testPath)

			const fileLines = fs.readFileSync(testPath, 'utf-8').split('\n');
			const writtenLines = mocks.fs.writeFileSync.firstCall.args[1].split('\n');
			
			assert.equal(writtenLines.filter(line => line.includes('describe(\'region_tag ')).length, 1)
		})
	});

	describe('Region terminator removal', () => {
		it('should remove preceding region terminator in Node.js', () => {
			const testPath = path.resolve('./test/data/nodejs/duplicate_tags_test/nested.test.js');

			const {program, mocks} = createMocks();

			program.dedupeRegionTags('NODEJS', testPath)

			const fileLines = fs.readFileSync(testPath, 'utf-8').split('\n');
			const writtenLines = mocks.fs.writeFileSync.firstCall.args[1].split('\n');
			
			const blockTerminatingLine = '});';

			assert.equal(
				writtenLines.filter(l => l === blockTerminatingLine).length,
				fileLines.filter(l => l === blockTerminatingLine).length - 1,
				'should remove ending (top-level) bracket'
			);
			assert.equal(writtenLines.length, fileLines.length - 2);
		});

		it('should remove preceding region terminator in Ruby', () => {
			const testPath = path.resolve('./test/data/ruby/duplicate_tags_test/nested_spec.rb');

			const {program, mocks} = createMocks();

			mocks.execPromise

			program.dedupeRegionTags('RUBY', testPath)

			const fileLines = fs.readFileSync(testPath, 'utf-8').split('\n');
			const writtenLines = mocks.fs.writeFileSync.firstCall.args[1].split('\n');
			
			const blockTerminatingLine = 'end';
			assert.equal(
				writtenLines.filter(l => l === blockTerminatingLine).length,
				fileLines.filter(l => l === blockTerminatingLine).length - 1,
				'should remove ending (top-level) "end" statement'
			);
			assert.equal(writtenLines.length, fileLines.length - 2);
		});
	})
})

describe('generateTestList', () => {
	it('should execute commands', async () => {
		const {program, mocks} = createMocks(true);
		const baseDir = 'foo/bar/baz';

		await program.generateTestList('NODEJS', baseDir);
		assert(mocks.execPromise.calledWith(
			`mocha --reporter xunit --timeout 30s --exit --reporter-option="output=all-tests.xml"`,
			{cwd: baseDir}
		));

		await program.generateTestList('PYTHON', baseDir);
		assert(mocks.execPromise.calledWith(
			`pytest --junitxml=all-tests.xml --cov=. --cov-report xml`,
			{cwd: baseDir}
		));

		await program.generateTestList('RUBY', baseDir);
		assert(mocks.execPromise.calledWith(
			`bundle exec "rspec --format RspecJunitFormatter --out all-tests.xml"`,
			{cwd: baseDir}
		));

		await program.generateTestList('PHP', baseDir);
		assert(mocks.execPromise.calledWith(
			`~/.composer/vendor/bin/phpunit ${baseDir}/test --verbose --log-junit ${baseDir}/all-tests.xml`,
			{cwd: path.dirname(baseDir)}
		));
	});
})

describe('_getLanguageForDirectory', () => {
	it('should auto-detect language', () => {
		const {program} = createMocks();

		assert.equal(program._getLanguageForDirectory('nodejs-docs-samples'), 'NODEJS');
		assert.equal(program._getLanguageForDirectory('python-docs-samples'), 'PYTHON');
		assert.equal(program._getLanguageForDirectory('ruby-docs-samples'), 'RUBY');
		assert.equal(program._getLanguageForDirectory('php-docs-samples'), 'PHP');
	});

	it('should return null for unrecognized languages', () => {
		const {program} = createMocks();

		assert.equal(program._getLanguageForDirectory('dotnet-docs-samples'), null);
	});
});

describe('perDirMain integration test', () => {
	it('should do nothing if file already has region tags', async () => {
		const {program, mocks} = createMocks(true,  true);

		mocks.execPromise = sinon.stub().resolves()

		const baseDir = path.resolve('./test/data/nodejs/per_dir_main_test') // expects test subdir, TODO find actual baseDir

		await program.perDirMain(baseDir);

		const fileLines = fs.readFileSync(path.join(baseDir, 'test/index.test.js'), 'utf-8');
		const writtenLines = mocks.fs.writeFileSync.getCall(0).args[1];
		assert.deepStrictEqual(fileLines, writtenLines);
	})
})