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

"""
Command line utilities.
"""

from abc import ABC, abstractmethod
from collections.abc import Callable
import sys
from typing import Any, Dict, Generic, Optional, TypeVar

from pydantic.v1 import BaseModel, Field
from pydantic_argparse import ArgumentParser


class ActionCommand(Callable, BaseModel):
    """
    Base class for a Pydantic-Argparse command
    """
    pass


class StringCommand(ActionCommand):

    @staticmethod
    def type(display_str: str):
        class _StringCommand(StringCommand):
            def __call__(self, file=sys.stdout):
                print(display_str, file=file)
        return _StringCommand


COPYRIGHT_DESCRIPTION = 'print the copyright and exit'
LICENSE_DESCRIPTION = 'print the software license and exit'
VERSION_DESCRIPTION = 'print the version number and exit'


BaseModelT = TypeVar('BaseModelT', bound=BaseModel)


class BaseCli(Generic[BaseModelT]):
    """
    Base class for general CLI functionality.

    ``BaseModelT`` represents a Pydantic-Argparse model type deriving from
    ``BaseModel``.

    For each command ``x-y-z`` induced by a Pydantic-Argparse field named
    ``x_y_z`` deriving from ``BaseModel`` , the ``dispatch()`` method expects a
    method named ``_x_y_z``.
    """

    def __init__(self, **extra):
        """
        Makes a new BaseCli instance.

        :param extra: Keyword arguments. Must include ``model``, the
                      ``BaseModel`` type corresponding to ``BaseModelT``. Must
                      include ``prog``, the command-line name of the program.
                      Must include ``description``, the description string of
                      the program.
        """
        super().__init__()
        self._args: Optional[BaseModelT] = None
        self._parser: Optional[ArgumentParser] = None
        self.extra: Dict[str, Any] = dict(**extra)

    def run(self) -> None:
        """
        Runs the command line tool:

        *  Creates a Pydantic-Argparse ``ArgumentParser`` with ``model``,
           ``prog`` and ``description`` from the constructor keyword
           arguments in ``self.parser``.

        *  Stores the Pydantic-Argparse parsed arguemnts in ``self.args``.

        *  Calls ``dispatch()``.

        :return: Nothing.
        """
        self._parser: ArgumentParser = ArgumentParser(model=self.extra.get('model'),
                                                      prog=self.extra.get('prog'),
                                                      description=self.extra.get('description'))
        self._args = self._parser.parse_typed_args()
        self.dispatch()

    def dispatch(self) -> None:
        """
        Dispatches from the first field ``x_y_z`` in ``self.args`` that is a
        command (i.e. whose value derives from ``BaseModel``) to a method
        called ``_x_y_z``.

        :return: Nothing.
        """
        field_names = self._args.__class__.__fields__.keys()
        for field_name in field_names:
            field_value = getattr(self._args, field_name)
            if issubclass(type(field_value), BaseModel):
                func = getattr(self, f'_{field_name}')
                if callable(func):
                    func(field_value)
                else:
                    self._parser.exit(1, f'internal error: no _{field_name} callable for the {field_name} command')
                break
        else:
            self._parser.error(f'unknown command; expected one of {', '.join(field_names)}')


def at_most_one_from_enum(model_cls, values: Dict[str, Any], enum_cls) -> Dict[str, Any]:
    """
    Among the fields of a Pydantic-Argparse model whose ``Field`` definition is
    tagged with the ``enum`` keyword set to the given ``Enum`` type, ensures
    that at most one of them has a true value in the given Pydantic-Argparse
    validator ``values``, or raises a ``ValueError`` otherwise.

    :param model_cls: A Pydantic-Argparse model class.
    :param values:    The Pydantic-Argparse validator ``values``.
    :param enum_cls:  The ``Enum`` class the fields of the Pydantic-Argparse
                      model are tagged with (using the ``enum`` keyword).
    :return: The ``values`` argument, if no ``ValueError`` has been raised.
    """
    enum_names = [field_name for field_name, model_field in model_cls.__fields__.items() if model_field.field_info.extra.get('enum') == enum_cls]
    ret = [field_name for field_name in enum_names if values.get(field_name)]
    if (length := len(ret)) > 1:
        raise ValueError(f'at most one of {', '.join([option_name(enum_name) for enum_name in enum_names])} is allowed, got {length} ({', '.join([option_name(enum_name) for enum_name in ret])})')
    return values


def get_from_enum(model_inst, enum_cls, default=None):
    """
    Among the fields of a Pydantic-Argparse model whose ``Field`` definition is
    tagged with the ``enum`` keyword set to the given ``Enum`` type, gets the
    corresponding enum value of the first with a true value in the model, or
    returns the given default value. Assumes the existence of a
    ``from_member()`` static method in the ``Enum`` class.

    :param model_inst:
    :param enum_cls:
    :param default:
    :return:
    """
    enum_names = [field_name for field_name, model_field in type(model_inst).__fields__.items() if model_field.field_info.extra.get('enum') == enum_cls]
    for field_name in enum_names:
        if getattr(model_inst, field_name):
            return enum_cls[field_name]
    return default


def at_most_one(values: Dict[str, Any], *names: str):
    if (length := _matchy_length(values, *names)) > 1:
        raise ValueError(f'at most one of {', '.join([option_name(name) for name in names])} is allowed, got {length}')
    return values


def exactly_one(values: Dict[str, Any], *names: str):
    if (length := _matchy_length(values, *names)) != 1:
        raise ValueError(f'exactly one of {', '.join([option_name(name) for name in names])} is required, got {length}')
    return values


def one_or_more(values: Dict[str, Any], *names: str):
    if _matchy_length(values, *names) == 0:
        raise ValueError(f'one or more of {', '.join([option_name(name) for name in names])} is required')
    return values


def option_name(name: str):
    return f'{('-' if len(name) == 1 else '--')}{name.replace('_', '-')}'


def _matchy_length(values: Dict[str, Any], *names: str) -> int:
    return len([name for name in names if values.get(name)])
