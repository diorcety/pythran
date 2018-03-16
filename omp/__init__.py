"""OpenMP wrapper using a libgomp dynamically loaded library."""

from ctypes.util import find_library
from subprocess import check_output
import ctypes
import os
import sys

try:
    # there may be an environ modification when loading config
    from pythran.config import compiler, compiler_executable
    c_compiler = compiler()
    cxx = compiler_executable(c_compiler.cxx_compiler())
except ImportError:
    c_compiler = None
    cxx = os.environ.get('CXX', 'c++')


class OpenMP(object):

    """
    Internal representation of the OpenMP module.

    Custom class is used to dynamically add omp runtime function
    to this library when function is called.
    """

    def __init__(self):
        if c_compiler is None or c_compiler.compiler_type != 'msvc':
            self.init_not_msvc()
        else:
            self.init_msvc()

    def init_msvc(self):
        vcomp_path = None
        for i in range(15, 8, -1):
            vcomp_name = 'vcomp%d0.dll' % i
            vcomp_path = find_library(vcomp_name)
            if vcomp_path:
                break
        if not vcomp_path:
            raise ImportError("I can't find a shared library for vcomp.")
        else:
            # Load the library (shouldn't fail with an absolute path right?)
            self.libomp = ctypes.CDLL(vcomp_path)
            self.version = 20

    def init_not_msvc(self):
        """ Find OpenMP library and try to load if using ctype interface. """
        # find_library() does not search automatically LD_LIBRARY_PATH
        paths = os.environ.get('LD_LIBRARY_PATH', '').split(':')
        for gomp in ('libgomp.so', 'libgomp.dylib'):
            cmd = [cxx, '-print-file-name=' + gomp]
            # the subprocess can fail in various ways
            # in that case just give up that path
            try:
                path = os.path.dirname(check_output(cmd).strip())
                if path:
                    paths.append(path)
            except OSError:
                pass

        # Try to load find libgomp shared library using loader search dirs
        libgomp_path = find_library("gomp")

        # Try to use custom paths if lookup failed
        for path in paths:
            if libgomp_path:
                break
            path = path.strip()
            if os.path.isdir(path):
                libgomp_path = find_library(os.path.join(str(path), "libgomp"))

        if not libgomp_path:
            raise ImportError("I can't find a shared library for libgomp,"
                              " you may need to install it or adjust the "
                              "LD_LIBRARY_PATH environment variable.")
        else:
            # Load the library (shouldn't fail with an absolute path right?)
            self.libomp = ctypes.CDLL(libgomp_path)
            self.version = 45

    def __getattr__(self, name):
        """
        Get correct function name from libgomp ready to be use.

        __getattr__ is call only `name != libomp` as libomp is a real
        attribute.
        """
        if name == 'VERSION':
            return self.version
        return getattr(self.libomp, 'omp_' + name)

# see http://mail.python.org/pipermail/python-ideas/2012-May/014969.html
sys.modules[__name__] = OpenMP()
