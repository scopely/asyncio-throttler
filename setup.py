import subprocess
from pathlib import Path
from setuptools import setup, find_packages

try:
    cmd = "pandoc -f markdown_github-hard_line_breaks -t rst -o README.rst README.md"  # noqa
    args = cmd.split(' ')
    proc = subprocess.run(args, check=False, universal_newlines=True)

    if proc.returncode != 0:
        print("Couldn't execute pandoc. No RST 4u.")

except subprocess.CalledProcessError:
    print("Failed to run pandoc to get an RST README.")
except Exception as e:
    raise e

rst = Path('./README.rst')
md = Path('./README.md')
README = rst.read_text() if rst.exists() else md.read_text()

setup(
    name='asyncio_throttler',
    version='0.1.0',
    description="Throttling tools for py3.5+ asyncio.",
    long_description=README,
    author="Anthony Grimes",
    author_email="anthony@scopely.com",
    url='https://github.com/scopely/asyncio_throttler',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[],
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.5'
        ]
    )
