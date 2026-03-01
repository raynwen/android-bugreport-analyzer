from setuptools import setup, find_packages

setup(
    name="android_bugreport_analyzer",
    version="1.2.0",
    description="Android Bug Report Analysis System",
    packages=[
        "bugreport_extractor",
        "bugreport_parser", 
        "bugreport_analyzer",
        "bugreport_coordinator",
    ],
    package_dir={
        "bugreport_extractor": "bugreport-extractor",
        "bugreport_parser": "bugreport-parser",
        "bugreport_analyzer": "bugreport-analyzer",
        "bugreport_coordinator": "bugreport-coordinator",
    },
    install_requires=[
        "dataclasses-json>=0.5.0",
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "bugreport-analyzer=main:main",
        ],
    },
)
