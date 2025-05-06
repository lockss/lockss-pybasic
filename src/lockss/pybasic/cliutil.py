#!/usr/bin/env python3

# Copyright (c) 2000-2025, Board of Trustees of Leland Stanford Jr. University
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its contributors
# may be used to endorse or promote products derived from this software without
# specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

'''
Command line utilities.
'''

from abc import ABC, abstractmethod
import sys
from typing import Any, Dict, Generic, List, TypeVar

from pydantic.v1 import BaseModel, Field
from pydantic_argparse import ArgumentParser


class Printable(ABC):

    def print(self, file=sys.stdout):
        print(self.get_display(), file=file)

    @abstractmethod
    def get_display(self):
        pass


class CopyrightCommand:

    @staticmethod
    def make(copyright):
        class CopyrightModel(Printable, BaseModel):
            def get_display(self):
                return copyright
        return CopyrightModel

    @staticmethod
    def field():
        return Field(description='print the copyright and exit')


class LicenseCommand:

    @staticmethod
    def make(license):
        class LicenseModel(Printable, BaseModel):
            def get_display(self):
                return license
        return LicenseModel

    @staticmethod
    def field():
        return Field(description='print the software license and exit')


class VersionCommand:

    @staticmethod
    def make(version):
        class VersionModel(Printable, BaseModel):
            def get_display(self):
                return version
        return VersionModel

    @staticmethod
    def field():
        return Field(description='print the version number and exit')


ModelT = TypeVar('ModelT')


class BaseCli(Generic[ModelT], ABC):
    args: ModelT
    extra: Dict[str, Any]
    parser: ArgumentParser

    def __init__(self, **extra):
        super().__init__()
        self.extra = dict(**extra)

    def run(self):
        self.parser: ArgumentParser = ArgumentParser(model=self.extra.get('model'),
                                                     prog=self.extra.get('prog'),
                                                     description=self.extra.get('description'))
        self.args = self.parser.parse_typed_args()
        self.dispatch()

    @abstractmethod
    def dispatch(self):
        pass


def exactly_one(values: Dict[str, Any], *names: str):
    if (length := len([values[name] for name in names if values[name]])) != 1:
        raise ValueError(f'exactly one of {', '.join([option_name(name) for name in names])} is required, got {length}')
    return values


def one_or_more(values: Dict[str, Any], *names: str):
    if len([values[name] for name in names if values[name]]) == 0:
        raise ValueError(f'one or more of {', '.join([option_name(name) for name in names])} is required')
    return values


def option_name(name: str):
    return f'{('-' if len(name) == 1 else '--')}{name.replace('_', '-')}'
