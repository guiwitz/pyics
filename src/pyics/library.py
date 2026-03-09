"""
Low-level wrapper for the libics C library.
"""

import ctypes
import platform
from pathlib import Path
from typing import Optional

from .constants import ICS_MAXDIM


class ICSError(Exception):
    """Exception raised for ICS library errors."""
    pass


class ICSLibrary:
    """Wrapper for the libics C library."""
    
    def __init__(self, lib_path: Optional[str] = None):
        """
        Initialize the ICS library wrapper.
        
        Parameters:
        -----------
        lib_path : str, optional
            Path to the libics shared library. If None, tries to find it automatically.
        """
        if lib_path is None:
            lib_path = self._find_library()
        
        self.lib = ctypes.CDLL(lib_path)
        self._setup_functions()
    
    def _find_library(self) -> str:
        """Find the libics shared library."""
        system = platform.system()
        
        # Common library names by platform
        if system == "Windows":
            lib_names = ["libics.dll", "ics.dll"]
        elif system == "Darwin":  # macOS
            lib_names = ["libics.dylib", "libics.0.dylib", "libics.so"]
        else:  # Linux and others
            lib_names = ["libics.so", "libics.so.2", "libics.so.1", "libics.so.0"]
        
        # Search in common locations
        search_paths = [
            Path(__file__).parent,
            Path(__file__).parent / "libics" / ".libs",
            Path(__file__).parent / "build",
            Path("/usr/local/lib"),
            Path("/usr/lib"),
        ]
        
        for path in search_paths:
            if not path.exists():
                continue
            for lib_name in lib_names:
                lib_path = path / lib_name
                if lib_path.exists():
                    return str(lib_path)
        
        raise ICSError(
            f"Could not find libics shared library. "
            f"Please compile it first or provide the path explicitly."
        )
    
    def _setup_functions(self):
        """Setup function signatures for the C library."""
        # IcsOpen
        self.lib.IcsOpen.argtypes = [
            ctypes.POINTER(ctypes.c_void_p),  # ICS**
            ctypes.c_char_p,                  # const char* filename
            ctypes.c_char_p                   # const char* mode
        ]
        self.lib.IcsOpen.restype = ctypes.c_int
        
        # IcsClose
        self.lib.IcsClose.argtypes = [ctypes.c_void_p]  # ICS*
        self.lib.IcsClose.restype = ctypes.c_int
        
        # IcsGetLayout
        self.lib.IcsGetLayout.argtypes = [
            ctypes.c_void_p,                           # const ICS*
            ctypes.POINTER(ctypes.c_int),              # Ics_DataType*
            ctypes.POINTER(ctypes.c_int),              # int* ndims
            ctypes.POINTER(ctypes.c_size_t * ICS_MAXDIM)  # size_t* dims
        ]
        self.lib.IcsGetLayout.restype = ctypes.c_int
        
        # IcsGetDataSize
        self.lib.IcsGetDataSize.argtypes = [ctypes.c_void_p]  # const ICS*
        self.lib.IcsGetDataSize.restype = ctypes.c_size_t
        
        # IcsGetData
        self.lib.IcsGetData.argtypes = [
            ctypes.c_void_p,   # ICS*
            ctypes.c_void_p,   # void* dest
            ctypes.c_size_t    # size_t n
        ]
        self.lib.IcsGetData.restype = ctypes.c_int
        
        # IcsSetLayout
        self.lib.IcsSetLayout.argtypes = [
            ctypes.c_void_p,                           # ICS*
            ctypes.c_int,                              # Ics_DataType
            ctypes.c_int,                              # int ndims
            ctypes.POINTER(ctypes.c_size_t)            # const size_t* dims
        ]
        self.lib.IcsSetLayout.restype = ctypes.c_int
        
        # IcsSetData
        self.lib.IcsSetData.argtypes = [
            ctypes.c_void_p,   # ICS*
            ctypes.c_void_p,   # const void* src
            ctypes.c_size_t    # size_t n
        ]
        self.lib.IcsSetData.restype = ctypes.c_int
        
        # IcsSetCompression
        self.lib.IcsSetCompression.argtypes = [
            ctypes.c_void_p,   # ICS*
            ctypes.c_int,      # Ics_Compression
            ctypes.c_int       # int level
        ]
        self.lib.IcsSetCompression.restype = ctypes.c_int
        
        # IcsGetErrorText
        self.lib.IcsGetErrorText.argtypes = [ctypes.c_int]  # Ics_Error
        self.lib.IcsGetErrorText.restype = ctypes.c_char_p
        
        # IcsGetOrder (for dimension labels)
        self.lib.IcsGetOrder.argtypes = [
            ctypes.c_void_p,        # const ICS*
            ctypes.c_int,           # int dimension
            ctypes.c_char_p,        # char* order
            ctypes.c_char_p         # char* label
        ]
        self.lib.IcsGetOrder.restype = ctypes.c_int
    
    def get_error_text(self, error_code: int) -> str:
        """Get error message for an error code."""
        msg = self.lib.IcsGetErrorText(error_code)
        return msg.decode('utf-8') if msg else f"Unknown error (code: {error_code})"
    
    def check_error(self, error_code: int):
        """Check error code and raise exception if needed."""
        if error_code != 0:  # IcsErr_Ok = 0
            raise ICSError(f"ICS Error: {self.get_error_text(error_code)}")
