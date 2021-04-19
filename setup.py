#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""

    The setup script.i

"""

import os
from os.path import join

from setuptools import (
    setup,
    find_packages
)

with open('README.md') as readme_file:
    readme = readme_file.read()

with open('CHANGELOG.md') as changelog_file:
    changelog = changelog_file.read()

install_requirements = [
    'blessed',
    'py-cpuinfo',
    'rpyc',
    'psutil',
    'pyyaml',
]

setup_requirements = [
]

test_requirements = [
]

# Possibly required by developers of colife-agent
dev_requirements = [
]

docs_requirements = [
]

setup(
    author="billbsing",
    author_email='billbsing@gmail.com',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.6',
    ],
    description="cluster",
    extras_require={
        'test': test_requirements,
        'docs': docs_requirements,
        'dev': dev_requirements + test_requirements + docs_requirements,
    },
    install_requires=install_requirements,
    license="Apache Software License 2.0",
    long_description=readme,
    long_description_content_type='text/markdown',
    keywords='cluster',
    name='cluster-py',
    packages=find_packages(),
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    python_requires='>=3.6',
    url='https://github.com/billbsing/cluster-py',
    version='0.0.1',
)

