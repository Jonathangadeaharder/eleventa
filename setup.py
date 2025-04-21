from setuptools import setup, find_packages

setup(
    name="eleventa",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "PySide6",
        "SQLAlchemy",
    ],
    extras_require={
        "test": [
            "pytest>=7.0.0",
            "pytest-qt>=4.0.0",
            "pytest-mock>=3.0.0",
            "pytest-timeout>=2.0.0",
            "pytest-cov",
        ],
    },
) 