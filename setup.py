"""Flexible tools for throttling and managing async tasks such as
web requests from asyncio.

"""
from setuptools import setup, find_packages

setup(
    name='asyncio_throttler',
    version='0.1.0',
    description=__doc__,
    author="Anthony Grimes",
    author_email="i@raynes.me",
    url='https://github.com/Raynes/asyncio_throttler',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.5'
        ]
    )
