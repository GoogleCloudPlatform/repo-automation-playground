'use strict'

const assert = require('assert');

/* Region tag in top-level 'describe' */
describe('region_tag', () => {
	describe('bar baz', () => {
		it('should pass', () => {
			assert.ok(true);
		});

		it('should fail', () => {
			assert.fail('top-level region tag');
		});
	});
});
