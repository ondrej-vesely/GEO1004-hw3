#!/usr/bin/python3

#
#   This file is part of Magnum.
#
#   Copyright © 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019,
#               2020 Vladimír Vondruš <mosra@centrum.cz>
#
#   Permission is hereby granted, free of charge, to any person obtaining a
#   copy of this software and associated documentation files (the "Software"),
#   to deal in the Software without restriction, including without limitation
#   the rights to use, copy, modify, merge, publish, distribute, sublicense,
#   and/or sell copies of the Software, and to permit persons to whom the
#   Software is furnished to do so, subject to the following conditions:
#
#   The above copyright notice and this permission notice shall be included
#   in all copies or substantial portions of the Software.
#
#   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#   IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#   FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
#   THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#   LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#   FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#   DEALINGS IN THE SOFTWARE.
#

# Tables based on Zijp, Fast Half Float Conversions
# ftp://ftp.fox-toolkit.org/pub/fasthalffloatconversion.pdf

def convertmantissa(i):
    m = i << 13
    e = 0
    while not (m & 0x00800000):
        e -= 0x00800000
        m <<= 1
    m &= ~0x00800000
    e += 0x38800000
    return m | e

mantissa_table = [0]*2048
for i in range(1, 1024):
    mantissa_table[i] = convertmantissa(i)
for i in range(1024, 2048):
    mantissa_table[i] = 0x38000000 + ((i - 1024) << 13)

exponent_table = [0]*64
for i in range(1, 31):
    exponent_table[i] = i << 23
exponent_table[31] = 0x47800000
exponent_table[32] = 0x80000000
for i in range(33, 63):
    exponent_table[i] = 0x80000000 + ((i - 32) << 23)
exponent_table[63] = 0xc7800000

offset_table = [1024]*64
offset_table[0] = 0
offset_table[32] = 0

base_table = [0]*512
shift_table = [0]*512

for i in range(0, 256):
    e = i - 127
    if e < -24:
        base_table[i | 0x000] = 0x0000
        base_table[i | 0x100] = 0x8000
        shift_table[i | 0x000] = 24
        shift_table[i | 0x100] = 24
    elif e < -14:
        base_table[i | 0x000] = (0x0400 >> (-e - 14))
        base_table[i | 0x100] = (0x0400 >> (-e - 14)) | 0x8000
        shift_table[i | 0x000] = -e - 1
        shift_table[i | 0x100] = -e - 1
    elif e <= 15:
        base_table[i | 0x000] = ((e + 15) << 10)
        base_table[i | 0x100] = ((e + 15) << 10) | 0x8000;
        shift_table[i | 0x000] = 13
        shift_table[i | 0x100] = 13
    elif e < 128:
        base_table[i | 0x000] = 0x7C00
        base_table[i | 0x100] = 0xFC00
        shift_table[i | 0x000] = 24
        shift_table[i | 0x100] = 24
    else:
        base_table[i | 0x000] = 0x7C00
        base_table[i | 0x100] = 0xFC00
        shift_table[i | 0x000] = 13
        shift_table[i | 0x100] = 13

# Print the stuff
print("""#ifndef Magnum_Math_halfTables_hpp
#define Magnum_Math_halfTables_hpp
/*
    This file is part of Magnum.

    Copyright © 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019,
                2020 Vladimír Vondruš <mosra@centrum.cz>

    Permission is hereby granted, free of charge, to any person obtaining a
    copy of this software and associated documentation files (the "Software"),
    to deal in the Software without restriction, including without limitation
    the rights to use, copy, modify, merge, publish, distribute, sublicense,
    and/or sell copies of the Software, and to permit persons to whom the
    Software is furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included
    in all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
    DEALINGS IN THE SOFTWARE.
*/

#include "Magnum/Types.h"

/* Generated by ./generateHalfTables.py */

namespace Magnum { namespace Math { namespace {
""")

def print32bit(table):
    for i, v in enumerate(table):
        print("0x{:08x}".format(v), end=",\n    " if not (i + 1) % 6 else ", " if not i == len(table) - 1 else "")
def print16bit(table):
    for i, v in enumerate(table):
        print("0x{:04x}".format(v), end=",\n    " if not (i + 1) % 9 else ", " if not i == len(table) - 1 else "")
def print8bit(table):
    for i, v in enumerate(table):
        print("0x{:02x}".format(v), end=",\n    " if not (i + 1) % 12 else ", " if not i == len(table) - 1 else "")

print("constexpr UnsignedInt HalfMantissaTable[2048] = {\n    ", end="")
print32bit(mantissa_table)
print("\n};\n")

print("constexpr UnsignedInt HalfExponentTable[64] = {\n    ", end="")
print32bit(exponent_table)
print("\n};\n")

print("constexpr UnsignedShort HalfOffsetTable[64] = {\n    ", end="")
print16bit(offset_table)
print("\n};\n")

print("constexpr UnsignedShort HalfBaseTable[512] = {\n    ", end="")
print16bit(base_table)
print("\n};\n")

print("constexpr UnsignedByte HalfShiftTable[512] = {\n    ", end="")
print8bit(shift_table)
print("""
};

}}}

#endif
""")
