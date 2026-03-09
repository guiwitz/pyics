"""
Input/Output functions for reading and writing ICS/IDS format files.
"""

import ctypes
import numpy as np
from typing import Tuple

from .constants import (
    ICS_DTYPES,
    NUMPY_TO_ICS,
    ICS_COMPRESSION_UNCOMPRESSED,
    ICS_COMPRESSION_GZIP,
    ICS_MAXDIM
)
from .library import ICSError
from .utils import get_library, fix_dimension_order


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
    lib = get_library()
    
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
            image = fix_dimension_order(image, dim_orders, dim_labels)
        
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
    lib = get_library()
    
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
