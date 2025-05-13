"""
Featherflow: Ultra-lightweight workflow orchestration tool

A minimalist alternative to Airflow using only Python standard libraries
"""

__version__ = "0.1.0"

from .core import featherflow
from .parser import parse_flow

__all__ = ["featherflow", "parse_flow"]