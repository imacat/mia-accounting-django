# The setup.py
#   by imacat <imacat@mail.imacat.idv.tw>, 2020/9/7

#  Copyright (c) 2020 imacat.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="mia-accounting",
    version="0.0.1",
    author="imacat",
    author_email="imacat@mail.imacat.idv.tw",
    description="A Django accounting application",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/imacat/mia-accounting",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Framework :: Django :: 3.0",
        "Topic :: Office/Business :: Financial :: Accounting",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    install_requires=["django", "django-dirtyfields", "titlecase",
                      "django-decorator-include"],
)
