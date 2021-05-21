import pathlib
from setuptools import find_packages, setup

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

# This call to setup() does all the work
setup(
    name="dell_warranty_api",
    version="1.4.0",
    description="Receive info about dell devices in humanize view",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/karma-git/dell_warranty_status_api",
    author="karma_",
    author_email="andrewhorbach@gmail.com",
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
    ],
    packages=find_packages(exclude=("tests",)),
    include_package_data=True,
    # requests, pycountry, prettytable, humanize, loguru, pretty_errors
    install_requires=["requests",
                      "pycountry",
                      "prettytable", 
                      "humanize",
                      "loguru",
                      "pretty_errors",
                      ],
    entry_points={
        "console_scripts": [
            "dell_api=dell_api.__main__:main",
        ]
    },
    
)