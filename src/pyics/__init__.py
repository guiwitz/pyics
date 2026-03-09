"""
Python wrapper for libics - Image Cytometry Standard file reading library.

This module provides a Python interface to read and write ICS/IDS format images
as numpy arrays.
"""

# Version information
try:
    from ._version import version as __version__
except ImportError:
    __version__ = "0.0.0+unknown"

__author__ = "Guillaume Witz"
__license__ = "LGPL-2.0-or-later"

# Import public API
from .io import imread, imwrite
from .library import ICSError, ICSLibrary
from .utils import set_library_instance

# Re-export main functions for convenience
__all__ = [
    'imread',
    'imwrite',
    'ICSError',
    'ICSLibrary',
    'set_library_instance',
    '__version__',
]
