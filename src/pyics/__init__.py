"""
Python wrapper for libics - Image Cytometry Standard file reading library.

This module provides a Python interface to read and write ICS/IDS format images
as numpy arrays.
"""

try:
    from ._version import version as __version__
except ImportError:
    __version__ = "0.0.0+unknown"

__author__ = "ICS Wrapper Contributors"
__license__ = "LGPL-2.0-or-later"

import ctypes
import numpy as np
import os
import platform
from typing import Tuple, Optional
from pathlib import Path


# Data type mapping from ICS to numpy
ICS_DTYPES = {
    1: np.uint8,    # Ics_uint8
    2: np.int8,     # Ics_sint8
    3: np.uint16,   # Ics_uint16
    4: np.int16,    # Ics_sint16
    5: np.uint32,   # Ics_uint32
    6: np.int32,    # Ics_sint32
    7: np.uint64,   # Ics_uint64
    8: np.int64,    # Ics_sint64
    9: np.float16,  # Ics_real16
    10: np.float32, # Ics_real32
    11: np.float64, # Ics_real64
    12: np.complex64,  # Ics_complex32
    13: np.complex128, # Ics_complex64
}

# Reverse mapping
NUMPY_TO_ICS = {v: k for k, v in ICS_DTYPES.items()}

# Compression methods
ICS_COMPRESSION_UNCOMPRESSED = 0
ICS_COMPRESSION_COMPRESS = 1
ICS_COMPRESSION_GZIP = 2

# Maximum dimensions
ICS_MAXDIM = 10


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


# Global library instance
_lib_instance = None


def _fix_dimension_order(image: np.ndarray, dim_orders: list, dim_labels: list) -> np.ndarray:
    """
    Attempt to reorder dimensions to standard microscopy format.
    
    Standard order: (Z, Channel, Y, X) for 4D or similar nesting for other dimensions.
    
    Parameters:
    -----------
    image : np.ndarray
        The image array
    dim_orders : list
        List of dimension order strings (e.g., 'x', 'y', 'z', 't')
    dim_labels : list
        List of dimension labels
    
    Returns:
    --------
    np.ndarray
        Reordered image array
    """
    if len(dim_orders) <= 2:
        return image  # 2D images don't need reordering
    
    # Map dimension types to their indices
    # Prioritize non-singleton dimensions when there are conflicts
    dim_map = {}
    dim_sizes = image.shape
    
    for i, (order, label) in enumerate(zip(dim_orders, dim_labels)):
        order_lower = order.lower()
        dim_size = dim_sizes[i]
        
        # Helper to update mapping only if better than existing
        def update_if_better(key, idx, size):
            if key not in dim_map:
                dim_map[key] = idx
            else:
                # Prefer non-singleton dimensions
                existing_size = dim_sizes[dim_map[key]]
                if existing_size == 1 and size > 1:
                    dim_map[key] = idx
        
        # Identify dimension types
        if order_lower == 'x':
            update_if_better('x', i, dim_size)
        elif order_lower == 'y':
            update_if_better('y', i, dim_size)
        elif order_lower == 'z':
            update_if_better('z', i, dim_size)
        elif order_lower in ['t', 'time']:
            update_if_better('t', i, dim_size)
        elif order_lower in ['ch', 'c', 'channel'] or 'channel' in label.lower():
            update_if_better('ch', i, dim_size)
        elif order_lower in ['p', 'probe']:
            update_if_better('ch', i, dim_size)  # Treat probe as channel
    
    # Only reorder if we have at least x and y
    if 'x' not in dim_map or 'y' not in dim_map:
        return image  # Can't determine spatial dimensions
    
    # For ICS files with interleaved data, we need to use reshape, not transpose
    # Build new shape in order: (t, ch, z, y, x) skipping singletons
    # This matches the actual memory layout of ICS files
    new_shape = []
    new_order_labels = []
    
    # Add time if present and non-singleton
    if 't' in dim_map and dim_sizes[dim_map['t']] > 1:
        new_shape.append(dim_sizes[dim_map['t']])
        new_order_labels.append('t')
    
    # Add channel if present and non-singleton
    if 'ch' in dim_map and dim_sizes[dim_map['ch']] > 1:
        new_shape.append(dim_sizes[dim_map['ch']])
        new_order_labels.append('ch')
    
    # Add z if present and non-singleton
    if 'z' in dim_map and dim_sizes[dim_map['z']] > 1:
        new_shape.append(dim_sizes[dim_map['z']])
        new_order_labels.append('z')
    
    # Add y and x (always include spatial dimensions)
    new_shape.append(dim_sizes[dim_map['y']])
    new_order_labels.append('y')
    new_shape.append(dim_sizes[dim_map['x']])
    new_order_labels.append('x')
    
    # Check if reshape is needed
    if tuple(new_shape) == image.shape:
        return image  # Already correct
    
    # Use reshape to reinterpret the data layout
    # This works for ICS files where data is stored with fast-varying dimensions
    try:
        # Verify total size matches
        if np.prod(new_shape) == image.size:
            reordered = np.reshape(image, new_shape)
            return reordered
        else:
            # Size mismatch, just squeeze singletons
            return np.squeeze(image)
    except Exception:
        # If reshape fails, return squeezed original
        return np.squeeze(image)


def _get_library() -> ICSLibrary:
    """Get or create the global library instance."""
    global _lib_instance
    if _lib_instance is None:
        _lib_instance = ICSLibrary()
    return _lib_instance


def imread(filename: str, fix_dimensions: bool = True) -> Tuple[np.ndarray, dict]:
    """
    Read an ICS/IDS format image file.
    
    Parameters:
    -----------
    filename : str
        Path to the ICS file (with or without .ics extension)
    fix_dimensions : bool, optional
        If True (default), attempts to reorder dimensions to standard microscopy format
        (Z, Channel, Y, X for 4D, or similar). If False, returns dimensions as stored.
    
    Returns:
    --------
    image : np.ndarray
        The image data as a numpy array
    metadata : dict
        Dictionary containing image metadata including:
        - dtype: numpy data type
        - ndims: number of dimensions
        - dimensions: original dimension sizes
        - dim_labels: dimension labels (e.g., 'x', 'y', 'z', 'ch', 't')
        - dim_order: dimension order strings
        - data_size: total data size in bytes
        - original_shape: shape before any reordering
    
    Examples:
    ---------
    >>> image, metadata = imread('myimage.ics')
    >>> print(f"Image shape: {image.shape}")
    >>> print(f"Dimension labels: {metadata['dim_labels']}")
    >>> print(f"Data type: {metadata['dtype']}")
    
    >>> # Read without automatic dimension fixing
    >>> image, metadata = imread('myimage.ics', fix_dimensions=False)
    """
    lib = _get_library()
    
    # Open the file
    ics_ptr = ctypes.c_void_p()
    filename_bytes = filename.encode('utf-8')
    error = lib.lib.IcsOpen(ctypes.byref(ics_ptr), filename_bytes, b"r")
    lib.check_error(error)
    
    try:
        # Get image layout
        dt = ctypes.c_int()
        ndims = ctypes.c_int()
        dims = (ctypes.c_size_t * ICS_MAXDIM)()
        
        error = lib.lib.IcsGetLayout(ics_ptr, ctypes.byref(dt), 
                                     ctypes.byref(ndims), ctypes.byref(dims))
        lib.check_error(error)
        
        # Convert dimensions to Python list
        dimensions = [dims[i] for i in range(ndims.value)]
        
        # Get dimension labels and order
        dim_labels = []
        dim_orders = []
        for i in range(ndims.value):
            order_buf = ctypes.create_string_buffer(32)
            label_buf = ctypes.create_string_buffer(32)
            error = lib.lib.IcsGetOrder(ics_ptr, i, order_buf, label_buf)
            if error == 0:  # IcsErr_Ok
                dim_orders.append(order_buf.value.decode('utf-8'))
                dim_labels.append(label_buf.value.decode('utf-8'))
            else:
                dim_orders.append('')
                dim_labels.append('')
        
        # Get data type
        if dt.value not in ICS_DTYPES:
            raise ICSError(f"Unsupported data type: {dt.value}")
        
        numpy_dtype = ICS_DTYPES[dt.value]
        
        # Get data size and allocate buffer
        data_size = lib.lib.IcsGetDataSize(ics_ptr)
        
        # Create numpy array
        image = np.empty(dimensions, dtype=numpy_dtype)
        
        # Read data
        error = lib.lib.IcsGetData(ics_ptr, 
                                   image.ctypes.data_as(ctypes.c_void_p),
                                   data_size)
        lib.check_error(error)
        
        # Store original shape
        original_shape = image.shape
        
        # Attempt to fix dimension ordering if requested
        if fix_dimensions and ndims.value > 2:
            image = _fix_dimension_order(image, dim_orders, dim_labels)
        
        # Prepare metadata
        metadata = {
            'dtype': numpy_dtype,
            'ndims': ndims.value,
            'dimensions': dimensions,
            'dim_labels': dim_labels,
            'dim_order': dim_orders,
            'data_size': data_size,
            'original_shape': original_shape,
            'shape': image.shape
        }
        
        return image, metadata
        
    finally:
        # Close the file
        error = lib.lib.IcsClose(ics_ptr)
        lib.check_error(error)


def imwrite(filename: str, image: np.ndarray, compression: str = 'none'):
    """
    Write a numpy array to an ICS/IDS format image file.
    
    Parameters:
    -----------
    filename : str
        Path to the output ICS file (with or without .ics extension)
    image : np.ndarray
        The image data to write
    compression : str, optional
        Compression method: 'none', 'gzip'. Default is 'none'.
    
    Examples:
    ---------
    >>> image = np.random.randint(0, 255, (100, 100), dtype=np.uint8)
    >>> imwrite('output.ics', image)
    >>> imwrite('output_compressed.ics', image, compression='gzip')
    """
    lib = _get_library()
    
    # Check if dtype is supported
    if image.dtype.type not in NUMPY_TO_ICS:
        raise ICSError(
            f"Unsupported numpy dtype: {image.dtype}. "
            f"Supported types: {list(NUMPY_TO_ICS.keys())}"
        )
    
    # Map compression
    compression_map = {
        'none': ICS_COMPRESSION_UNCOMPRESSED,
        'uncompressed': ICS_COMPRESSION_UNCOMPRESSED,
        'gzip': ICS_COMPRESSION_GZIP,
    }
    
    if compression.lower() not in compression_map:
        raise ValueError(
            f"Invalid compression '{compression}'. "
            f"Valid options: {list(compression_map.keys())}"
        )
    
    compression_method = compression_map[compression.lower()]
    
    # Open file for writing
    ics_ptr = ctypes.c_void_p()
    filename_bytes = filename.encode('utf-8')
    error = lib.lib.IcsOpen(ctypes.byref(ics_ptr), filename_bytes, b"w2")
    lib.check_error(error)
    
    try:
        # Set layout
        ics_dtype = NUMPY_TO_ICS[image.dtype.type]
        ndims = len(image.shape)
        dims = (ctypes.c_size_t * ndims)(*image.shape)
        
        error = lib.lib.IcsSetLayout(ics_ptr, ics_dtype, ndims, dims)
        lib.check_error(error)
        
        # Set compression
        error = lib.lib.IcsSetCompression(ics_ptr, compression_method, 0)
        lib.check_error(error)
        
        # Set data
        data_size = image.nbytes
        
        # Make sure array is contiguous
        if not image.flags['C_CONTIGUOUS']:
            image = np.ascontiguousarray(image)
        
        error = lib.lib.IcsSetData(ics_ptr,
                                   image.ctypes.data_as(ctypes.c_void_p),
                                   data_size)
        lib.check_error(error)
        
    finally:
        # Close the file (this actually writes the data)
        error = lib.lib.IcsClose(ics_ptr)
        lib.check_error(error)


def set_library_path(path: str):
    """
    Set the path to the libics shared library.
    
    Parameters:
    -----------
    path : str
        Path to the libics shared library file
    """
    global _lib_instance
    _lib_instance = ICSLibrary(path)


if __name__ == "__main__":
    print("ICS Library Python Wrapper")
    print("=" * 50)
    print("Usage:")
    print("  from pyics import imread, imwrite")
    print("  image, metadata = imread('myimage.ics')")
    print("  imwrite('output.ics', image)")
