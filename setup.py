# -*- coding: utf-8 -*-
from os import path, chdir, pardir
from setuptools import setup, find_packages

README = open(path.join(path.dirname(__file__), 'README.rst')).read()

# allow setup.py to be run from any path
chdir(path.normpath(path.join(path.abspath(__file__), pardir)))

setup(
    name="django-onfido",
    version="0.4.0",
    packages=find_packages(),
    install_requires=[
        'django>=1.8',
        'requests>=2',
        'python-dateutil'
    ],
    include_package_data=True,
    description='Django app for integration with Onfido.',
    long_description=README,
    url='https://github.com/hugorodgerbrown/django-onfido',
    author='Hugo Rodger-Brown',
    author_email='code@yunojuno.com',
    maintainer='Hugo Rodger-Brown',
    maintainer_email='hugo@yunojuno.com',
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
)
