import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="vogcast",
    version="0.0.1",
    author="Nadya Moisseeva",
    author_email="nadya.moisseeva@hawaii.edu",
    description="VogCast volcanic air quality modelling framework",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/nmoisseeva/vogcast/",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)
