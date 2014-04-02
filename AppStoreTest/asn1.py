#
# This file is part of Python-ASN1. Python-ASN1 is free software that is
# made available under the MIT license. 
#
# Copyright (c) 2007 the Python-ASN1 authors.
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
# Python-ASN1 is copyright (c) 2007-2008 by the following people who have 
# contributed to Python-ASN1. Collectively they own the copyright of this software.
# * Geert Jansen <geert@boskant.nl>: original implementation
#

Boolean = 0x01
Integer = 0x02
OctetString = 0x04
Null = 0x05
ObjectIdentifier = 0x06
Enumerated = 0x0a
Sequence = 0x10
Set = 0x11

TypeConstructed = 0x20
TypePrimitive = 0x00

ClassUniversal = 0x00
ClassApplication = 0x40
ClassContext = 0x80
ClassPrivate = 0xc0

import re


class Error(Exception):
    """ASN1 error"""


class Encoder(object):
    """A ASN.1 encoder. Uses DER encoding."""

    def __init__(self):
        """Constructor."""
        self.m_stack = None

    def start(self):
        """Start encoding."""
        self.m_stack = [[]]

    def enter(self, nr, cls=None):
        """Start a constructed data value."""
        if self.m_stack is None:
            raise Error, 'Encoder not initialized. Call start() first.'
        if cls is None:
            cls = ClassUniversal
        self._emit_tag(nr, TypeConstructed, cls)
        self.m_stack.append([])

    def leave(self):
        """Finish a constructed data value."""
        if self.m_stack is None:
            raise Error, 'Encoder not initialized. Call start() first.'
        if len(self.m_stack) == 1:
            raise Error, 'Tag stack is empty.'
        value = ''.join(self.m_stack[-1])
        del self.m_stack[-1]
        self._emit_length(len(value))
        self._emit(value)

    def write(self, value, nr=None, typ=None, cls=None):
        """Write a primitive data value."""
        if self.m_stack is None:
            raise Error, 'Encoder not initialized. Call start() first.'
        if nr is None:
            if isinstance(value, int) or isinstance(value, long):
                nr = Integer
            elif isinstance(value, str) or isinstance(value, unicode):
                nr = OctetString
            elif value is None:
                nr = Null
        if typ is None:
            typ = TypePrimitive
        if cls is None:
            cls = ClassUniversal
        value = self._encode_value(nr, value)
        self._emit_tag(nr, typ, cls)
        self._emit_length(len(value))
        self._emit(value)

    def output(self):
        """Return the encoded output."""
        if self.m_stack is None:
            raise Error, 'Encoder not initialized. Call start() first.'
        if len(self.m_stack) != 1:
            raise Error, 'Stack is not empty.'
        output = ''.join(self.m_stack[0])
        return output

    def _emit_tag(self, nr, typ, cls):
        """Emit a tag."""
        if nr < 31:
            self._emit_tag_short(nr, typ, cls)
        else:
            self._emit_tag_long(nr, typ, cls)

    def _emit_tag_short(self, nr, typ, cls):
        """Emit a short (< 31 bytes) tag."""
        assert nr < 31
        self._emit(chr(nr | typ | cls))

    def _emit_tag_long(self, nr, typ, cls):
        """Emit a long (>= 31 bytes) tag."""
        head = chr(typ | cls | 0x1f)
        self._emit(head)
        values = []
        values.append((nr & 0x7f))
        nr >>= 7
        while nr:
            values.append((nr & 0x7f) | 0x80)
            nr >>= 7
        values.reverse()
        values = map(chr, values)
        for val in values:
            self._emit(val)

    def _emit_length(self, length):
        """Emit length octects."""
        if length < 128:
            self._emit_length_short(length)
        else:
            self._emit_length_long(length)

    def _emit_length_short(self, length):
        """Emit the short length form (< 128 octets)."""
        assert length < 128
        self._emit(chr(length))

    def _emit_length_long(self, length):
        """Emit the long length form (>= 128 octets)."""
        values = []
        while length:
            values.append(length & 0xff)
            length >>= 8
        values.reverse()
        values = map(chr, values)
        # really for correctness as this should not happen anytime soon
        assert len(values) < 127
        head = chr(0x80 | len(values))
        self._emit(head)
        for val in values:
            self._emit(val)

    def _emit(self, s):
        """Emit raw bytes."""
        assert isinstance(s, str)
        self.m_stack[-1].append(s)

    def _encode_value(self, nr, value):
        """Encode a value."""
        if nr in (Integer, Enumerated):
            value = self._encode_integer(value)
        elif nr == OctetString:
            value = self._encode_octet_string(value)
        elif nr == Boolean:
            value = self._encode_boolean(value)
        elif nr == Null:
            value = self._encode_null()
        elif nr == ObjectIdentifier:
            value = self._encode_object_identifier(value)
        return value

    def _encode_boolean(self, value):
        """Encode a boolean."""
        return value and '\xff' or '\x00'

    def _encode_integer(self, value):
        """Encode an integer."""
        if value < 0:
            value = -value
            negative = True
            limit = 0x80
        else:
            negative = False
            limit = 0x7f
        values = []
        while value > limit:
            values.append(value & 0xff)
            value >>= 8
        values.append(value & 0xff)
        if negative:
            # create two's complement
            for i in range(len(values)):
                values[i] = 0xff - values[i]
            for i in range(len(values)):
                values[i] += 1
                if values[i] <= 0xff:
                    break
                assert i != len(values)-1
                values[i] = 0x00
        values.reverse()
        values = map(chr, values)
        return ''.join(values)

    def _encode_octet_string(self, value):
        """Encode an octetstring."""
        # Use the primitive encoding
        return value 

    def _encode_null(self):
        """Encode a Null value."""
        return ''

    _re_oid = re.compile('^[0-9]+(\.[0-9]+)+$')

    def _encode_object_identifier(self, oid):
        """Encode an object identifier."""
        if not self._re_oid.match(oid):
            raise Error, 'Illegal object identifier'
        cmps = map(int, oid.split('.'))
        if cmps[0] > 39 or cmps[1] > 39:
            raise Error, 'Illegal object identifier'
        cmps = [40 * cmps[0] + cmps[1]] + cmps[2:]
        cmps.reverse()
        result = []
        for cmp in cmps:
            result.append(cmp & 0x7f)
            while cmp > 0x7f:
                cmp >>= 7
                result.append(0x80 | (cmp & 0x7f))
        result.reverse()
        result = map(chr, result)
        return ''.join(result)


class Decoder(object):
    """A ASN.1 decoder. Understands BER (and DER which is a subset)."""

    def __init__(self):
        """Constructor."""
        self.m_stack = None
        self.m_tag = None

    def start(self, data):
        """Start processing `data'."""
        if not isinstance(data, str):
            raise Error, 'Expecting string instance.'
        self.m_stack = [[0, data]]
        self.m_tag = None

    def peek(self):
        """Return the value of the next tag without moving to the next
        TLV record."""
        if self.m_stack is None:
            raise Error, 'No input selected. Call start() first.'
        if self._end_of_input():
            return None
        if self.m_tag is None:
            self.m_tag = self._read_tag()
        return self.m_tag

    def read(self):
        """Read a simple value and move to the next TLV record."""
        if self.m_stack is None:
            raise Error, 'No input selected. Call start() first.'
        if self._end_of_input():
            return None
        tag = self.peek()
        length = self._read_length()
        value = self._read_value(tag[0], length)
        self.m_tag = None
        return (tag, value)

    def eof(self):
        """Return True if we are end of input."""
        return self._end_of_input()

    def enter(self):
        """Enter a constructed tag."""
        if self.m_stack is None:
            raise Error, 'No input selected. Call start() first.'
        nr, typ, cls = self.peek()
        if typ != TypeConstructed:
            raise Error, 'Cannot enter a non-constructed tag.'
        length = self._read_length()
        bytes = self._read_bytes(length)
        self.m_stack.append([0, bytes])
        self.m_tag = None

    def leave(self):
        """Leave the last entered constructed tag."""
        if self.m_stack is None:
            raise Error, 'No input selected. Call start() first.'
        if len(self.m_stack) == 1:
            raise Error, 'Tag stack is empty.'
        del self.m_stack[-1]
        self.m_tag = None

    def _decode_boolean(self, bytes):
        """Decode a boolean value."""
        if len(bytes) != 1:
            raise Error, 'ASN1 syntax error'
        if bytes[0] == '\x00':
            return False
        return True

    def _read_tag(self):
        """Read a tag from the input."""
        byte = self._read_byte()
        cls = byte & 0xc0
        typ = byte & 0x20
        nr = byte & 0x1f
        if nr == 0x1f:
            nr = 0
            while True:
                byte = self._read_byte()
                nr = (nr << 7) | (byte & 0x7f)
                if not byte & 0x80:
                    break
        return (nr, typ, cls)

    def _read_length(self):
        """Read a length from the input."""
        byte = self._read_byte()
        if byte & 0x80:
            count = byte & 0x7f
            if count == 0x7f:
                raise Error, 'ASN1 syntax error'
            bytes = self._read_bytes(count)
            bytes = [ ord(b) for b in bytes ]
            length = 0L
            for byte in bytes:
                length = (length << 8) | byte
            try:
                length = int(length)
            except OverflowError:
                pass
        else:
            length = byte
        return length

    def _read_value(self, nr, length):
        """Read a value from the input."""
        bytes = self._read_bytes(length)
        if nr == Boolean:
            value = self._decode_boolean(bytes)
        elif nr in (Integer, Enumerated):
            value = self._decode_integer(bytes)
        elif nr == OctetString:
            value = self._decode_octet_string(bytes)
        elif nr == Null:
            value = self._decode_null(bytes)
        elif nr == ObjectIdentifier:
            value = self._decode_object_identifier(bytes)
        else:
            value = bytes
        return value

    def _read_byte(self):
        """Return the next input byte, or raise an error on end-of-input."""
        index, input = self.m_stack[-1]
        try:
            byte = ord(input[index])
        except IndexError:
            raise Error, 'Premature end of input.'
        self.m_stack[-1][0] += 1
        return byte

    def _read_bytes(self, count):
        """Return the next `count' bytes of input. Raise error on
        end-of-input."""
        index, input = self.m_stack[-1]
        bytes = input[index:index+count]
        if len(bytes) != count:
            raise Error, 'Premature end of input.'
        self.m_stack[-1][0] += count
        return bytes

    def _end_of_input(self):
        """Return True if we are at the end of input."""
        index, input = self.m_stack[-1]
        assert not index > len(input)
        return index == len(input)

    def _decode_integer(self, bytes):
        """Decode an integer value."""
        values = [ ord(b) for b in bytes ]
        # check if the integer is normalized
        if len(values) > 1 and \
                (values[0] == 0xff and values[1] & 0x80 or
                 values[0] == 0x00 and not (values[1] & 0x80)):
            raise Error, 'ASN1 syntax error'
        negative = values[0] & 0x80
        if negative:
            # make positive by taking two's complement
            for i in range(len(values)):
                values[i] = 0xff - values[i]
            for i in range(len(values)-1, -1, -1):
                values[i] += 1
                if values[i] <= 0xff:
                    break
                assert i > 0
                values[i] = 0x00
        value = 0L
        for val in values:
            value = (value << 8) |  val
        if negative:
            value = -value
        try:
            value = int(value)
        except OverflowError:
            pass
        return value

    def _decode_octet_string(self, bytes):
        """Decode an octet string."""
        return bytes

    def _decode_null(self, bytes):
        """Decode a Null value."""
        if len(bytes) != 0:
            raise Error, 'ASN1 syntax error'
        return None

    def _decode_object_identifier(self, bytes):
        """Decode an object identifier."""
        result = []
        value = 0
        for i in range(len(bytes)):
            byte = ord(bytes[i])
            if value == 0 and byte == 0x80:
                raise Error, 'ASN1 syntax error'
            value = (value << 7) | (byte & 0x7f)
            if not byte & 0x80:
                result.append(value)
                value = 0
        if len(result) == 0 or result[0] > 1599:
            raise Error, 'ASN1 syntax error'
        result = [result[0] // 40, result[0] % 40] + result[1:]
        result = map(str, result)
        return '.'.join(result)
