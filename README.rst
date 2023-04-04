======================================
The Mia! Accounting Django Application
======================================


Description
===========

*mia-accounting* is a Django_ accounting application.  It was
rewritten from my own private accounting application in Perl/mod_perl_
in 2007.  The revision aims to be mobile-friendly with Bootstrap, with
a modern back-end framework and front-end technology like jQuery.  The
first revision was in Perl/Mojolicious_ in 2019.  This is the second
revision in Python/Django in 2020.

The Mia! Accounting Django application comes with two parts:

- The ``accounting`` application contains the main accounting
  application.

- The ``mia_core`` application contains core shared libraries that are
  used by the ``accounting`` application and my other applications.

You may try it in live demonstration at:

- URL: https://accounting-django.imacat.idv.tw/accounting
- Username: ``admin``
- Password: ``12345``

.. _Django: https://www.djangoproject.com
.. _mod_perl: https://perl.apache.org
.. _Mojolicious: https://mojolicious.org


Installation
============

Install
-------

The Mia! Accounting Django application requires Python 3.7 and Django
3.1.

Install ``mia-accounting-django`` with ``pip``.

.. code::

    pip install mia-accounting-django

``settings.py``
---------------

Add these two applications in the ``INSTALL_APPS`` section of your
``settings.py``.

.. code::

    INSTALLED_APPS = [
      'mia_core.apps.MiaCoreConfig',
      'accounting.apps.AccountingConfig',
      ...
    ]

Make sure the locale middleware is in the ``MIDDLEWARE`` section of
your ``settings.py``, and add it if it is not added yet.

.. code::

    MIDDLEWARE = [
      ...
      'django.middleware.locale.LocaleMiddleware',
      ...
    ]

``urls.py``
-----------

Add the ``accounting`` application in the ``urlpatterns`` in your
``urls.py``.

.. code::

    urlpatterns = [
      ...
      path('accounting/', decorator_include(login_required, 'accounting.urls')),
      ...
    ]

Make sure ``i18n`` and ``jsi18n`` are also in the ``urlpatterns`` of
your ``urls.py``, and add them if they are not added yet.

.. code::

    urlpatterns = [
      ...
      path('i18n/', include("django.conf.urls.i18n")),
      path('jsi18n/', JavaScriptCatalog.as_view(), name='javascript-catalog'),
      ...
    ]

``base.html``
-------------

Add the following to the very beginning of your base template
``base.html``, before your first real HTML tag.

.. code::

    {% load mia_core %}
    {% init_libs %}
    {% block settings %}{% endblock %}

Add the CSS and JavaScripts in the ``<head>...</head>`` section of your
base template ``base.html``.

.. code::

    {% for css in libs.css %}
      <link rel="stylesheet" type="text/css" href="{% if css|is_static_url %}{% static css %}{% else %}{{ css }}{% endif %}" />
    {% endfor %}
    {% for js in libs.js %}
      <script src="{% if js|is_static_url %}{% static js %}{% else %}{{ js }}{% endif %}"></script>
    {% endfor %}

Database Initialization
-----------------------

Run the management commands to initialize the database.

.. code::

    ./manage.py migrate accounting
    ./manage.py accounting_accounts

Optionally you can populate the database with some sample data.

.. code::

    ./manage.py accounting_sample

Restart Your Web Server
-----------------------

And you are done.


Management Commands
===================

The following management commands are added by *the Mia! Accounting Django
application* to ``manage.py``:

``accounting_accounts``
-----------------------

.. code::

    % ./manage.py accounting_accounts [--user USER]

Fills the database with the accounting accounts.

- ``--user`` *USER*

  An optional user to specify which user these initial accounts
  belongs to.  When omitted, the first user found in the system will
  be used.

``accounting_sample``
---------------------

.. code::

    % ./manage.py accounting_sample [--user USER]

Fills the database with sample accounting data.

- ``--user`` *USER*

  An optional user to specify which user these initial accounts
  belongs to.  When omitted, the first user found in the system will
  be used.

``make_trans``
--------------

.. code::

    % ./manage.py make_trans --domain DOMAIN APP_DIR1 [APP_DIR2 ...]

Updates the revision date, converts the Traditional Chinese
translation into Simplified Chinese, and then calls the
``compilemessages`` command.

- ``--domain`` *DOMAIN*

  The message domain, either ``django`` or ``djangojs``.

- *APP_DIR1* [*APP_DIR2* ...]

  One or more application directories that contains their ``locale``
  subdirectories.


Advanced Settings
=================

The following advanced settings are available in ``settings.py``.

.. code::

    # Settings for the accounting application
    ACCOUNTING = {
        # The default cash account, for ex., "0" (current assets and liabilities),
        # "1111" (cash on hand), "1113" (cash in banks) or any
        "DEFAULT_CASH_ACCOUNT": "1111",
        # The shortcut cash accounts
        "CASH_SHORTCUT_ACCOUNTS": ["0", "1111"],
        # The default ledger account
        "DEFAULT_LEDGER_ACCOUNT": "1111",
        # The payable accounts to track
        "PAYABLE_ACCOUNTS": ["2141"],
        # The asset accounts to track
        "EQUIPMENT_ACCOUNTS": ["1441"],
    }

    # The local static CSS and JavaScript libraries
    # The default is to use the libraries from CDN.  You may set them to use the
    # local static copies of these libraries
    STATIC_LIBS = {
        "jquery": {"css": [], "js": ["jquery/jquery-3.5.1.min.js"]},
        "bootstrap4": {"css": ["bootstrap4/css/bootstrap.min.css"],
                       "js": ["bootstrap4/js/bootstrap.bundle.min.js"]},
        "font-awesome-5": {"css": ["font-awesome-5/css/all.min.css"],
                           "js": []},
        "bootstrap4-datatables": {
            "css": ["datatables/css/jquery.dataTables.min.css",
                    "datatables/css/dataTables.bootstrap4.min.css"],
            "js": ["datatables/js/jquery.dataTables.min.js",
                   "datatables/js/dataTables.bootstrap4.min.js"]},
        "jquery-ui": {"css": ["jquery-ui/jquery-ui.min.css"],
                      "js": ["jquery-ui/jquery-ui.min.js"]},
        "bootstrap4-tempusdominus": {
            "css": [("tempusdominus-bootstrap-4/css/"
                     "tempusdominus-bootstrap-4.min.css")],
            "js": ["moment/moment-with-locales.min.js",
                   ("tempusdominus-bootstrap-4/js/"
                    "tempusdominus-bootstrap-4.min.js")]},
        "decimal.js": {"css": [], "js": ["decimal/decimal.min.js"]},
    }

    # The default static stylesheets to include.  Default is none.
    DEFAULT_CSS = ["css/app.css"]
    # The default static JavaScript to include.  Default is none.
    DEFAULT_JS = ["js/app.js"]

    # The regular accounts in the summary helper.  They should be lists of tuples
    # of (generic title, summary format, account code).
    #
    # The following variables are available.  Variables are surrounded in brackets.
    #
    #  month_no: The numeric month of the current date
    #  month_name: The month name of the current date
    #  last_month_no: The numeric previous month of the current date
    #  last_month_name: The previous month name of the current date
    #  last_bimonthly_from_no: The first month number of the last bimonthly period
    #  last_bimonthly_from_name: The first month name of the last bimonthly period
    #  last_bimonthly_to_no: The second month number of the last bimonthly period
    #  last_bimonthly_to_name: The second month name of the last bimonthly period
    #
    REGULAR_ACCOUNTS = {
        "debit": [
            ("Rent", "Rent for (month_name)", "6252"),
            ("Gas bill",
             "Gas bill for (last_bimonthly_from_name)-(last_bimonthly_to_name)",
             "6261"),
        ],
        "credit": [
            ("Payroll", "Payroll for (last_month_name)", "46116"),
        ],
    }


Bugs and Supports
=================

The Mia! Accounting Django application is hosted on GitHub.

    https://github.com/imacat/mia-accounting-django

Address all bugs and support requests to imacat@mail.imacat.idv.tw.


Copyright
=========

 Copyright (c) 2020-2023 imacat.

 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.
