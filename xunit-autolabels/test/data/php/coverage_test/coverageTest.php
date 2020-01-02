<?php

use PHPUnit\Framework\TestCase;

include 'coverage.php';

class CoverageTest extends TestCase
{
    public function testOne()
    {
    	$this->assertEquals(CoverageMethods::returnOne(), 1);
    }

    /**
     * @depends testOne
     */
    public function test_tag_two_SHOULD_testTwo()
    {
    	$this->assertEquals(CoverageMethods::returnTwo(), 2);
    }
}