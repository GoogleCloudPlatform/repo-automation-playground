const assert = require('assert');

describe('basic test', () => {
	before(() => {
		assert.strictEqual(1, 1);
	});

	it('should only detect this test', () => {
		assert.strictEqual(2, 2);
	});

	after(() => {
		assert.strictEqual(3, 3);
	});
});