# mia-accounting

The Django Accounting application.

## Description

`mia-accounting` is a Django accounting application.  It was a re-write of my
own private accounting application written in Perl for `mod_perl` in 2007.  The
revision aims to be mobile-friendly with Bootstrap, with a modern back-end
framework and front-end technology like jQuery.  The first revision was in
Perl / Mojolicious in 2019.  This is the second revision in Python / Django
in 2020.

`mia-accounting` comes with two parts:

* The `accounting` application contains the main accounting application. 

* The `mia_core` application contains core shared libraries that are used by the
accounting application and my other applications.

You may try it in live demonstration at
https://accounting.imacat.idv.tw/accounting .
* Username: `admin`
* Password: `12345`

## Installation

### Requirements

`mia-accounting` requires Python 3.6 or above to work.

Install the required packages with `pip`.

```
pip install django django-dirtyfields titlecase django-decorator-include
```

### Download

The Mia! Accounting project is hosted on GitHub.

https://github.com/imacat/mia-accounting

You can download or clone the project from from GitHub

```
git clone git@github.com:imacat/mia-accounting.git
```

Move the `accounting` and `mia_core` directories into your Django project root
directory.

### `settings.py`

Add these two applications in the `INSTALL_APPS` section of your `settings.py`.

```
INSTALLED_APPS = [
  'mia_core.apps.MiaCoreConfig',
  'accounting.apps.AccountingConfig',
  ...
]
```

Make sure the locale middleware is in the `MIDDLEWARE` section of your
`settings.py`, and add it if it is not added yet.

```
MIDDLEWARE = [
  ...
  'django.middleware.locale.LocaleMiddleware',
  ...
]
```

### `urls.py`

Add the `accounting` application in the `urlpatterns` of your `urls.py`.

```
urlpatterns = [
  ...
  path('accounting/', decorator_include(login_required, 'accounting.urls')),
  ...
]
```

Make sure `i18n` and `jsi18n` are also in the `urlpatterns` of your `urls.py`,
and add them if they are not added yet.

```
urlpatterns = [
  ...
  path('i18n/', include("django.conf.urls.i18n")),
  path('jsi18n/', JavaScriptCatalog.as_view(), name='javascript-catalog'),
  ...
]
```

### `base.html`

Add the following to the very beginning of your base template
`base.html`, before your first real HTML tag.

```
{% load mia_core %}
{% init_libs %}
{% block settings %}{% endblock %}
```

Add the CSS and JavaScripts in the `<head>...</head>` section of your
base template `base.html`.

```
{% for css in libs.css %}
  <link rel="stylesheet" type="text/css" href="{% if css|is_static_url %}{% static css %}{% else %}{{ css }}{% endif %}" />
{% endfor %}
{% for js in libs.js %}
  <script src="{% if js|is_static_url %}{% static js %}{% else %}{{ js }}{% endif %}"></script>
{% endfor %}
```

### Restart Your Web Project

## Advanced Settings

The following advanced settings are available in `settings.py`.

```
# Settings for the accounting application
ACCOUNTING = {
    # The default cash acount, for ex., "0" (current assets and liabilities),
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
                "edatatables/css/dataTables.bootstrap4.min.css"],
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
# of (generic title, title format, account code).
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
```

## Bugs and Supports

Address all bugs and support requests to imacat@mail.imacat.idv.tw.

## Copyright

```
 Copyright (c) 2020 imacat.

 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.
```
