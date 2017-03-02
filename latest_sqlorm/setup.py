'''
Contains informations necessaries to build, release and install a distribution.
by ssb
'''
# see more at https://pypi.python.org/pypi?%3Aaction=list_classifiers
from setuptools import setup

setup(
    name='python-sqlite-orm',
    version='0.0.1-beta',
    author='surajsinghbisht054@gmail.com',
    url='https://github.com/surajsinghbisht054/sqlorm',
    license='Apache License',
    description='Python SQLite Object-Relational Mapper.',
    py_modules=['sqlorm'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 3',
    ],  
    zip_safe=False
)
