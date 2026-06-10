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
Unit tests for lockss.pybasic.nodeutil.
"""

from typing import Optional
from unittest import TestCase

from pydantic import ValidationError

from lockss.pybasic.nodeutil import NodeProtocolEnum, NodeSet, NodeSpec, NodeSpec1, NodeSpec2, NodeTypeEnum, get_node_spec_adapter


class TestNodeUtil(TestCase):

    def test_node_spec(self):
        host = 'myhost'
        def _test_node_spec(proto: str,
                            repo: Optional[str],
                            cfg: Optional[bool],
                            pol: Optional[bool],
                            crw: Optional[bool],
                            md: Optional[bool],
                            soa: Optional[bool]) -> None:
            hr = f'{proto}{host}'
            if repo is not None:
                hr = f'{hr}:{repo}'
                if cfg is not None:
                    hr = f'{hr}{":2" if cfg else ":"}'
                    if pol is not None:
                        hr = f'{hr}{":3" if pol else ":"}'
                        if crw is not None:
                            hr = f'{hr}{":4" if crw else ":"}'
                            if md is not None:
                                hr = f'{hr}{":5" if md else ":"}'
                                if soa is not None:
                                    hr = f'{hr}{":6" if soa else ":"}'
            five = (cfg, pol, crw, md, soa)
            try:
                spec: NodeSpec = get_node_spec_adapter().validate_python(hr)
                self.assertEqual(spec.protocol, NodeProtocolEnum.HTTPS if proto == 'https://' else NodeProtocolEnum.HTTP) # else includes proto == ''
                self.assertEqual(spec.host, host)
                if not any(five) and repo == '4444':
                    self.assertEqual(spec.type, NodeTypeEnum.V1.value)
                    self.assertEqual(spec.ui, int(repo))
                else:
                    self.assertEqual(spec.type, NodeTypeEnum.V2.value)
                    self.assertEqual(spec.repository, int(repo) if repo else NodeSpec2.DEFAULT_REPO_PORT)
                    self.assertEqual(spec.configuration, 2 if cfg else NodeSpec2.DEFAULT_CFG_PORT)
                    self.assertEqual(spec.poller, 3 if pol else NodeSpec2.DEFAULT_POL_PORT)
                    self.assertEqual(spec.crawler, 4 if crw else NodeSpec2.DEFAULT_CRW_PORT)
                    self.assertEqual(spec.metadata, 5 if md else NodeSpec2.DEFAULT_MD_PORT)
                    self.assertEqual(spec.soap, 6 if soa else NodeSpec2.DEFAULT_SOAP_PORT)
            except ValidationError as validation_err:
                self.assertEqual(validation_err.error_count(), 1)
                e0 = validation_err.errors()[0]
                if hr.endswith(':'):
                    self.assertEqual(e0['type'], 'value_error')
                    self.assertEqual(e0['msg'], f'Value error, Invalid compact node specification: {hr}')
                elif repo == '333' and not any(five):
                    self.assertEqual(e0['type'], 'value_error')
                    self.assertEqual(e0['msg'], f'Value error, Invalid repository/UI port in compact node specification: {repo}')
                elif repo == '666666':
                    self.assertEqual(e0['type'], 'less_than_equal')
                    self.assertEqual(e0['msg'], 'Input should be less than or equal to 65535')
                else:
                    self.fail(f'Unexpected ValidationError: {hr}')
            except ValueError as value_err:
                self.fail(f'Unexpected ValueError: {hr}')

        for proto in ('', *(f'{p.value}://' for p in NodeProtocolEnum)):
            for repo in (None, '', '333', '4444', '55555', '666666'):
                if repo is None:
                    _test_node_spec(proto, repo, None, None, None, None, None)
                else:
                    for cfg in (None, False, True):
                        if cfg is None:
                            _test_node_spec(proto, repo, cfg, None, None, None, None)
                        else:
                            for pol in (None, False, True):
                                if pol is None:
                                    _test_node_spec(proto, repo, cfg, pol, None, None, None)
                                else:
                                    for crw in (None, False, True):
                                        if crw is None:
                                            _test_node_spec(proto, repo, cfg, pol, crw, None, None)
                                        else:
                                            for md in (None, False, True):
                                                if md is None:
                                                    _test_node_spec(proto, repo, cfg, pol, crw, md, None)
                                                else:
                                                    for soa in (None, False, True):
                                                        _test_node_spec(proto, repo, cfg, pol, crw, md, soa)

    def test_node_set(self):
        data1 = {
            'kind': 'NodeSet',
            'id': 'mynodeset',
            'name': 'My Node Set',
            'nodes': {
                'node1': {
                    'type': 'v1',
                    'host': 'myhost1',
                },
                'node2': 'myhost2:4444',
                'node3': 'myhost3:55555'
            }
        }
        ns1 = NodeSet(**data1)
        self.assertEqual(len(nodes := ns1.nodes), 3)
        self.assertEqual((n1 := nodes['node1']).type, NodeTypeEnum.V1.value)
        self.assertEqual(n1.host, 'myhost1')
        self.assertEqual(n1.ui, NodeSpec1.DEFAULT_UI_PORT_V1)
        self.assertEqual((n2 := nodes['node2']).type, NodeTypeEnum.V1.value)
        self.assertEqual(n2.host, 'myhost2')
        self.assertEqual(n2.ui, 4444)
        self.assertEqual((n3 := nodes['node3']).type, NodeTypeEnum.V2.value)
        self.assertEqual(n3.host, 'myhost3')
        self.assertEqual(n3.repository, 55555)
