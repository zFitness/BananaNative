#!/usr/bin/env python3
"""Write an NSO with its segments stored raw: a file dm/tools/nso.py can read without the zbic package (a ZBIC segment needs it).

The device has no zbic, so a module whose text segment is ZBIC (system 22.0.0+) cannot be read there. The rewriter needs the module, and the shader split
reads main for its embedded shaders: this writes the same module with its segments uncompressed, so both can run without zbic.
Usage: nso_unpack.py <in.nso> <out.nso>
"""
import struct, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import nso

HDR = 0x100


def main():
    src, dst = sys.argv[1], sys.argv[2]
    d = Path(src).read_bytes()
    m = nso.load(d, src)
    out = bytearray(HDR)
    struct.pack_into('<4s', out, 0, b'NSO0')
    struct.pack_into('<I', out, 0xc, 0)          # flags: no segment is compressed
    struct.pack_into('<I', out, 0x3c, m.bss)
    out[0x40:0x60] = m.build_id
    off = HDR
    for i, (mo, sz) in enumerate(m.segments):
        struct.pack_into('<III', out, 0x10 + i * 0x10, off, mo, sz)
        out += m.image[mo:mo + sz]
        off += sz
    Path(dst).write_bytes(bytes(out))
    print(f'{src}: {len(d):,} bytes -> {dst}: {len(out):,} bytes (text {m.segments[0][1]:,}, ro {m.segments[1][1]:,}, data {m.segments[2][1]:,}, bss {m.bss:,})')


if __name__ == '__main__':
    main()
