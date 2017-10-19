# -*- coding: UTF-8 -*-
from setuptools import setup, find_packages  # type: ignore
from os import path

here = path.abspath(path.dirname(__file__))


def slurp(filename):
    with open(filename, encoding='UTF-8') as text_file:
        return text_file.read()


setup(
    name='sensibility',
    version='0.3.dev0',

    description='Syntax error finder and fixer',
    long_description=slurp(path.join(here, 'README.rst')),
    url='https://github.com/naturalness/sensibility',

    author='Eddie Antonio Santos',
    author_email='easantos@ualberta.ca',

    license='Apache',

    classifiers=[
        'Development Status :: 2 - Pre-Alpha',

        'Intended Audience :: Developers',
        'Environment :: Console',

        'License :: OSI Approved :: Apache Software License',

        'Programming Language :: Python :: 3.6',
    ],

    packages=find_packages(),

    # Node.JS app is NOT zip safe!
    zip_safe=False,
    include_package_data=True,

    install_requires=[
        'blessings',
        'github3.py==0.9.6',
        'h5py>=2.6.0',
        'javac-parser>=0.2.0, <0.3.0',
        'jenkspy>= 0.1.3, <0.2.0',
        # Due to difficulty loading the models across versions, it's easier to
        # install this SPECIFIC version of Keras.
        'Keras==2.0.8',
        'more-itertools>=2.3',
        'numpy>=1.11.0',
        'python-dateutil>=2.6.0',
        'edit-distance>=1.0.1',
        'pyzmq>=16.0.2, <17.0.0',
        'redis>=2.10.5',
        'requests==2.13.0',
        'SQLAlchemy>=1.1.9',
        'Theano>=0.8.0, < 0.9.0',
        'tqdm',
    ],
    extras_require={
        'test': [
            'pytest',
            'mypy',
            'pycodestyle'
        ]
    },
)
