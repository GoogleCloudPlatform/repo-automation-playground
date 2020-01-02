const assert = require('assert');

const lib = require('..');

describe('some test', () => {
describe('return_one', () => {
	it('return_one', () => {
		assert.strictEqual(lib.returnOne(), 1);
	});
});

describe('return_two', () => {
	it('return_two', () => {
		assert.strictEqual(lib.returnTwo(), 2);
	});
});
});