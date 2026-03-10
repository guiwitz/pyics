#!/usr/bin/env python3
"""
Setup script for pyics package.

This setup script handles:
1. Building the libics shared library
2. Installing the Python wrapper package
3. Including the compiled library in the package
"""

import os
import sys
import subprocess
import platform
from pathlib import Path
from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext
from setuptools.command.build_py import build_py
from setuptools.command.install import install


class BuildLibICS(build_ext):
    """Custom build command to compile libics library."""
    
    def run(self):
        """Build the libics shared library."""
        libics_dir = Path(__file__).parent / "libics"
        
        if not libics_dir.exists():
            raise RuntimeError(
                f"libics directory not found at {libics_dir}. "
                "Please ensure the libics submodule is initialized."
            )
        
        print("=" * 60)
        print("Building libics shared library...")
        print("=" * 60)
        
        # Try autotools build
        try:
            self.build_with_autotools(libics_dir)
        except Exception as e:
            print(f"Autotools build failed: {e}")
            print("Attempting CMake build...")
            try:
                self.build_with_cmake(libics_dir)
            except Exception as e2:
                raise RuntimeError(
                    f"Failed to build libics with both autotools and CMake.\n"
                    f"Autotools error: {e}\n"
                    f"CMake error: {e2}"
                )
        
        # Copy the built library to the package
        self.copy_library()
        
        # Now run the parent's build_ext to process extensions
        # This will call build_extension() for our dummy extension
        super().run()
    
    def build_extension(self, ext):
        """Override to skip building the dummy extension but create a marker."""
        if ext.name == "pyics._dummy":
            # Create an empty marker file to make setuptools happy
            # This ensures the wheel is marked as platform-specific
            build_lib = Path(self.build_lib)
            package_dir = build_lib / "pyics"
            package_dir.mkdir(parents=True, exist_ok=True)
            
            # Create empty __dummy.py to mark as extension package
            dummy_marker = package_dir / "_dummy.py"
            dummy_marker.write_text("# Dummy module to mark platform wheel\n")
            print(f"Created marker: {dummy_marker}")
            
            # Also copy the library to build_lib so it's included in the wheel
            self.copy_library_to_build()
        else:
            super().build_extension(ext)
    
    def build_with_autotools(self, libics_dir):
        """Build using autotools (configure/make)."""
        configure_path = libics_dir / "configure"
        
        # Run bootstrap if needed
        if not configure_path.exists():
            bootstrap_path = libics_dir / "bootstrap.sh"
            if bootstrap_path.exists():
                subprocess.check_call(["sh", "bootstrap.sh"], cwd=libics_dir)
            else:
                raise RuntimeError("Neither configure nor bootstrap.sh found")
        
        # Configure
        subprocess.check_call(["./configure", "--enable-shared"], cwd=libics_dir)
        
        # Make
        subprocess.check_call(["make"], cwd=libics_dir)
    
    def build_with_cmake(self, libics_dir):
        """Build using CMake."""
        build_dir = Path(__file__).parent / "build"
        build_dir.mkdir(exist_ok=True)
        
        cmake_args = [
            "cmake",
            str(libics_dir),
            "-DBUILD_SHARED_LIBS=ON",
        ]
        
        if platform.system() == "Darwin":
            cmake_args.extend([
                "-DCMAKE_MACOSX_RPATH=ON",
                "-DCMAKE_INSTALL_RPATH=@loader_path",
            ])
        
        subprocess.check_call(cmake_args, cwd=build_dir)
        subprocess.check_call(["cmake", "--build", "."], cwd=build_dir)
    
    def copy_library(self):
        """Copy the built library to the package directory."""
        package_dir = Path(__file__).parent / "src" / "pyics"
        package_dir.mkdir(exist_ok=True, parents=True)
        
        # Find the library
        search_dirs = [
            Path(__file__).parent / "libics" / ".libs",
            Path(__file__).parent / "libics",  # Sometimes library is in root
            Path(__file__).parent / "build",
        ]
        
        system = platform.system()
        if system == "Windows":
            lib_patterns = ["*.dll"]
        elif system == "Darwin":
            lib_patterns = ["*.dylib", "*.*.dylib"]
        else:
            lib_patterns = ["*.so", "*.so.*"]
        
        found = False
        for search_dir in search_dirs:
            if not search_dir.exists():
                continue
            for pattern in lib_patterns:
                libs = list(search_dir.glob(pattern))
                for lib_file in libs:
                    # Skip symlinks, get actual files
                    if lib_file.is_symlink():
                        continue
                    target = package_dir / lib_file.name
                    print(f"Copying {lib_file} to {target}")
                    
                    import shutil
                    shutil.copy2(lib_file, target)
                    print(f"✓ Library copied to package: {target}")
                    found = True
        
        if not found:
            raise RuntimeError(
                f"Could not find built library in {search_dirs}. "
                "Build may have failed."
            )
    
    def copy_library_to_build(self):
        """Copy the built library to the build directory for wheel packaging."""
        import shutil
        
        # Get the build_lib directory where built packages go
        build_lib = Path(self.build_lib)
        package_dir = build_lib / "pyics"
        package_dir.mkdir(parents=True, exist_ok=True)
        
        # Find the library in the same locations
        search_dirs = [
            Path(__file__).parent / "libics" / ".libs",
            Path(__file__).parent / "libics",
            Path(__file__).parent / "build",
            Path(__file__).parent / "src" / "pyics",  # May have been copied here already
        ]
        
        system = platform.system()
        if system == "Windows":
            lib_patterns = ["*.dll"]
        elif system == "Darwin":
            lib_patterns = ["*.dylib", "*.*.dylib"]
        else:
            lib_patterns = ["*.so", "*.so.*"]
        
        found = False
        for search_dir in search_dirs:
            if not search_dir.exists():
                continue
            for pattern in lib_patterns:
                libs = list(search_dir.glob(pattern))
                for lib_file in libs:
                    if lib_file.is_symlink():
                        continue
                    target = package_dir / lib_file.name
                    print(f"Copying {lib_file} to build: {target}")
                    shutil.copy2(lib_file, target)
                    print(f"✓ Library copied to build directory: {target}")
                    found = True
        
        if not found:
            raise RuntimeError(
                f"Could not find library to copy to build directory. "
                f"Searched: {search_dirs}"
            )


class CustomBuildPy(build_py):
    """Custom build_py to ensure library is built before collecting files."""
    
    def run(self):
        # Run build_ext first to build and copy the library
        self.run_command('build_ext')
        # Then run normal build_py to collect Python files
        super().run()
        
        # Debug: List what was copied
        print("=" * 60)
        print("Files in build directory:")
        build_lib = Path(self.build_lib) / "pyics"
        if build_lib.exists():
            for f in build_lib.iterdir():
                print(f"  {f.name} ({f.stat().st_size} bytes)")
        else:
            print(f"  WARNING: {build_lib} does not exist!")
        print("=" * 60)


if __name__ == "__main__":
    from setuptools.dist import Distribution
    
    # Custom distribution to force platform-specific wheels
    class BinaryDistribution(Distribution):
        def has_ext_modules(self):
            return True
    
    # Define a dummy extension to force build_ext to run
    # This ensures the libics library gets built even though we don't
    # have actual Python C extensions
    dummy_ext = Extension(
        name="pyics._dummy",
        sources=[],
        optional=False  # Changed from True to ensure it's not skipped
    )
    
    setup(
        distclass=BinaryDistribution,
        cmdclass={
            'build_py': CustomBuildPy,
            'build_ext': BuildLibICS,
        },
        ext_modules=[dummy_ext],
    )
