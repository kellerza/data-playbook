"""Tests for data.py"""
from dataplaybook import DataPlaybook


def test_from_str():
    """Test starting from string."""
    txt = """
        tasks:
    """
    _dt = DataPlaybook(yaml_text=txt)
