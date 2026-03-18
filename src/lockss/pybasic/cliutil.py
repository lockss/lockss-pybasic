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

from pathlib import Path
from typing import Any, Optional, Union

import click
from click.types import ParamType, IntRange
from click_extra import ChoiceSource, EnumChoice, ExtraContext, HelpExtraFormatter, Style, TableFormat, option
from click_extra.colorize import default_theme


def click_path(spec: Optional[str]) -> click.Path:
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
            exists = True
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


def compose_decorators(*decorators):
    def wrapped(decorated):
        for dec in reversed(decorators):
            decorated = dec(decorated)
        return decorated
    return wrapped


def make_table_format_option(switches: Union[str, tuple[str, ...]] = ('--table-format', '-T'),
                             default: TableFormat = TableFormat.SIMPLE):
    if type(switches) == str:
        switches = (switches,)
    return option(*switches, type=EnumChoice(TableFormat, choice_source=ChoiceSource.VALUE), default=default, show_default=True, help='Set the rendering of tables to the given style.')


def make_extra_context_settings() -> dict[str, Any]:
    return ExtraContext.settings(
        formatter_settings=HelpExtraFormatter.settings(
            theme=default_theme.with_(
                invoked_command=Style(bold=True)
            )
        )
    )


PositiveInt: ParamType = IntRange(min=1, max=None)


NonNegativeInt: ParamType = IntRange(min=0, max=None)


NegativeInt: ParamType = IntRange(min=None, max=-1)


NonPositiveInt: ParamType = IntRange(min=None, max=0)


UInt16: ParamType = IntRange(min=0, max=65535)
