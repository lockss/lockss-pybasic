#!/usr/bin/env python3

# Copyright (c) 2000-2026, Board of Trustees of Leland Stanford Jr. University
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

from pathlib import Path
from typing import Any, Optional, Union

import click
from click.types import ParamType, IntRange
from click_extra import ChoiceSource, EnumChoice, ExtraContext, HelpExtraFormatter, Style, TableFormat, option
from click_extra.colorize import default_theme


def click_path(spec: Optional[str]) -> click.Path:
    """
    Generates a ``click.Path`` based on a specification string.

    The specification string can contain the following specifier characters:

    .. list-table::
       :header-rows: 1

       *  *  Specifier
          *  Present
          *  Mutually exclusive with
       *  *  ``f``
          *  Must be a file
          *  ``d`` [*]
       *  *  ``d``
          *  Must be a directory
          *  ``f`` [*]
       *  *  ``e``
          *  File or directory must exist
          *  ``E``
       *  *  ``E``
          *  File or directory may or may not exist, but if it does not exist,
             other checks are skipped (default)
          *  ``e``
       *  *  ``r``
          *  File or directory must be readable
          *
       *  *  ``w``
          *  File or directory must be writable
          *
       *  *  ``x``
          *  File or directory must be executable
          *
       *  *  ``p``
          *  Resulting path will be ``pathlib.Path`` (default)
          *  ``s``
       *  *  ``s``
          *  Resulting path will be ``str``
          *  ``p``
       *  *  ``-``
          *  Path is allowed to be ``-``
          *
       *  *  ``z``
          *  Path will be absolute and resolved, with ``pathlib.Path.resolve``
          *

    When two mutual exclusive specifiers are present, ``ValueError`` is raised.

    :param spec: A specification string.
    :type spec: str
    :return: A ``click.Path``.
    :rtype: click.Path
    :raises ValueError: If two mutually exclusive specifiers are present in the
                        specification string.
    """
    if spec is None:
        spec = ''
    allow_dash = False
    dir_okay = True
    executable = False
    exists = False
    file_okay = True
    path_type = Path
    readable = True
    resolve_path = False
    writable = False
    for char in spec:
        if char == 'd':
            if 'f' in spec:
                raise ValueError(f'"d" and "f" are mutually exclusive: {spec}')
            dir_okay = True
            file_okay = False
        elif char == 'e':
            if 'E' in spec:
                raise ValueError(f'"e" and "E" are mutually exclusive: {spec}')
            exists = True
        elif char == 'E':
            if 'e' in spec:
                raise ValueError(f'"E" and "e" are mutually exclusive: {spec}')
            exists = False
        elif char == 'f':
            if 'd' in spec:
                raise ValueError(f'"f" and "d" are mutually exclusive: {spec}')
            dir_okay = False
            file_okay = True
        elif char == 'p':
            if 's' in spec:
                raise ValueError(f'"p" and "s" are mutually exclusive: {spec}')
            path_type = Path
        elif char == 'r':
            readable = True
        elif char == 's':
            if 'p' in spec:
                raise ValueError(f'"s" and "p" are mutually exclusive: {spec}')
            path_type = str
        elif char == 'w':
            writable = True
        elif char == 'x':
            executable = True
        elif char == 'z':
            resolve_path = True
        elif char == '-':
            allow_dash = True
        else:
            raise ValueError(f'unknown specification character "{char}": {spec}')
    return click.Path(allow_dash=allow_dash,
                      dir_okay=dir_okay,
                      executable=executable,
                      exists=exists,
                      file_okay=file_okay,
                      path_type=path_type,
                      readable=readable,
                      resolve_path=resolve_path,
                      writable=writable)


#: Composes the given decorators, so that
#:     @compose_decorators(f, g, h)
#:     def foo():
#:         pass
#: is equivalent to:
#:     @f
#      @g
#      @h
#:     def foo():
#:         pass
def compose_decorators(*decorators):
    def wrapped(decorated):
        for dec in reversed(decorators):
            decorated = dec(decorated)
        return decorated
    return wrapped


def make_table_format_option(switches: Union[str, tuple[str, ...]] = ('--table-format', '-T'),
                             default: TableFormat = TableFormat.SIMPLE):
    """
    Makes an equivalent of ``click_Extra.table_format_option`` with the given
    command line switches and the given table format default.

    The standard ``click_Extra.table_format_option`` attaches to the top-level
    command only.

    :param switches: A string or tuple of strings for the command line switches.
    :type switches: Union[str, tuple[str, ...]]
    :param default: A ``click_extra.TableFormat`` default.
    :type default: TableFormat
    :return: A remixed ``click_Extra.table_format_option``.
    :rtype:
    """
    if type(switches) == str:
        switches = (switches,)
    return option(*switches, type=EnumChoice(TableFormat, choice_source=ChoiceSource.VALUE), default=default, show_default=True, help='Set the rendering of tables to the given style.')


def make_extra_context_settings() -> dict[str, Any]:
    """
    Makes a custom ``click_Extra.ExtraContext`` with essential changes.

    Currently, the only change is that the help formatter styles the invoked
    command in bold.

    :return: A custom ``click_Extra.ExtraContext``.
    :rtype: dict[str, Any]
    """
    return ExtraContext.settings(
        formatter_settings=HelpExtraFormatter.settings(
            theme=default_theme.with_(
                invoked_command=Style(bold=True)
            )
        )
    )


#: A ``click.ParamType`` for strictly positive integers (1 to infinity).
PositiveInt: ParamType = IntRange(min=1, max=None)


#: A ``click.ParamType`` for non-negative integers (0 to infinity).
NonNegativeInt: ParamType = IntRange(min=0, max=None)


#: A ``click.ParamType`` for strictly negative integers (negative infinity to -1).
NegativeInt: ParamType = IntRange(min=None, max=-1)


#: A ``click.ParamType`` for non-positive integers (negative infinity to 0).
NonPositiveInt: ParamType = IntRange(min=None, max=0)


#: A ``click.ParamType`` for unsigned 16-bit integers (0 to 65535).
UInt16: ParamType = IntRange(min=0, max=65535)
