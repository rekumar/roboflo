from setuptools import setup
from setuptools import find_packages
import os

this_dir = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(this_dir, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

requirements = [
    "numpy ~= 1.24.0",
    "ortools ~= 9.5.2237",
    "matplotlib ~= 3.6.2",
]

dev_requirements = ["pytest >= 6.2.5"]

setup(
    name="roboflo",
    version="0.2",
    description="Scheduler for automation tasks that involve multiple stations/workers.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Rishi Kumar",
    author_email="rek010@eng.ucsd.edu",
    download_url="https://github.com/rekumar/roboflo",
    license="MIT",
    install_requires=requirements,
    extras_require={"dev": dev_requirements},
    packages=find_packages(),
    package_data={
        "": ["Examples/*.ipynb"],
    },
    include_package_data=True,
    keywords=["research", "science", "machine", "automation"],
    classifiers=[
        "Programming Language :: Python :: 3.8",
        "Development Status :: 4 - Beta",
        "Topic :: Office/Business :: Scheduling",
        "Intended Audience :: Manufacturing",
        "Intended Audience :: Science/Research",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: Scientific/Engineering :: Physics",
        "Topic :: Scientific/Engineering :: Chemistry",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
