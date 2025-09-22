"""Setup configuration for eBook Image Extractor."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [
        line.strip() for line in fh if line.strip() and not line.startswith("#")
    ]

setup(
    name="ebook-image-extractor",
    version="2.0.0",
    author="Leonardo Klein",
    author_email="leo@ziondev.us",
    description="Python tool to extract images from EPUB and MOBI files with intelligent filtering",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/leonardokr/ebook-extract-images",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Multimedia :: Graphics",
        "Topic :: Text Processing",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "ebook-extract=main:main",
        ],
    },
    keywords="epub, mobi, azw, images, extraction, ebook, converter, manga, comics",
)
