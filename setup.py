#!/usr/bin/env python

"""
distutils setup script for distributing pycornetto
"""

# TODO:
# - somehow get PCK-INFO and MANIFEST in the shared dir as well 

__author__ = 'Erwin Marsi <e.marsi@gmail.com>'
__version__ = '0.6.1'


from distutils.core import setup
from os import walk, path, remove
from os.path import join, exists
from glob import glob
from shutil import rmtree


if exists('MANIFEST'): remove('MANIFEST')
if exists("build"): rmtree("build")


def get_data_files(data_dir_prefix, dir):
    # data_files specifies a sequence of (directory, files) pairs 
    # Each (directory, files) pair in the sequence specifies the installation directory 
    # and the files to install there.
    data_files = []

    for base, subdirs, files in walk(dir):
        install_dir = join(data_dir_prefix, base)
        files = [ join(base, f) for f in files
                  if not f.endswith(".pyc") and not f.endswith("~") ]
        
        data_files.append((install_dir, files))

        if '.svn' in subdirs:
            subdirs.remove('.svn')  # ignore svn directories
                
    return data_files


long_description = """
python interface to Cornetto
"""

classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Science/Research",
    "License :: OSI Approved :: GNU Public License (GPL)",
    "Operating System :: OS Independent",
    "Programming Language :: Python",
    "Topic :: Scientific/Engineering :: Artificial Intelligence",
    "Topic :: Text Processing :: Linguistic",
    "Topic :: Scientific/Engineering :: Information Analysis"
    "Natural Language :: English"
]

name = "pycornetto"

# data files are installed under sys.prefix/share/pycornetto-%(version)
data_dir = join("share", "%s-%s" % (name, __version__))
data_files = [(data_dir, ['CHANGES', 'COPYING', 'INSTALL', 'README', 'USAGE'])]
data_files += get_data_files(data_dir, "doc")

from pprint import pprint
pprint(data_files)

sdist_options = dict( 
    formats=["zip","gztar","bztar"])

setup_options = dict(    
    name =                  name,
    version =               __version__,
    description =           "python interface to Cornetto database",
    long_description =      long_description, 
    author =                "Erwin Marsi",
    author_email =          "e.marsi@gmail.com",
    url =                   "https://github.com/emsrc/pycornetto",
    copyright =             "Tilburg University and Erwin Marsi",
    license =               "GNU Public License",
    formats =               ["zip","gztar","bztar"],
    requires =              ["networkx"],
    provides =              ["%s (%s)" % (name, __version__)],
    platforms =             "POSIX, Mac OS X, MS Windows",
    classifiers =           classifiers,
    
    packages =              ["cornetto"],
    package_dir =           { "" : "lib" },
    scripts =               glob(join("bin", "*.py")),
    data_files =            data_files,
    options =               dict(sdist=sdist_options)
)


setup(**setup_options)

