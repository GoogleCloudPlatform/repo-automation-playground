<?php

namespace Google\Cloud\Samples\Spanner;
use Google\Cloud\TestUtils\TestTrait;
use PHPUnit\Framework\TestCase;

class outOfOrderTest extends TestCase
{
    /**
     * @depends testOne
     */
    public function testTwo()
    {
        $this->assertEquals(2, 2);
    }

    public function testOne()
    {
    	$this->assertEquals(1, 1);
    }
}