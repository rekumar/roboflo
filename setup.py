from setuptools import setup
from setuptools import find_packages
import os
import re

this_dir = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(this_dir, "README.md"), encoding="utf-8") as f:
    long_description = f.read()


# with open('megnet/__init__.py', encoding='utf-8') as fd:
#     try:
#         lines = ''
#         for item in fd.readlines():
#             item = item
#             lines += item + '\n'
#     except Exception as exc:
#         raise Exception('Caught exception {}'.format(exc))


# version = re.search('__version__ = "(.*)"', lines).group(1)


setup(
    name="roboflo",
    version="0.1.2",
    description="Scheduler for automation tasks that involve multiple stations/workers.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Rishi Kumar",
    author_email="rek010@eng.ucsd.edu",
    # download_url="https://github.com/rekumar/roboflo",
    license="MIT",
    install_requires=[
        "numpy",
        "ortools",
        "matplotlib",
    ],
    # extras_require={
    #     'model_saving': ['h5py'],
    #     'molecules': ['openbabel', 'rdkit'],
    #     'tensorflow': ['tensorflow>=2.1'],
    #     'tensorflow with gpu': ['tensorflow-gpu>=2.1'],
    # },
    packages=find_packages(),
    package_data={
        # "hardware": ["*.yaml", "*/*.yaml", "*/*/*.yaml", "*/*/*.json"],
        "Examples": ["*.ipynb"],
    },
    include_package_data=True,
    keywords=["research", "science", "machine", "automation"],
    classifiers=[
        "Programming Language :: Python :: 3.8",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: Scientific/Engineering :: Physics",
        "Topic :: Scientific/Engineering :: Chemistry",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    # entry_points={
    #     'console_scripts': [
    #         'meg = megnet.cli.meg:main',
    #     ]
    # }
)
