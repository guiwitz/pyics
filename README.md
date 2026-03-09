# ICS Python Wrapper

A Python wrapper for [libics](https://github.com/svi-opensource/libics) - the Image Cytometry Standard (ICS) file format library. This wrapper provides a simple interface to read and write ICS/IDS format images directly as numpy arrays.

## Features

- 🔄 Read ICS/IDS format images directly as numpy arrays
- 💾 Write numpy arrays to ICS/IDS format
- 📊 Support for multiple data types (uint8, uint16, int16, float32, float64, complex, etc.)
- 🗜️ Compression support (uncompressed, gzip)
- 🎯 Simple, pythonic API
- 🔧 Automatic data type conversion between ICS and numpy

## What is ICS?

The Image Cytometry Standard (ICS) is an open file format for storing microscopy images. It consists of two files:
- `.ics` - Contains metadata (image dimensions, data type, etc.)
- `.ids` - Contains the actual image data

## Installation

### Quick Install

```bash
pip install .
```

The installation will automatically build the libics shared library.

### Prerequisites

- Python 3.7 or higher
- NumPy
- C compiler (gcc, clang, or MSVC)

### Detailed Installation

See [INSTALL.md](INSTALL.md) for detailed installation instructions including platform-specific notes and troubleshooting.

### Development Installation

For development work:

```bash
# Build the library first
python build_libics.py

# Install in editable mode
pip install -e .
```

### Platform Support

⚠️ **Important:** This package includes a compiled C library.

- **macOS**: ✅ Works out-of-the-box (pre-compiled library included)
- **Linux**: ⚠️ Requires C compiler and build tools during installation
  ```bash
  sudo apt-get install build-essential zlib1g-dev  # Ubuntu/Debian
  pip install .
  ```
- **Windows**: ⚠️ Requires Visual Studio Build Tools or MinGW
  ```cmd
  # Install VS Build Tools first
  pip install .
  ```

See [CROSS_PLATFORM.md](CROSS_PLATFORM.md) for detailed platform compatibility information and how to create platform-specific wheels.

## Quick Start

### Reading ICS Images

```python
from pyics import imread

# Read an ICS image
image, metadata = imread('myimage.ics')

print(f"Image shape: {image.shape}")
print(f"Data type: {image.dtype}")
print(f"Dimensions: {metadata['ndims']}")

# Work with the image as a numpy array
print(f"Min: {image.min()}, Max: {image.max()}, Mean: {image.mean()}")
```

### Writing ICS Images

```python
from pyics import imwrite
import numpy as np

# Create a sample image
image = np.random.randint(0, 255, (512, 512), dtype=np.uint8)

# Write to ICS format
imwrite('output.ics', image)

# Write with compression
imwrite('output_compressed.ics', image, compression='gzip')
```

### Complete Example

```python
import numpy as np
from pyics import imread, imwrite

# Read an image
image, metadata = imread('input.ics')

# Process with numpy
processed = image * 2  # Simple processing example
processed = np.clip(processed, 0, 255).astype(np.uint8)

# Save result
imwrite('processed.ics', processed)
```

## API Reference

### `imread(filename)`

Read an ICS/IDS format image file.

**Parameters:**
- `filename` (str): Path to the ICS file (with or without .ics extension)

**Returns:**
- `image` (np.ndarray): The image data as a numpy array
- `metadata` (dict): Dictionary containing:
  - `dtype`: numpy data type
  - `ndims`: number of dimensions
  - `dimensions`: list of dimension sizes
  - `data_size`: total data size in bytes

**Example:**
```python
image, metadata = imread('myimage.ics')
```

### `imwrite(filename, image, compression='none')`

Write a numpy array to an ICS/IDS format image file.

**Parameters:**
- `filename` (str): Path to the output ICS file
- `image` (np.ndarray): The image data to write
- `compression` (str, optional): Compression method - 'none', 'uncompressed', or 'gzip'. Default is 'none'.

**Example:**
```python
imwrite('output.ics', image, compression='gzip')
```

### `set_library_path(path)`

Set a custom path to the libics shared library.

**Parameters:**
- `path` (str): Path to the libics shared library file

**Example:**
```python
from pyics import set_library_path
set_library_path('/custom/path/to/libics.so')
```

## Supported Data Types

The wrapper supports the following numpy data types:

| NumPy Type | ICS Type | Description |
|------------|----------|-------------|
| `np.uint8` | Ics_uint8 | Unsigned 8-bit integer |
| `np.int8` | Ics_sint8 | Signed 8-bit integer |
| `np.uint16` | Ics_uint16 | Unsigned 16-bit integer |
| `np.int16` | Ics_sint16 | Signed 16-bit integer |
| `np.uint32` | Ics_uint32 | Unsigned 32-bit integer |
| `np.int32` | Ics_sint32 | Signed 32-bit integer |
| `np.uint64` | Ics_uint64 | Unsigned 64-bit integer |
| `np.int64` | Ics_sint64 | Signed 64-bit integer |
| `np.float16` | Ics_real16 | 16-bit floating point |
| `np.float32` | Ics_real32 | 32-bit floating point |
| `np.float64` | Ics_real64 | 64-bit floating point |
| `np.complex64` | Ics_complex32 | Complex (2×32-bit) |
| `np.complex128` | Ics_complex64 | Complex (2×64-bit) |

## Examples

Run the included example script:

```bash
# With a synthetic image
python example.py

# With your own ICS file
python example.py path/to/your/image.ics
```

The example script demonstrates:
- Reading ICS files
- Processing images with numpy
- Writing ICS files with and without compression
- Creating synthetic test images

## Project Structure

```
ics_wrapper/
├── pyics/              # Main Python package
│   ├── __init__.py     # Package module (wrapper implementation)
│   └── libics.*.dylib  # Compiled shared library (after build)
├── libics/              # libics C library (submodule/clone)
├── build/               # Build directory (created during build)
├── example.py          # Example usage script
├── test_wrapper.py     # Test suite
├── build_libics.py     # Build script for compiling libics
├── setup.py            # Setup script for pip installation
├── pyproject.toml      # Package configuration
├── MANIFEST.in         # Package manifest
├── requirements.txt    # Python dependencies
├── INSTALL.md          # Detailed installation guide
├── LICENSE             # License file
└── README.md           # This file
```

## Troubleshooting

### Library Not Found

If you get an error about the library not being found:

```python
from pyics import set_library_path
set_library_path('/path/to/your/libics.so')  # or .dylib on macOS, .dll on Windows
```

### Build Errors

If the build fails:

1. **Check compiler installation:**
   ```bash
   gcc --version  # Linux/macOS
   # or
   clang --version  # macOS
   ```

2. **Try manual build:**
   ```bash
   cd libics
   ./configure --enable-shared
   make
   ```

3. **For CMake build:**
   ```bash
   mkdir build && cd build
   cmake ../libics -DBUILD_SHARED_LIBS=ON
   cmake --build .
   ```

### Import Errors

Make sure numpy is installed:
```bash
pip install numpy
```

## Advanced Usage

### Working with Multi-dimensional Images

```python
from pyics import imread, imwrite

# Read a 3D image (e.g., z-stack)
image_3d, metadata = imread('zstack.ics')
print(f"3D image shape: {image_3d.shape}")  # e.g., (100, 512, 512)

# Process each z-slice
for z in range(image_3d.shape[0]):
    slice_2d = image_3d[z, :, :]
    # Process slice...

# Save the 3D result
imwrite('processed_zstack.ics', image_3d)
```

### Integration with Image Processing Libraries

```python
import numpy as np
from scipy import ndimage
from pyics import imread, imwrite

# Read image
image, _ = imread('input.ics')

# Apply Gaussian filter
filtered = ndimage.gaussian_filter(image, sigma=2)

# Save result
imwrite('filtered.ics', filtered)
```

## Performance Tips

1. **Use appropriate data types**: Choose the smallest data type that fits your data range
2. **Compression**: Use gzip compression for storage, but keep uncompressed for frequent access
3. **Memory efficiency**: For large images, process in chunks when possible

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

### Development Setup

```bash
git clone https://github.com/guiwitz/pyics.git
cd pyics
pip install -e ".[dev]"
```

### Running Tests

```bash
python test_wrapper.py
```

### Publishing

See [PUBLISHING.md](PUBLISHING.md) for instructions on publishing to PyPI.

## License

This wrapper is released under the GNU Library General Public License v2, matching the libics library license.

The libics library is:
- Copyright 2015-2025: Scientific Volume Imaging Holding B.V.
- Copyright 2000-2013: Cris Luengo and others

## Related Links

- [libics GitHub Repository](https://github.com/svi-opensource/libics)
- [ICS File Format Documentation](http://libics.sourceforge.net/)
- [Scientific Volume Imaging](https://www.svi.nl)

## Cross-Platform Support

This package now includes automated wheel building for all major platforms! See:
- [CROSS_PLATFORM.md](CROSS_PLATFORM.md) - Platform compatibility details
- [CI_CD_SETUP.md](CI_CD_SETUP.md) - GitHub Actions setup and usage

After setting up GitHub Actions, users can simply run `pip install pyics` on any platform without needing compilers!

## Citation

If you use this wrapper in your research, please cite the original libics library:

```
Cris Luengo et al., "libics: Image Cytometry Standard file reading and writing"
Available at: https://github.com/svi-opensource/libics
```

## Changelog

### Version 1.0.0 (Initial Release)
- Basic read/write functionality
- Support for all ICS data types
- Gzip compression support
- Comprehensive examples and documentation
