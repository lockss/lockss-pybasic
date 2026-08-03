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
from re import Match, Pattern
import re
from typing import Annotated, Any, ClassVar, Literal, Optional, TypeAlias, Union

from annotated_types import Ge, Le
from pydantic import BaseModel, BeforeValidator, Field, TypeAdapter, model_validator


#: An annotated type for port numbers (0-65535)
PortNumber: TypeAlias = Annotated[int, Ge(0), Le(65535)]


class NodeTypeEnum(Enum):
    """An enumerated type representing LOCKSS node types."""
    #: An enumerated constant representing a LOCKSS 1.x node.
    V1 = 'v1'
    #: An enumerated constant representing a LOCKSS 2.x node.
    V2 = 'v2'
    #: An enumerated constant representing a LOCKSS 1.x and 2.x node pair in
    #: migration mode.
    V1_V2_MIGRATION_PAIR = 'v1-v2-migration-pair'


class NodeProtocolEnum(Enum):
    """An enumerated type representing protocols for reaching LOCKSS nodes."""
    #: An enumerated constant representing HTTP.
    HTTP = 'http'
    #: An enumerated constant representing HTTPS.
    HTTPS = 'https'


NodeSpecKind: TypeAlias = Literal['NodeSpec']


NodeIdentifier: TypeAlias = str


class BaseNodeSpec(BaseModel):

    DEFAULT_PROTOCOL: ClassVar[NodeProtocolEnum] = NodeProtocolEnum.HTTP

    TYPE_FIELD: ClassVar[dict[str, str]] = dict(title='Type',
                                                description="The node's type")

    kind: NodeSpecKind = Field(title='Kind',
                               description="This object's kind")

    id: NodeIdentifier = Field(title='Node Identifier',
                               description='An identifier for the node')

    protocol: NodeProtocolEnum = Field(default=DEFAULT_PROTOCOL,
                                       title='Protocol',
                                       description="The protocol for reaching the node")


class NodeSpec1(BaseNodeSpec):

    DEFAULT_UI_PORT_V1: ClassVar[int] = 8081

    type: Literal['v1'] = Field(**BaseNodeSpec.TYPE_FIELD)

    host: str = Field(title='Host',
                      description="The node's host")

    ui: PortNumber = Field(title='UI Port',
                           description="The LOCKSS 1.x node's Web user interface port")

    def get_host(self) -> str:
        return f'{self.protocol.value}://{self.host}:{self.ui}'

    @model_validator(mode='before')
    @classmethod
    def _parse_compact_node_spec(cls, data: Any) -> Any:
        return _maybe_deserialize_compact_node_spec(data)


class NodeSpec2(BaseNodeSpec):

    DEFAULT_REPO_PORT: ClassVar[int] = 24611

    DEFAULT_CFG_PORT: ClassVar[int] = 24612

    DEFAULT_POL_PORT: ClassVar[int] = 24613

    DEFAULT_CRW_PORT: ClassVar[int] = 24614

    DEFAULT_MD_PORT: ClassVar[int] = 24615

    DEFAULT_SOAP_PORT: ClassVar[int] = 24616

    type: Literal['v2'] = Field(**BaseNodeSpec.TYPE_FIELD)

    host: str = Field(title='Host',
                      description="The node's host")

    repository: PortNumber = Field(title='Repository Port',
                                   description="The node's Repository Service REST API Port")

    configuration: PortNumber = Field(title='Configuration Port',
                                      description="The node's Configuration Service REST API Port")

    poller: PortNumber = Field(title='Poller Port',
                               description="The node's Poller Service REST API Port")

    crawler: Optional[PortNumber] = Field(default=None,
                                          title='Crawler Port',
                                          description="The node's Crawler Service REST API Port")

    metadata: Optional[PortNumber] = Field(default=None,
                                           title='Metadata Port',
                                           description="The node's Metadata Service REST API Port")

    soap: Optional[PortNumber] = Field(default=None,
                                       title='SOAP Port',
                                       description="The node's SOAP Compatibility Service REST API Port")

    def get_repository_host(self) -> str:
        return self._generic_get_host(self.repository)

    def get_configuration_host(self) -> str:
        return self._generic_get_host(self.configuration)

    def get_poller_host(self) -> str:
        return self._generic_get_host(self.poller)

    def get_crawler_host(self) -> str:
        return self._generic_get_host(self.crawler)

    def get_metadata_host(self) -> str:
        return self._generic_get_host(self.metadata)

    def get_soap_host(self) -> str:
        return self._generic_get_host(self.soap)

    def _generic_get_host(self, port: Optional[PortNumber]) -> str:
        return f'{self.protocol}://{self.host}:{port}'

    @model_validator(mode='before')
    @classmethod
    def _parse_compact_node_spec(cls, data: Any) -> Any:
        return _maybe_deserialize_compact_node_spec(data)


class NodeSpec12Pair(BaseNodeSpec):

    type: Literal['v1-v2-migration-pair'] = Field(**BaseNodeSpec.TYPE_FIELD)

    origin: NodeSpec1 = Field(title='Origin',
                              description='The origin node (LOCKSS 1.x)')

    destination: NodeSpec2 = Field(title='Destination',
                                   description='The destination node (LOCKSS 2.x)')


#_RE_COMPACT_NODE_SPEC: Pattern[str] = re.compile(r'((?P<protocol>https?)://)?(?P<host>[^:]+)(:(?P<repository>\d+)(:(?P<configuration>\d+)(:(?P<poller>\d+)(:(?P<crawler>\d+|(?=:))(:(?P<metadata>\d+|(?=:))(:(?P<soap>\d+))?)?)?)?)?)?')

#: A type for LOCKSS node specification strings.
CompactNodeSpec: TypeAlias = str


_RE_COMPACT_NODE_SPEC: Pattern[str] = re.compile(r'((?P<protocol>https?)://)?(?P<host>[^:]+)(:(?P<repository>\d*)(?P<v2>:(?P<configuration>\d*)(:(?P<poller>\d*)(:(?P<crawler>\d*)(:(?P<metadata>\d*)(:(?P<soap>\d*))?)?)?)?)?)?')


def _parse_compact_node_spec(compact_node_spec: CompactNodeSpec) -> dict[str, str]:
    mat: Optional[Match[str]] = _RE_COMPACT_NODE_SPEC.fullmatch(compact_node_spec)
    if mat is None:
        raise ValueError(f'Invalid compact node specification: {compact_node_spec}')
    d = dict(kind='NodeSpec', id=compact_node_spec, host=mat.group('host'))
    if prot := mat.group('protocol'):
        d['protocol'] = prot
    if mat.group('v2'):
        d['type'] = NodeTypeEnum.V2.value
        for k in ('repository', 'configuration', 'poller', 'crawler', 'metadata', 'soap'):
            if v := mat.group(k):
                d[k] = v
    else:
        d['type'] = NodeTypeEnum.V1.value
        if v := mat.group('repository'):
            d['ui'] = v
    return d


def _maybe_deserialize_compact_node_spec(value: Any) -> Any:
    if isinstance(value, CompactNodeSpec) and not value.startswith('{'):
        return _parse_compact_node_spec(value)
    return value


#: A type for LOCKSS node specifications, that also accepts a compact LOCKSS
#: node specification.
NodeSpec: TypeAlias = Annotated[
    Annotated[Union[NodeSpec1, NodeSpec2, NodeSpec12Pair], Field(discriminator='type')],
    BeforeValidator(_maybe_deserialize_compact_node_spec)
]


#: A type adapter for the NodeSpec type.
_node_spec_adapter: TypeAdapter[NodeSpec] = TypeAdapter(NodeSpec)


def get_node_spec_adapter() -> TypeAdapter[NodeSpec]:
    """
    Gets a type adapter for the NodeSpec type, which is a union type and cannot
    be instantiated directly.

    :return: A type adapter for the NodeSpec type.
    """
    return _node_spec_adapter


NodeSetKind: TypeAlias = Literal['NodeSet']


NodeSetIdentifier: TypeAlias = str


class NodeSet(BaseModel):

    kind: NodeSetKind = Field(title='Kind',
                              description="This object's kind")

    id: NodeSetIdentifier = Field(title='Node Set Identifier',
                                  description='An identifier for the node set')

    name: str = Field(title='Node Set Name',
                      description='A name for the node set')

    nodes: list[NodeSpec] = Field(min_length=1,
                                  title='Nodes',
                                  description='A non-empty list of nodes')
