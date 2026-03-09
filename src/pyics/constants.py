"""
Constants and type mappings for the ICS library.
"""

import numpy as np


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
