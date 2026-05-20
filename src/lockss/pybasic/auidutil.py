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
LOCKSS AUID Generator

Port of the AUID generation logic from org.lockss.plugin.PluginManager
and related utility classes in the LOCKSS lockss-core library.
"""

import urllib.parse
from typing import Dict


class InvalidAuidError(ValueError):
    """Raised when an AUID string is malformed or invalid."""
    pass


class AuidGenerator:
    """
    Generator for LOCKSS Archival Unit Identifiers (AUIDs).

    This class provides static methods for generating and parsing AUIDs,
    which uniquely identify archival units in the LOCKSS system.

    AUID Format: pluginKey&auKey
    - pluginKey: Plugin class name with dots replaced by pipes
    - auKey: Canonically encoded definitional parameters

    Example:
        >>> plugin_id = "org.lockss.plugin.simulated.SimulatedPlugin"
        >>> params = {"base_url": "http://example.com/", "year": "2023"}
        >>> auid = AuidGenerator.generate_auid(plugin_id, params)
        >>> print(auid)
        org|lockss|plugin|simulated|SimulatedPlugin&base_url~http%3A%2F%2Fexample%2Ecom%2F&year~2023
    """

    @staticmethod
    def plugin_key_from_id(plugin_id: str) -> str:
        """
        Convert plugin ID to plugin key by replacing dots with pipes.

        Port of PluginManager.pluginKeyFromId()

        Args:
            plugin_id: Plugin class name (e.g., "org.lockss.plugin.simulated.SimulatedPlugin")

        Returns:
            Plugin key (e.g., "org|lockss|plugin|simulated|SimulatedPlugin")

        Example:
            >>> AuidGenerator.plugin_key_from_id("org.lockss.plugin.TestPlugin")
            'org|lockss|plugin|TestPlugin'
        """
        if not plugin_id:
            raise ValueError("plugin_id cannot be empty")
        return plugin_id.replace(".", "|")

    @staticmethod
    def plugin_id_from_key(plugin_key: str) -> str:
        """
        Convert plugin key back to plugin ID by replacing pipes with dots.

        Args:
            plugin_key: Plugin key (e.g., "org|lockss|plugin|simulated|SimulatedPlugin")

        Returns:
            Plugin ID (e.g., "org.lockss.plugin.simulated.SimulatedPlugin")

        Example:
            >>> AuidGenerator.plugin_id_from_key("org|lockss|plugin|TestPlugin")
            'org.lockss.plugin.TestPlugin'
        """
        if not plugin_key:
            raise ValueError("plugin_key cannot be empty")
        return plugin_key.replace("|", ".")

    # Characters that don't need encoding - matches Java PropKeyEncoder exactly
    # See lockss-core PropKeyEncoder.java lines 46-62
    _DONT_NEED_ENCODING = set(
        'abcdefghijklmnopqrstuvwxyz'
        'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        '0123456789'
        ' '  # Space is converted to '+' in encode()
        '-'
        '_'
        '*'
    )

    @staticmethod
    def encode_component(s: str) -> str:
        """
        URL-encode a string component for use in AUID.

        Port of PropKeyEncoder.encode() from lockss-core.

        This method encodes strings using URL encoding with the following rules:
        - Alphanumeric characters (a-z, A-Z, 0-9) are not encoded
        - Hyphens (-), underscores (_), and asterisks (*) are not encoded
        - Spaces are encoded as '+'
        - All other characters (including periods) are percent-encoded with uppercase hex digits

        Note: This differs from standard URL encoding (RFC 3986) which treats
        periods (.) as unreserved. Java's PropKeyEncoder encodes periods.

        Args:
            s: String to encode

        Returns:
            URL-encoded string with spaces as '+' and uppercase hex digits

        Example:
            >>> AuidGenerator.encode_component("http://example.com/")
            'http%3A%2F%2Fexample%2Ecom%2F'
        """
        if not s:
            return ""

        result = []
        # Encode string to UTF-8 bytes, matching Java's OutputStreamWriter behavior
        for char in s:
            if char in AuidGenerator._DONT_NEED_ENCODING:
                if char == ' ':
                    result.append('+')
                else:
                    result.append(char)
            else:
                # Encode character to UTF-8 bytes and percent-encode each byte
                char_bytes = char.encode('utf-8')
                for byte in char_bytes:
                    result.append('%')
                    result.append(format(byte, '02X'))

        return ''.join(result)

    @staticmethod
    def decode_component(s: str) -> str:
        """
        URL-decode a string component from an AUID.

        Args:
            s: URL-encoded string

        Returns:
            Decoded string

        Example:
            >>> AuidGenerator.decode_component('http%3A%2F%2Fexample.com%2F')
            'http://example.com/'
        """
        if not s:
            return ""
        return urllib.parse.unquote_plus(s, errors="strict")

    @staticmethod
    def props_to_canonical_encoded_string(props: Dict[str, str]) -> str:
        """
        Convert properties dictionary to canonical encoded string.

        Port of PropUtil.propsToCanonicalEncodedString() from lockss-core.

        The canonical form is created by:
        1. Sorting keys alphabetically
        2. Encoding each key and value
        3. Joining with '~' between key and value, '&' between pairs

        Args:
            props: Dictionary of AU definitional parameters

        Returns:
            Canonical encoded string (e.g., "key1~val1&key2~val2")

        Example:
            >>> props = {"year": "2023", "base_url": "http://example.com/"}
            >>> AuidGenerator.props_to_canonical_encoded_string(props)
            'base_url~http%3A%2F%2Fexample.com%2F&year~2023'
        """
        if not props:
            return ""

        # Sort keys for canonical ordering (case-sensitive, like Java TreeSet)
        sorted_keys = sorted(props.keys())

        parts = []
        for key in sorted_keys:
            val = props[key]
            if val is None:
                val = ""
            encoded_key = AuidGenerator.encode_component(str(key))
            encoded_val = AuidGenerator.encode_component(str(val))
            parts.append(f"{encoded_key}~{encoded_val}")

        return "&".join(parts)

    @staticmethod
    def canonical_encoded_string_to_props(encoded: str) -> Dict[str, str]:
        """
        Decode a canonical encoded string back to properties dictionary.

        Args:
            encoded: Canonical encoded string (e.g., "key1~val1&key2~val2")

        Returns:
            Dictionary of decoded parameters

        Example:
            >>> encoded = 'base_url~http%3A%2F%2Fexample.com%2F&year~2023'
            >>> AuidGenerator.canonical_encoded_string_to_props(encoded)
            {'base_url': 'http://example.com/', 'year': '2023'}
        """
        if not encoded:
            return {}

        props = {}
        pairs = encoded.split("&")

        for pair in pairs:
            if "~" not in pair:
                raise ValueError("Missing tilde in key-value pair")
            key_encoded, val_encoded = pair.split("~", 1)
            if "~" in val_encoded:
                raise ValueError("Additional tilde in key-value pair")
            key = AuidGenerator.decode_component(key_encoded)
            val = AuidGenerator.decode_component(val_encoded)
            props[key] = val

        return props

    @staticmethod
    def generate_auid(plugin_id: str, au_def_props: Dict[str, str]) -> str:
        """
        Generate an AUID from plugin ID and definitional properties.

        Port of PluginManager.generateAuId() from lockss-core.

        Args:
            plugin_id: Plugin class name (e.g., "org.lockss.plugin.simulated.SimulatedPlugin")
            au_def_props: Dictionary of AU definitional parameters

        Returns:
            AUID string (e.g., "org|lockss|plugin|simulated|SimulatedPlugin&base_url~...")

        Raises:
            ValueError: If plugin_id is empty

        Example:
            >>> plugin_id = "org.lockss.plugin.simulated.SimulatedPlugin"
            >>> params = {"base_url": "http://example.com/", "year": "2023"}
            >>> AuidGenerator.generate_auid(plugin_id, params)
            'org|lockss|plugin|simulated|SimulatedPlugin&base_url~http%3A%2F%2Fexample.com%2F&year~2023'
        """
        if not plugin_id:
            raise ValueError("plugin_id cannot be empty")

        plugin_key = AuidGenerator.plugin_key_from_id(plugin_id)
        au_key = AuidGenerator.props_to_canonical_encoded_string(au_def_props)
        return f"{plugin_key}&{au_key}"

    @staticmethod
    def plugin_key_from_auid(auid: str) -> str:
        """
        Extract plugin key from AUID.

        Port of PluginManager.pluginKeyFromAuId() from lockss-core.

        Args:
            auid: AUID string

        Returns:
            Plugin key portion

        Raises:
            InvalidAuidError: If AUID format is invalid

        Example:
            >>> auid = "org|lockss|plugin|TestPlugin&base_url~http%3A%2F%2Fexample.com%2F"
            >>> AuidGenerator.plugin_key_from_auid(auid)
            'org|lockss|plugin|TestPlugin'
        """
        if not auid:
            raise InvalidAuidError("AUID cannot be empty")

        idx = auid.find("&")
        if idx < 0:
            raise InvalidAuidError(f"AUID missing '&' separator: {auid}")

        return auid[:idx]

    @staticmethod
    def au_key_from_auid(auid: str) -> str:
        """
        Extract AU key from AUID.

        Port of PluginManager.auKeyFromAuId() from lockss-core.

        Args:
            auid: AUID string

        Returns:
            AU key portion (may be empty string)

        Raises:
            InvalidAuidError: If AUID format is invalid

        Example:
            >>> auid = "org|lockss|plugin|TestPlugin&base_url~http%3A%2F%2Fexample.com%2F"
            >>> AuidGenerator.au_key_from_auid(auid)
            'base_url~http%3A%2F%2Fexample.com%2F'
        """
        if not auid:
            raise InvalidAuidError("AUID cannot be empty")

        idx = auid.find("&")
        if idx < 0:
            raise InvalidAuidError(f"AUID missing '&' separator: {auid}")

        return auid[idx + 1:]

    @staticmethod
    def plugin_id_from_auid(auid: str) -> str:
        """
        Extract plugin ID from AUID.

        Port of PluginManager.pluginIdFromAuId() from lockss-core.

        Args:
            auid: AUID string

        Returns:
            Plugin ID (with dots restored)

        Raises:
            InvalidAuidError: If AUID format is invalid

        Example:
            >>> auid = "org|lockss|plugin|TestPlugin&base_url~http%3A%2F%2Fexample.com%2F"
            >>> AuidGenerator.plugin_id_from_auid(auid)
            'org.lockss.plugin.TestPlugin'
        """
        plugin_key = AuidGenerator.plugin_key_from_auid(auid)
        return AuidGenerator.plugin_id_from_key(plugin_key)

    @staticmethod
    def decode_auid(auid: str) -> Dict[str, str]:
        """
        Decode an AUID into its definitional parameters.

        This is a convenience method that extracts the AU key and decodes it.

        Args:
            auid: AUID string

        Returns:
            Dictionary of decoded AU parameters

        Raises:
            InvalidAuidError: If AUID format is invalid

        Example:
            >>> auid = "org|lockss|plugin|TestPlugin&base_url~http%3A%2F%2Fexample.com%2F&year~2023"
            >>> AuidGenerator.decode_auid(auid)
            {'base_url': 'http://example.com/', 'year': '2023'}
        """
        au_key = AuidGenerator.au_key_from_auid(auid)
        return AuidGenerator.canonical_encoded_string_to_props(au_key)

    @staticmethod
    def validate_auid(auid: str) -> bool:
        """
        Check if an AUID string is valid.

        Args:
            auid: AUID string to validate

        Returns:
            True if valid, False otherwise

        Example:
            >>> AuidGenerator.validate_auid("org|lockss|plugin|TestPlugin&base_url~http%3A%2F%2Fexample.com%2F")
            True
            >>> AuidGenerator.validate_auid("invalid-auid")
            False
        """
        try:
            AuidGenerator.plugin_key_from_auid(auid)
            AuidGenerator.au_key_from_auid(auid)
            return True
        except (InvalidAuidError, ValueError):
            return False
