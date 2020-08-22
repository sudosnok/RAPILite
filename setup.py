from setuptools import setup, find_packages
import pathlib

here = pathlib.Path(__file__).parent.resolve()

long_description = (here / 'README.md').read_text(encoding='utf-8')

setup(
    name='RAPILite',
    version='0.1.0',
    description='An asynchronous wrapper for Reddit\'s readonly API',
    long_description=None,
    url='https://github.com/sudosnok/RAPILite',
    license='MIT',
    include_package_data=True,
    author='sudosnok',
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: MIT License",
        "Programming Language :: Python :: 3.6"
    ],
    packages=['RAPILite'],
    python_requires=">=3.6",
    install_requires=['aiohttp==3.6.2'],
)
