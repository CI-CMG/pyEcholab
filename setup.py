import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name = "pyEcholab",
    version = "0.0.2",
    author = "",
    author_email = "",
    description= "pyEcholab is a python package for reading, writing, processing, and plotting data from Simrad/Kongsberg sonar systems.",
    long_description = long_description,
    long_description_content_type = "text/markdown",
    url = "https://github.com/CI-CMG/pyEcholab",
    packages = setuptools.find_packages(),
    classifiers=["Programming Language :: Python :: 3",
                 "License :: OSI Approved :: MIT License",
                 "Operating System :: OS Independent",
    ],
)
