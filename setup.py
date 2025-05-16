from setuptools import setup, find_packages

setup(
    name="featherflow",
    version="0.1.0",
    description="Ultra-lightweight workflow orchestration tool built with Python's standard library",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Anthony Baum",
    author_email="wxbaum@gmail.com",
    url="https://github.com/wxbaum/featherflow",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    package_data={
        "featherflow": ["templates/*.sh"],
    },
    entry_points={
        "console_scripts": [
            "featherflow=featherflow.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.7",
    license="GNU GPL v3",
)
