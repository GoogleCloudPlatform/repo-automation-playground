<?php
use PHPUnit\Framework\TestCase;

class RegionTag extends TestCase
{
	public function testPass() {
		$this->expectNotToPerformAssertions();
	}

	public function testFail() {
		$this->fail('foo');
	}
}