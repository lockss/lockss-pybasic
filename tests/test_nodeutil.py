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
import unittest

from pydantic import ValidationError

from lockss.pybasic.nodeutil import LockssNodeModel, LockssNodeProtocolEnum, LockssNodeTypeEnum, DEFAULT_CFG_PORT, DEFAULT_CRW_PORT, DEFAULT_MD_PORT, DEFAULT_POL_PORT, DEFAULT_REPO_PORT, DEFAULT_SOAP_PORT, DEFAULT_UI_PORT_V1


class TestNodeUtil(TestCase):

    def test_node_references(self):
        host = 'myhost'
        def _test_node_reference(proto: str,
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
                mod = LockssNodeModel(host=hr)
                self.assertEqual(mod.protocol, LockssNodeProtocolEnum.HTTP if proto == 'http://' else LockssNodeProtocolEnum.HTTPS) # else includes proto == ''
                self.assertEqual(mod.host, host)
                if not any(five) and repo == '4444':
                    self.assertEqual(mod.type, LockssNodeTypeEnum.V1)
                    self.assertEqual(mod.ui, int(repo))
                    # Check defaults
                    self.assertEqual(mod.repository, DEFAULT_REPO_PORT)
                    self.assertEqual(mod.configuration, DEFAULT_CFG_PORT)
                    self.assertEqual(mod.poller, DEFAULT_POL_PORT)
                    self.assertEqual(mod.crawler, DEFAULT_CRW_PORT)
                    self.assertEqual(mod.metadata, DEFAULT_MD_PORT)
                    self.assertEqual(mod.soap, DEFAULT_SOAP_PORT)
                else:
                    self.assertEqual(mod.type, LockssNodeTypeEnum.V2)
                    self.assertEqual(mod.repository, int(repo) if repo else DEFAULT_REPO_PORT)
                    self.assertEqual(mod.configuration, 2 if cfg else DEFAULT_CFG_PORT)
                    self.assertEqual(mod.poller, 3 if pol else DEFAULT_POL_PORT)
                    self.assertEqual(mod.crawler, 4 if crw else DEFAULT_CRW_PORT)
                    self.assertEqual(mod.metadata, 5 if md else DEFAULT_MD_PORT)
                    self.assertEqual(mod.soap, 6 if soa else DEFAULT_SOAP_PORT)
                    # Check defaults
                    self.assertEqual(mod.ui, DEFAULT_UI_PORT_V1)
            except ValidationError as ve:
                if hr.endswith(':'):
                    self.assertEqual(ve.error_count(), 1)
                    self.assertEqual((e0 := ve.errors()[0])['type'], 'value_error')
                    self.assertIsInstance(valerr := e0['ctx']['error'], ValueError)
                    self.assertEqual(valerr.args, (f'Invalid node reference: {hr}',))
                elif repo == '333' and not any(five):
                    self.assertEqual(ve.error_count(), 1)
                    self.assertEqual((e0 := ve.errors()[0])['type'], 'value_error')
                    self.assertIsInstance(valerr := e0['ctx']['error'], ValueError)
                    self.assertEqual(valerr.args, (f'Invalid repository/UI port in node reference: {repo}',))
                else:
                    raise ValueError(hr) from ve

        for proto in ('', *(f'{p.value}://' for p in LockssNodeProtocolEnum)):
            for repo in (None, '', '333', '4444', '55555'):
                if repo is None:
                    _test_node_reference(proto, repo, None, None, None, None, None)
                else:
                    for cfg in (None, False, True):
                        if cfg is None:
                            _test_node_reference(proto, repo, cfg, None, None, None, None)
                        else:
                            for pol in (None, False, True):
                                if pol is None:
                                    _test_node_reference(proto, repo, cfg, pol, None, None, None)
                                else:
                                    for crw in (None, False, True):
                                        if crw is None:
                                            _test_node_reference(proto, repo, cfg, pol, crw, None, None)
                                        else:
                                            for md in (None, False, True):
                                                if md is None:
                                                    _test_node_reference(proto, repo, cfg, pol, crw, md, None)
                                                else:
                                                    for soa in (None, False, True):
                                                        _test_node_reference(proto, repo, cfg, pol, crw, md, soa)

if __name__ == "__main__":
    unittest.main()
