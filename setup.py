#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = ['future', 'pandas', 'marshmallow' ]

setup_requirements = [ ]

test_requirements = [ 'nose ']

setup(
    author="bsnacks000",
    author_email='bsnacks000@gmail.com',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    description="Interfaces for an in-memory datastore and calc framework using marshmallow + pandas",
    install_requires=requirements,
    license="MIT license",
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='binx',
    name='binx',
    packages=find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
    setup_requires=setup_requirements,
    test_suite='nose.collector',
    tests_require=test_requirements,
    url='https://github.com/bsnacks000/binx',
    version='0.2.3',
    zip_safe=False,
)
