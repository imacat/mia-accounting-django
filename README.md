# mia-accounting

The Mia! Accounting Application Built on Python Django

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

## Live Demonstration

https://accounting.imacat.idv.tw/accounting
* Username: admin
* Password: 12345

## Installation

### Requirements

Installs the following requirements with pip:

* Python 3.6 or above
* Django 3.0 or above
* django-dirtyfields
* django-decorator-include
* titlecase

### Download

Clones the project from GitHub

```
git clone git@github.com:imacat/mia-accounting.git
```

Moves the accounting and mia_core directories into your Django project root
directory.

### Configure Your settings.py

Adds these two applications into your INSTALL_APPS.

```
'mia_core.apps.MiaCoreConfig'
'accounting.apps.AccountingConfig'
```

Adds the locale middleware if it is not added yet.

```
'django.middleware.locale.LocaleMiddleware'
```

### Configure Your urls.py:

Adds this line into your urls.py:

```
path('accounting/', decorator_include(login_required, 'accounting.urls')),
```

Ensures these two lines are also in your urls.py, if they are not yet:

```
path('i18n/', include("django.conf.urls.i18n")),
path('jsi18n/', JavaScriptCatalog.as_view(), name='javascript-catalog'),
```

### Restarts Your Web Project

## Bugs and Supports

Address all bugs and support requests to imacat@mail.imacat.idv.tw.
