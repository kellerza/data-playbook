"""Tests for data.py"""
from dataplaybook import DataPlaybook


def test_from_str():
    txt = """
    """
    _dt = DataPlaybook(yaml_text=txt)
