'''
This modules contains a distutils extension mechanism for Pythran
    * PythranExtension: is used as distutils's Extension
'''

import pythran.config as cfg
import pythran.toolchain as tc

from numpy.distutils.extension import Extension

import os.path
import os


class PythranExtension(Extension):
    '''
    Description of a Pythran extension

    Similar to distutils.core.Extension except that the sources are .py files
    They must be processable by pythran, of course.

    The compilation process ends up in a native Python module.
    '''
    def __init__(self, name, sources, *args, **kwargs):
        kwargs.update(cfg.make_extension(False))
        self._sources = sources
        Extension.__init__(self, name, sources, *args, **kwargs)
        self.__dict__.pop("sources", None)

    @property
    def sources(self):
        cxx_sources = []
        for source in self._sources:
            base, ext = os.path.splitext(source)
            if ext != '.py':
                cxx_sources.append(source)
                continue
            output_file = base + '.cpp'  # target name

            if not os.path.exists(output_file) or os.stat(output_file) < os.stat(source):
                # get the last name in the path
                if '.' in self.name:
                    module_name = os.path.splitext(self.name)[-1][1:]
                else:
                    module_name = self.name
                tc.compile_pythranfile(source, output_file,
                                       module_name, cpponly=True)
            cxx_sources.append(output_file)
        return cxx_sources

    @sources.setter
    def sources(self, sources):
        self._sources = sources
