#!/usr/bin/env python3

import sys, re
import numpy

if sys.version_info[0] < 3:
    sys.exit('Sorry, Python < 3.x is not supported')

# Try using setuptools first, if it's installed
from setuptools import setup, find_packages

# Extract the version number from pyfx/__init__.py
version = None
with open("pyfx/__init__.py","r") as f:
    for l in f:
        if l.startswith("__version__"):
            version = l.split("=")[1].strip()
            version = re.sub("\"","",version)


# Need to add all dependencies to setup as we go!
setup(name='pyfx',
      packages=find_packages(),
      version=version,
      description="Python software package for generating video effects",
      long_description=open("README.md").read(),
      author='Michael J. Harms',
      author_email='harmsm@gmail.com',
      url='https://github.com/harmsm/pyfx',
      download_url='https://github.com/harmsm/pyfx/tarball/0.1',
      zip_safe=False,
      install_requires=["scipy","numpy","scikit-image","dlib","pillow","ffmpeg-python"],
      package_data={"":["pyfx/data/*"]},
      include_package_data=True,
      classifiers=['Programming Language :: Python'])
