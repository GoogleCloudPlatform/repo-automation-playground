import pytest
import unittest


# Region tag in class name (in CapWords case)
class RegionTag(unittest.TestCase):
	def test_should_pass(self):
		pass

	def test_should_fail(self):
		self.fail('top-level region tag')