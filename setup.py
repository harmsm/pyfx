#!/usr/bin/env python3

import sys
import numpy

if sys.version_info[0] < 3:
    sys.exit('Sorry, Python < 3.x is not supported')

# Try using setuptools first, if it's installed
from setuptools import setup, find_packages

# Need to add all dependencies to setup as we go!
setup(name='photonzombie',
      packages=find_packages(),
      version='0.1',
      description="Python software package for algorithmically generating movie effects",
      long_description=open("README.md").read(),
      author='Michael J. Harms',
      author_email='harmsm@gmail.com',
      url='https://github.com/harmsm/photonzombie',
      download_url='https://github.com/harmsm/photonzombie/tarball/0.1',
      zip_safe=False,
      install_requires=["scipy","numpy","scikit-image","dlib","pillow"],
      package_data={"":["data/*"]},
      classifiers=['Programming Language :: Python'])
