import pytest
import unittest

import coverage_main

def test_one():
	assert coverage_main.return_one() == 1

@pytest.mark.skipif(False)
def test_two():
	assert coverage_main.return_two() == 2