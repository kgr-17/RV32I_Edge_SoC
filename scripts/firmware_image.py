"""Small strict ELF32 reader and little-endian ROM formatter; no tool dependency."""
import struct

ROM_SIZE = 65536


def parse_elf(data):
    if len(data) < 52:
        raise ValueError('Short ELF header')
    h = struct.unpack_from('<16sHHIIIIIHHHHHH', data)
    ident, kind, machine, version, entry, phoff, shoff, flags, ehsize, phsize, phnum, shsize, shnum, shstr = h
    if (ident[:7] != b'\x7fELF\x01\x01\x01' or kind != 2 or machine != 243 or
            version != 1 or entry != 0 or flags != 0 or ehsize != 52 or phsize != 32 or
            not phnum or phoff + phsize * phnum > len(data) or shsize != 40 or
            not shnum or shoff + shsize * shnum > len(data) or shstr >= shnum):
        raise ValueError('Unexpected ELF class/target/entry/flags/table bounds')
    image = bytearray(ROM_SIZE)
    occupied = set()
    segments = []
    for index in range(phnum):
        typ, offset, vma, lma, size, memsize, permission, alignment = struct.unpack_from('<8I', data, phoff + index * phsize)
        if typ != 1:
            continue
        if size > memsize or offset + size > len(data) or lma + size > ROM_SIZE:
            raise ValueError('Load segment outside file/ROM')
        if permission == 5:
            if not 0 <= vma < ROM_SIZE or vma != lma or vma + memsize > ROM_SIZE:
                raise ValueError('Executable segment outside ROM')
        elif permission == 6:
            if not 0x10000 <= vma < 0x20000 or vma + memsize > 0x1f000:
                raise ValueError('Writable segment outside RAM/stack boundary')
        else:
            raise ValueError('Unexpected segment permissions')
        addresses = set(range(lma, lma + size))
        if occupied & addresses:
            raise ValueError('Overlapping load segments')
        occupied.update(addresses)
        image[lma:lma + size] = data[offset:offset + size]
        segments.append(dict(vma=vma,lma=lma,size=size,memsize=memsize,flags=permission))
    if len(segments) != 2 or {s['flags'] for s in segments} != {5,6}:
        raise ValueError('Expected ROM and RAM load segments')
    sections = [struct.unpack_from('<10I', data, shoff + i * shsize) for i in range(shnum)]
    symbols = {}
    for section in sections:
        _, typ, _, _, offset, size, link, _, _, entsize = section
        if typ != 2:
            continue
        if entsize != 16 or size % 16 or offset + size > len(data) or link >= shnum:
            raise ValueError('Invalid symbol table')
        strings = sections[link]
        if strings[1] != 3 or strings[4] + strings[5] > len(data):
            raise ValueError('Invalid symbol strings')
        table = data[strings[4]:strings[4] + strings[5]]
        for pos in range(offset, offset + size, 16):
            name, value, _, _, _, _ = struct.unpack_from('<IIIBBH', data, pos)
            if name >= len(table):
                raise ValueError('Symbol string outside table')
            end = table.find(b'\0', name)
            if end < 0:
                raise ValueError('Unterminated symbol')
            if name:
                symbols[table[name:end].decode('ascii')] = value
    required={'_start','main','halt_ecall','__data_load','__data_start','__data_end','__bss_start','__bss_end','__stack_top','__stack_bottom','initial_data','zero_area','signature'}
    if not required <= set(symbols) or symbols['_start'] != 0 or symbols['__stack_top'] != 0x20000 or symbols['__stack_bottom'] != 0x1f000:
        raise ValueError('Missing/incorrect boot symbols')
    return bytes(image), segments, symbols


def words(raw):
    if len(raw) != ROM_SIZE:
        raise ValueError('ROM must be exactly64KiB')
    return ''.join('%08x\n' % int.from_bytes(raw[i:i+4], 'little') for i in range(0,len(raw),4))
