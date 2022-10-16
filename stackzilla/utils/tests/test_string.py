"""Tests for the string module."""
from stackzilla.utils.string import removeprefix

TEST_STR = '_prefix_value'
TEST_UNMODIFIED_STR = 'value_prefix_'
TEST_PREFIX = '_prefix_'

def test_string():
    """Verify basic functionality of the removeprefix function."""
    result = removeprefix(string=TEST_STR, prefix=TEST_PREFIX)
    assert result == 'value'

def test_empty_string():
    """Make sure empty strings are handled."""
    result = removeprefix(string='', prefix=TEST_PREFIX)
    assert result == ''

def test_empty_prefix():
    """Verify empty prefixes are handled."""
    result = removeprefix(string=TEST_STR, prefix='')
    assert result == TEST_STR

def test_missing_prefix():
    """Make sure that if the prefix is anywhere but at the beginning, nothing happens."""
    result = removeprefix(string=TEST_UNMODIFIED_STR, prefix=TEST_PREFIX)
    assert result == TEST_UNMODIFIED_STR
