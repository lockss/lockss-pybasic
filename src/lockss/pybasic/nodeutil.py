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
from typing import Annotated, Any, ClassVar, Literal, Optional, Union

from annotated_types import Ge, Le
from pydantic import BaseModel, BeforeValidator, Field, TypeAdapter


#: An annotated type for port numbers (0-65535)
PortNumber = Annotated[int, Ge(0), Le(65535)]


class NodeTypeEnum(Enum):
    """An enumerated type representing LOCKSS node types."""
    #: An enumerated constant representing LOCKSS 1.x nodes.
    V1 = 'v1'
    #: An enumerated constant representing LOCKSS 2.x nodes.
    V2 = 'v2'


class NodeProtocolEnum(Enum):
    """An enumerated type representing protocols for reaching LOCKSS nodes."""
    #: An enumerated constant representing HTTP.
    HTTP = 'http'
    #: An enumerated constant representing HTTPS.
    HTTPS = 'https'


class BaseNodeSpec(BaseModel):

    DEFAULT_PROTOCOL: ClassVar[NodeProtocolEnum] = NodeProtocolEnum.HTTP

    TYPE_FIELD: ClassVar[dict[str, str]] = dict(title='Type',
                                                description="The node's type")

    protocol: NodeProtocolEnum = Field(default=DEFAULT_PROTOCOL,
                                       title='Protocol',
                                       description="The protocol for reaching the node")

    host: str = Field(title='Host',
                      description="The node's host")


class NodeSpec1(BaseNodeSpec):

    DEFAULT_UI_PORT_V1: ClassVar[int] = 8081

    type: Literal['v1'] = Field(**BaseNodeSpec.TYPE_FIELD)

    ui: PortNumber = Field(default=DEFAULT_UI_PORT_V1,
                           title='UI Port',
                           description="The LOCKSS 1.x node's Web user interface port")


class NodeSpec2(BaseNodeSpec):

    DEFAULT_REPO_PORT: ClassVar[int] = 24611

    DEFAULT_CFG_PORT: ClassVar[int] = 24612

    DEFAULT_POL_PORT: ClassVar[int] = 24613

    DEFAULT_CRW_PORT: ClassVar[int] = 24614

    DEFAULT_MD_PORT: ClassVar[int] = 24615

    DEFAULT_SOAP_PORT: ClassVar[int] = 24616

    type: Literal['v2'] = Field(**BaseNodeSpec.TYPE_FIELD)

    repository: PortNumber = Field(default=DEFAULT_REPO_PORT,
                                   title='Repository Port',
                                   description="The node's Repository Service REST API Port")

    configuration: PortNumber = Field(default=DEFAULT_CFG_PORT,
                                      title='Configuration Port',
                                      description="The node's Configuration Service REST API Port")

    poller: PortNumber = Field(default=DEFAULT_POL_PORT,
                               title='Poller Port',
                               description="The node's Poller Service REST API Port")

    crawler: PortNumber = Field(default=DEFAULT_CRW_PORT,
                                title='Crawler Port',
                                description="The node's Crawler Service REST API Port")

    metadata: PortNumber = Field(default=DEFAULT_MD_PORT,
                                 title='Metadata Port',
                                 description="The node's Metadata Service REST API Port")

    soap: PortNumber = Field(default=DEFAULT_SOAP_PORT,
                             title='SOAP Port',
                             description="The node's SOAP Compatibility Service REST API Port")


_RE_COMPACT_NODE_SPEC: Pattern[str] = re.compile(r'((?P<protocol>https?)://)?(?P<host>[^:]+)(:(?P<repository>\d+|(?=:))(:(?P<configuration>\d+|(?=:))(:(?P<poller>\d+|(?=:))(:(?P<crawler>\d+|(?=:))(:(?P<metadata>\d+|(?=:))(:(?P<soap>\d+))?)?)?)?)?)?')


#: A type for LOCKSS node specification strings.
CompactNodeSpec = str


def _parse_compact_node_spec(compact_node_spec: CompactNodeSpec) -> dict[str, str]:
    mat: Optional[Match[str]] = _RE_COMPACT_NODE_SPEC.fullmatch(compact_node_spec)
    if mat is None:
        raise ValueError(f'Invalid compact node specification: {compact_node_spec}')
    d = dict(host=mat.group('host'))
    if prot := mat.group('protocol'):
        d['protocol'] = prot
    five = ('configuration', 'poller', 'crawler', 'metadata', 'soap')
    if repo_or_ui := mat.group('repository'):
        if any(mat.group(x) for x in five) or len(repo_or_ui) >= 5:
            # 10000 or larger: assume V2
            d['type'] = NodeTypeEnum.V2.value
            d['repository'] = repo_or_ui
        elif len(repo_or_ui) == 4:
            # 1000 through 9999: assume V1
            d['type'] = NodeTypeEnum.V1.value
            d['ui'] = repo_or_ui
        else:
            raise ValueError(f'Invalid repository/UI port in compact node specification: {repo_or_ui}')
    else:
        # Assume V2
        d['type'] = NodeTypeEnum.V2.value
    for k in five:
        if p := mat.group(k):
            d[k] = p # string okay, will be coerced to int
    return d


def _maybe_deserialize_compact_node_spec(value: Any) -> Any:
    if isinstance(value, CompactNodeSpec) and not value.startswith('{'):
        return _parse_compact_node_spec(value)
    return value


#: A type for LOCKSS node specifications, that also accepts a compact LOCKSS
#: node specification.
NodeSpec = Annotated[
    Annotated[Union[NodeSpec1, NodeSpec2], Field(discriminator='type')],
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


NodeSetKind = Literal['NodeSet']


NodeSetIdentifier = str


NodeIdentifier = str


class NodeSet(BaseModel):

    kind: NodeSetKind = Field(title='Kind',
                              description="This object's kind")

    id: NodeSetIdentifier = Field(title='Node Set Identifier',
                                  description='An identifier for the node set')

    name: str = Field(title='Node Set Name',
                      description='A name for the node set')

    nodes: dict[NodeIdentifier, NodeSpec] = Field(min_length=1,
                                                  title='Nodes',
                                                  description='A non-empty list of nodes')
