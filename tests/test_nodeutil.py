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

from lockss.pybasic.nodeutil import NodeProtocolEnum, NodeSet, NodeSpec, NodeSpec2, NodeTypeEnum, get_node_spec_adapter


class TestNodeUtil(TestCase):

    def test_compact_node_spec(self):
        host = 'myhost'
        def _test_compact_node_spec(proto: Optional[NodeProtocolEnum],
                                    repo_or_ui: Optional[str],
                                    cfg: Optional[str],
                                    pol: Optional[str],
                                    crw: Optional[str],
                                    md: Optional[str],
                                    soa: Optional[str]) -> None:
            hr = f'{f"{proto.value}://" if proto else ""}{host}'
            if repo_or_ui is not None:
                hr = f'{hr}:{repo_or_ui}'
                if cfg is not None:
                    hr = f'{hr}:{cfg}'
                    if pol is not None:
                        hr = f'{hr}:{pol}'
                        if crw is not None:
                            hr = f'{hr}:{crw}'
                            if md is not None:
                                hr = f'{hr}:{md}'
                                if soa is not None:
                                    hr = f'{hr}:{soa}'
            with (self.subTest(hr=hr)):
                required = (repo_or_ui, cfg, pol)
                optional = (crw, md, soa)
                five = (*required[1:], *optional)
                try:
                    if repo_or_ui and ((cfg and pol) or all(x is None for x in five)):
                        # This parses as either v1 or v2
                        spec: NodeSpec = get_node_spec_adapter().validate_python(hr)
                        self.assertEqual(spec.protocol, proto if proto else NodeProtocolEnum.HTTP)
                        self.assertEqual(spec.host, host)
                        self.assertTrue(repo_or_ui)
                        if all(x is None for x in five):
                            # This is v1
                            self.assertEqual(spec.type, NodeTypeEnum.V1.value)
                            self.assertEqual(spec.ui, int(repo_or_ui))
                        else:
                            # This is v2
                            self.assertTrue(cfg)
                            self.assertTrue(pol)
                            self.assertEqual(spec.type, NodeTypeEnum.V2.value)
                            self.assertEqual(spec.repository, int(repo_or_ui))
                            self.assertEqual(spec.configuration, int(cfg))
                            self.assertEqual(spec.poller, int(pol))
                            self.assertEqual(spec.crawler, int(crw) if crw else None)
                            self.assertEqual(spec.metadata, int(md) if md else None)
                            self.assertEqual(spec.soap, int(soa) if soa else None)
                    elif repo_or_ui is None or (repo_or_ui == '' and all(x is None for x in five)):
                        # This parses as v1 but fails
                        with self.assertRaises(ValidationError) as cm:
                            get_node_spec_adapter().validate_python(hr)
                        validation_err: ValidationError = cm.exception
                        self.assertEqual(validation_err.error_count(), 1)
                        cur = validation_err.errors()[0]
                        self.assertEqual(cur['type'], 'missing')
                        self.assertEqual(cur['msg'], f'Field required')
                        self.assertEqual(cur['loc'], ('v1', 'ui'))
                    elif not all (x for x in required):
                        # This parses as v2 but fails
                        with self.assertRaises(ValidationError) as cm:
                            get_node_spec_adapter().validate_python(hr)
                        validation_err: ValidationError = cm.exception
                        j = 0
                        if not repo_or_ui:
                            self.assertGreater(validation_err.error_count(), j)
                            cur = validation_err.errors()[j]
                            self.assertEqual(cur['type'], 'missing')
                            self.assertEqual(cur['msg'], f'Field required')
                            self.assertEqual(cur['loc'], ('v2', 'repository'))
                            j = j + 1
                        if not cfg:
                            self.assertGreater(validation_err.error_count(), j)
                            cur = validation_err.errors()[j]
                            self.assertEqual(cur['type'], 'missing')
                            self.assertEqual(cur['msg'], f'Field required')
                            self.assertEqual(cur['loc'], ('v2', 'configuration'))
                            j = j + 1
                        if not pol:
                            self.assertGreater(validation_err.error_count(), j)
                            cur = validation_err.errors()[j]
                            self.assertEqual(cur['type'], 'missing')
                            self.assertEqual(cur['msg'], f'Field required')
                            self.assertEqual(cur['loc'], ('v2', 'poller'))
                            j = j + 1
                        self.assertEqual(j, sum(0 if x else 1 for x in required))
                    else:
                        self.fail(f'Unexpected case: {hr}')
                except ValueError as value_err:
                    self.fail(f'Unexpected ValueError: {value_err!s}')

        for proto in (None, *(e for e in NodeProtocolEnum)):
            for repo_or_ui in (None, '', '111'):
                if repo_or_ui is None:
                    _test_compact_node_spec(proto, repo_or_ui, None, None, None, None, None)
                else:
                    for cfg in (None, '', '222'):
                        if cfg is None:
                            _test_compact_node_spec(proto, repo_or_ui, cfg, None, None, None, None)
                        else:
                            for pol in (None, '', '333'):
                                if pol is None:
                                    _test_compact_node_spec(proto, repo_or_ui, cfg, pol, None, None, None)
                                else:
                                    for crw in (None, '', '444'):
                                        if crw is None:
                                            _test_compact_node_spec(proto, repo_or_ui, cfg, pol, crw, None, None)
                                        else:
                                            for md in (None, '', '555'):
                                                if md is None:
                                                    _test_compact_node_spec(proto, repo_or_ui, cfg, pol, crw, md, None)
                                                else:
                                                    for soa in (None, '', '666'):
                                                        _test_compact_node_spec(proto, repo_or_ui, cfg, pol, crw, md, soa)

    def test_node_set(self):
        data1 = {
            'kind': 'NodeSet',
            'id': 'mynodeset',
            'name': 'My Node Set',
            'nodes': [
                {
                    'kind': 'NodeSpec',
                    'id': 'node1',
                    'type': 'v1',
                    'host': 'myhost1',
                    'ui': 7777
                },
                'myhost2:7777',
                'myhost3:1111:2222:3333',
                {
                    'kind': 'NodeSpec',
                    'id': 'migrate1',
                    'type': 'v1-v2-migration-pair',
                    'origin': 'migrate1a:7777',
                    'destination': 'migrate1b:1111:2222:3333',
                }
            ]
        }
        ns1 = NodeSet(**data1)
        self.assertEqual(ns1.kind, 'NodeSet')
        self.assertEqual(ns1.id, 'mynodeset')
        self.assertEqual(ns1.name, 'My Node Set')
        self.assertEqual(len(nodes := ns1.nodes), 4)
        self.assertEqual((n1 := nodes[0]).kind, 'NodeSpec')
        self.assertEqual(n1.id, 'node1')
        self.assertEqual(n1.type, NodeTypeEnum.V1.value)
        self.assertEqual(n1.host, 'myhost1')
        self.assertEqual(n1.ui, 7777)
        self.assertEqual((n2 := nodes[1]).type, NodeTypeEnum.V1.value)
        self.assertEqual(n2.id, 'myhost2:7777')
        self.assertEqual(n2.host, 'myhost2')
        self.assertEqual(n2.ui, 7777)
        self.assertEqual((n3 := nodes[2]).type, NodeTypeEnum.V2.value)
        self.assertEqual(n3.id, 'myhost3:1111:2222:3333')
        self.assertEqual(n3.host, 'myhost3')
        self.assertEqual(n3.repository, 1111)
        self.assertEqual(n3.configuration, 2222)
        self.assertEqual(n3.poller, 3333)
        self.assertIsNone(n3.crawler)
        self.assertIsNone(n3.metadata)
        self.assertIsNone(n3.soap)
        self.assertEqual((n4 := nodes[3]).type, NodeTypeEnum.V1_V2_MIGRATION_PAIR.value)
        self.assertEqual(n4.id, 'migrate1')
        self.assertEqual((n4a := n4.origin).type, NodeTypeEnum.V1.value)
        self.assertEqual(n4a.id, 'migrate1a:7777')
        self.assertEqual(n4a.host, 'migrate1a')
        self.assertEqual(n4a.ui, 7777)
        self.assertEqual((n4b := n4.destination).type, NodeTypeEnum.V2.value)
        self.assertEqual(n4b.id, 'migrate1b:1111:2222:3333')
        self.assertEqual(n4b.host, 'migrate1b')
        self.assertEqual(n4b.repository, 1111)
        self.assertEqual(n4b.configuration, 2222)
        self.assertEqual(n4b.poller, 3333)
        self.assertIsNone(n4b.crawler)
        self.assertIsNone(n4b.metadata)
        self.assertIsNone(n4b.soap)
