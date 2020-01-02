<?php

use PHPUnit\Framework\TestCase;

class basicTest extends TestCase
{
    public function testOne()
    {
    	$this->assertEquals(1, 1);
    }

    /**
     * @depends testOne
     */
    public function testTwo()
    {
    	$this->assertEquals(2, 2);
    }
}