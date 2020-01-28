import pytest
import unittest

class BasicTest(unittest.TestCase):
	def test_one(self):
		assert 1 == 1

	def test_two(self):
		assert 2 == 2