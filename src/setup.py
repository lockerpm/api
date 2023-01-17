import pathlib
import setuptools

# The directory containing this file
HERE = pathlib.Path(__file__).parent.parent
print(HERE)

# The text of the README file
README = (HERE / "README.md").read_text()
print(README)

# This call to setup() does all the work
setuptools.setup(
    name="locker-api",
    version="0.0.1",
    description="Locker API",
    long_description=README,
    long_description_content_type="text/markdown",
    author="CyStack",
    author_email="contact@cystack.net",
    # license="GPLv3",
    classifiers=[
        # "License :: OSI Approved :: MIT License",
        "Programming Language :: Python"
    ],
    packages=setuptools.find_packages(),
    python_requires=">=3"
)
