const assert = require('assert');

const tabs = require('./tabs');
const spaces = require('./spaces');

describe('basic test', () => {
	it('test tabs', () => {
		assert.strictEqual(tabs.returnTabs(), 'tabs');
	});

	it('test spaces', () => {
		assert.strictEqual(spaces.returnSpaces(), 'spaces');
	});
});