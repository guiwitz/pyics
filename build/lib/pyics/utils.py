"""
Utility functions for dimension handling and library management.
"""

import numpy as np
from typing import Optional

from .library import ICSLibrary


# Global library instance
_lib_instance = None


def get_library() -> ICSLibrary:
    """Get or create the global library instance."""
    global _lib_instance
    if _lib_instance is None:
        _lib_instance = ICSLibrary()
    return _lib_instance


def set_library_instance(lib: Optional[ICSLibrary]):
    """Set the global library instance."""
    global _lib_instance
    _lib_instance = lib


def fix_dimension_order(image: np.ndarray, dim_orders: list, dim_labels: list) -> np.ndarray:
    """
    Attempt to reorder dimensions to standard microscopy format.
    
    Standard order: (Time, Channel, Z, Y, X) for multi-dimensional images.
    
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
