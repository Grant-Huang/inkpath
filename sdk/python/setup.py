"""InkPath Python SDK安装配置"""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="inkpath-sdk",
    version="0.1.0",
    author="InkPath Team",
    author_email="support@inkpath.com",
    description="InkPath官方Python SDK，简化Bot开发",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/inkpath/inkpath-sdk-python",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.31.0",
        "flask>=3.0.0",
    ],
    license="MIT",
)
