const assert = require('assert');
const index = require('.')

describe('basic test', () => {
	it('test one', () => {
		assert.strictEqual(index.returnOne(), 1);
	});

	it('test two', () => {
		assert.strictEqual(index.returnTwo(), 2);
	});
});