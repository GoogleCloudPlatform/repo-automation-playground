const assert = require('assert');
const loadable = require('./loadable.js');
const index = require('./index.js');

describe('filename denylist test', () => {
	it('test loadable', () => {
		assert.strictEqual(loadable.returnLoadable(), 'loadable');
	});

	it('test index', () => {
		assert.strictEqual(index.returnIndex(), 'index');
	});
});