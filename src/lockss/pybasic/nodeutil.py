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
LOCKSS node utilities.
"""

from enum import Enum
from re import Pattern
import re
from typing import Any, Optional

from pydantic import BaseModel, Field, model_validator

from .errorutil import InternalError


RE_NODE_REFERENCE: Pattern = re.compile(r'((?P<protocol>https?)://)?(?P<host>[^:]+)(:(?P<repository>\d+|(?=:))(:(?P<configuration>\d+|(?=:))(:(?P<poller>\d+|(?=:))(:(?P<crawler>\d+|(?=:))(:(?P<metadata>\d+|(?=:))(:(?P<soap>\d+))?)?)?)?)?)?')


class LockssNodeTypeEnum(Enum):
    V1 = 'v1'
    V2 = 'v2'


class LockssNodeProtocolEnum(Enum):
    HTTP = 'http'
    HTTPS = 'https'


DEFAULT_UI_PORT_V1: int = 8081

DEFAULT_REPO_PORT: int = 24611

DEFAULT_CFG_PORT: int = 24612

DEFAULT_POL_PORT: int = 24613

DEFAULT_CRW_PORT: int = 24614

DEFAULT_MD_PORT: int = 24615

DEFAULT_SOAP_PORT: int = 24616


class LockssNodeModel(BaseModel):
    host: str = Field(title='Host', description="The LOCKSS node's host")
    type: LockssNodeTypeEnum = Field(default=LockssNodeTypeEnum.V2, title='Type', description='LOCKSS node type')
    protocol: LockssNodeProtocolEnum = Field(default=LockssNodeProtocolEnum.HTTPS, title='Protocol', description="The protocol for reaching the node")
    repository: int = Field(default=DEFAULT_REPO_PORT, title='Repository Port', description="The node's Repository Service REST API Port")
    configuration: int = Field(default=DEFAULT_CFG_PORT, title='Configuration Port', description="The node's Configuration Service REST API Port")
    poller: int = Field(default=DEFAULT_POL_PORT, title='Poller Port', description="The node's Poller Service REST API Port")
    crawler: int = Field(default=DEFAULT_CRW_PORT, title='Crawler Port', description="The node's Crawler Service REST API Port")
    metadata: int = Field(default=DEFAULT_MD_PORT, title='Metadata Port', description="The node's Metadata Service REST API Port")
    soap: int = Field(default=DEFAULT_SOAP_PORT, title='SOAP Port', description="The node's SOAP Compatibility Service REST API Port")
    ui: int = Field(default=DEFAULT_UI_PORT_V1, title='UI Port', description="The LOCKSS 1.x node's Web user interface port")

    @model_validator(mode='before')
    @classmethod
    def _validate_model_type(cls, data: Any) -> Any:
        _has, _get, _set = (dict.__contains__, dict.get, dict.__setitem__) if isinstance(data, dict) else (hasattr, getattr, setattr)
        if (host_orig := _get(data, 'host', None)) is not None and isinstance(host_orig, str):
            host_ref: str = host_orig
            mat = RE_NODE_REFERENCE.fullmatch(host_ref)
            if mat is None:
                raise ValueError(f'Invalid node reference: {host_ref}')
            # Avoid conflicting definitions
            five = ('configuration', 'poller', 'crawler', 'metadata', 'soap')
            for k in ('protocol', *five):
                if h_val := mat.group(k):
                    if _get(data, k, None) is not None:
                        raise ValueError(f"Node reference conflicts with '{k}' definition: {h_val}")
                    _set(data, k, h_val)
            # 'repository' + 'ui' is more complicated
            if h_repo_or_ui := mat.group('repository'):
                for k in ('repository', 'ui'):
                    if _get(data, k, None) is not None:
                        raise ValueError(f"Node reference conflicts with '{k}' definition: {h_repo_or_ui}")
                try:
                    repo_or_ui_int: int = int(h_repo_or_ui)
                except ValueError as ve:
                    raise InternalError from ve # shouldn't happen, should be \d+
                if any(mat.group(x) for x in five) or repo_or_ui_int >= 10000:
                    _set(data, 'repository', h_repo_or_ui)  # Assume v2
                elif 1000 <= repo_or_ui_int < 10000:
                    _set(data, 'ui', h_repo_or_ui) # Assume v1
                    if _get(data, 'type', None) is None:
                        _set(data, 'type', LockssNodeTypeEnum.V1.value)
                else:
                    raise ValueError(f'Invalid repository/UI port in node reference: {repo_or_ui_int}')
            # Finally, reset 'host'
            if any(mat.group(x) for x in ('protocol', 'repository', *five)):
                _set(data, 'host', mat.group('host'))
        return data
