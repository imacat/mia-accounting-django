# mia-accounting

The Mia! Accounting Django Application

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

You can download or clone
the project from from GitHub

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

And the CSS and JavaScripts in the `<head>...</head>` section of your
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

## Bugs and Supports

Address all bugs and support requests to imacat@mail.imacat.idv.tw.

2020/9/7
