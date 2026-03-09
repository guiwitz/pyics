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
        
        # Continue with extension building (though we don't have any)
        super().run()
    
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
        package_dir = Path(__file__).parent / \"pyics\"
        package_dir.mkdir(exist_ok=True)
        
        # Find the library
        search_dirs = [
            Path(__file__).parent / "libics" / ".libs",
            Path(__file__).parent / "build",
        ]
        
        system = platform.system()
        if system == "Windows":
            lib_patterns = ["*.dll"]
        elif system == "Darwin":
            lib_patterns = ["*.dylib"]
        else:
            lib_patterns = ["*.so", "*.so.*"]
        
        for search_dir in search_dirs:
            if not search_dir.exists():
                continue
            for pattern in lib_patterns:
                libs = list(search_dir.glob(pattern))
                if libs:
                    lib_file = libs[0]
                    target = package_dir / lib_file.name
                    print(f"Copying {lib_file} to {target}")
                    
                    import shutil
                    shutil.copy2(lib_file, target)
                    print(f"✓ Library copied to package: {target}")
                    return
        
        raise RuntimeError("Could not find built library to copy to package")


if __name__ == "__main__":
    setup(
        cmdclass={
            'build_ext': BuildLibICS,
        },
    )
