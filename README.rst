Django-Onfido
==============

.. image:: https://travis-ci.org/yunojuno/django-onfido.svg?branch=master
    :target: https://travis-ci.org/yunojuno/django-onfido

Django app for integration with the Onfido API (v2)

Background
----------

Onfido is an online identity verification service. It provides API access to a range of tests (identity, right to work, criminal history, credit report). It is assumed that you are only interested in this project because you are already aware of what Onfido does, and so I won't repeat it here. If you want to find out more, head over to their website.

If you *are* using Onfido, and you are using Django, then this project can be used to manage Onfido checks against your existing Django users. It handles the API interactions, as well as providing the callback webhooks required to support live status updates.

Installation
------------

The project is available through PyPI as ``django-onfido``:

.. code::

    $ pip install django-onfido

And the main package itself is just ``onfido``:

.. code:: python

    >>> from onfido import api, models, views, urls, admin, signals

Usage
-----

The main use case is as follows:

1. Create an Onfido **Applicant** from your Django user:

.. code:: python

    >>> from django.contrib.auth.models import User
    >>> from onfido.api import create_applicant
    >>> user = User.objects.last()  # any old one will do
    >>> applicant = create_applicant(user)
    DEBUG Making POST request to https://api.onfido.com/v2/applicants
    DEBUG <Response [201]>
    DEBUG {u'first_name': u'hugo', u'last_name': u'rb', u'middle_name': None, ...}
    DEBUG Creating new Onfido applicant from JSON: {u'first_name': u'hugo', u'last_name': u'rb', ...}
    <Applicant id=a2c98eae-XXX user='hugo'>

2. Create your check + reports for the applicant:

.. code:: python

    >>> from onfido.api import create_check
    >>> create_check(applicant, check_type='standard', reports=['identity', 'right_to_work'])
    >>> assert Check.objects.count() == 1
    >>> assert Report.objects.count() == 2

This will create the **Check** and **Report** objects on Onfido, and store them locally as Django model objects.

3. Wait for callback events to update the status of reports and checks:

.. code:: shell

    DEBUG Received Onfido callback: {"payload":{...}}
    DEBUG Processing 'check.completed' action on check.bd8232c4-...

Tests
-----

The project has pretty good test coverage (>90%) and the tests themselves run through ``tox``.

.. code::

    $ pip install tox
    $ tox

If you want to run the tests manually, make sure you install the requirements, and Django.

.. code::

    $ pip install -r requirements.txt
    $ pip install django==1.8  # your version goes here
    $ python manage.py test onfido.tests

If you are hacking on the project, please keep coverage up.

Contributing
------------

Standard GH rules apply: clone the repo to your own account, create a branch, make sure you update the tests, and submit a pull request.

Status
------

This project is very early in its development. We are using it at YunoJuno, but 'caveat emptor'. It currently only supports 'standard' checks, and has very patchy support for the full API. It does what we need it to do right now, and we will extend it as we evolve. If you need or want additional features, get involved :-).
