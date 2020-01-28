const assert = require('assert');

const lib = require('./index.js');

describe('region_tag test', () => {
	it('return_one', () => {
		assert.strictEqual(lib.returnOne(), 1);
	});

	it('return_two', () => {
		assert.strictEqual(lib.returnTwo(), 2);
	});
});