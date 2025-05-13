from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="featherflow",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="Ultra-lightweight workflow orchestration tool",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/featherflow",
    packages=find_packages(),
    package_data={
        "featherflow": ["templates/*"],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    entry_points={
        "console_scripts": [
            "featherflow=featherflow.cli:main",
        ],
    },
)