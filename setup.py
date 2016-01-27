import subprocess
from pathlib import Path
from setuptools import setup, find_packages

rst_rtfm = None

try:
    cmd = "pandoc -f markdown_github -r rst -o README.rst README.md"
    args = cmd.split(' ')
    proc = subprocess.run(args, check=False, universal_newlines=True)

    if proc.returncode != 0:
        print("Couldn't execute pandoc. No RST 4u.")
    else:
        rst_rtfm = proc.stdout


except subprocess.CalledProcessError:
    print("Failed to run pandoc to get an RST README.")

setup(
    name='asyncio_throttler',
    version='0.1.0',
    description="Throttling tools for py3.5+ asyncio.",
    long_description=rst_rtfm or Path('./README.md').read_text(),
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
