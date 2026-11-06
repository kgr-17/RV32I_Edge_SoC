#!/usr/bin/env python3
"""Independent ELF corruption and byte-addressed memory expectation tests."""
import struct
import sys
import unittest
import harness
from firmware_image import parse_elf,words
sys.path.insert(0,str(harness.inside('dv/firmware')))
import memory_model


def elf_fixture():
    symbols={'_start':0,'main':0,'halt_ecall':0,'__data_load':4,'__data_start':65536,'__data_end':65544,
        '__bss_start':65544,'__bss_end':65556,'__stack_top':131072,'__stack_bottom':126976,
        'initial_data':65536,'zero_area':65544,'signature':65552}
    strings=bytearray(b'\0');entries=bytearray()
    for name,value in symbols.items():
        offset=len(strings);strings.extend(name.encode()+b'\0')
        entries.extend(struct.pack('<IIIBBH',offset,value,0,0,0,0))
    data=bytearray(0x678)
    struct.pack_into('<16sHHIIIIIHHHHHH',data,0,b'\x7fELF\x01\x01\x01'+bytes(9),2,243,1,0,52,0x600,0,52,32,2,40,3,0)
    struct.pack_into('<8I',data,52,1,0x100,0,0,4,4,5,4)
    struct.pack_into('<8I',data,84,1,0x104,65536,4,8,20,6,4)
    data[0x100:0x10c]=b'\x73\x00\x00\x00'+struct.pack('<II',0xcafebabe,0x13579bdf)
    data[0x200:0x200+len(entries)]=entries;data[0x400:0x400+len(strings)]=strings
    struct.pack_into('<10I',data,0x628,0,2,0,0,0x200,len(entries),2,0,4,16)
    struct.pack_into('<10I',data,0x650,0,3,0,0,0x400,len(strings),0,0,1,0)
    return data


class FirmwareTests(unittest.TestCase):
    def test_independent_elf_lma_and_little_endian_word_image(self):
        raw,segments,symbols=parse_elf(elf_fixture())
        self.assertEqual(len(raw),65536);self.assertEqual(raw[:12],struct.pack('<III',0x73,0xcafebabe,0x13579bdf))
        self.assertEqual(segments[1]['vma'],65536);self.assertEqual(segments[1]['lma'],4)
        self.assertEqual(symbols['signature'],65552)
        self.assertEqual(words(raw).splitlines()[:3],['00000073','cafebabe','13579bdf'])
        self.assertEqual(len(words(raw).splitlines()),16384)

    def test_wrong_class_machine_entry_flags_and_short_tables_rejected(self):
        for offset,fmt,value in [(4,'B',2),(18,'H',62),(24,'I',4),(36,'I',1),(44,'H',0),(32,'I',65535)]:
            data=elf_fixture();struct.pack_into('<'+fmt,data,offset,value)
            with self.assertRaises(ValueError):parse_elf(data)
        for data in (b'',elf_fixture()[:51]):
            with self.assertRaises(ValueError):parse_elf(data)

    def test_outside_rom_ram_overlap_and_permissions_rejected(self):
        for offset,value in [(96,65535),(96,0),(92,0x1efff),(108,7),(100,65537)]:
            data=elf_fixture();struct.pack_into('<I',data,offset,value)
            with self.assertRaises(ValueError):parse_elf(data)

    def test_bad_symbols_and_image_capacity_rejected(self):
        data=elf_fixture();struct.pack_into('<I',data,0x200,65535)
        with self.assertRaises(ValueError):parse_elf(data)
        for raw in (bytes(65535),bytes(65537)):
            with self.assertRaises(ValueError):words(raw)

    def test_byte_lane_read_first_and_warm_reset_retention(self):
        base=(0,0,0,0,0,1,0)
        stim=[(1,0,0,0,0,1,0,15,0xffffffff),(*base,15,0x11223344),(*base,2,0xaabbccdd),(*base,0,0),
              (1,0,0,0,0,1,0,15,0xffffffff),(*base,0,0)]
        rows=memory_model.expected(stim,[0]*16384)
        self.assertEqual([r[13] for r in rows],[0,0,0x11223344,0x1122cc44,0,0x1122cc44])
        self.assertEqual([r[-1] for r in rows],[0,1,1,1,0,1])

    def test_rom_two_ports_independent_enable_and_holds(self):
        rows=memory_model.expected([(1,1,0,1,0,0,0,0,0),(0,1,3,1,7,0,0,0,0),(0,0,9,1,11,0,0,0,0)],list(range(16384)))
        self.assertEqual(rows[1][11:13],(3,7));self.assertEqual(rows[2][11:13],(3,11))
        self.assertEqual(rows[2][-3:],(0,1,0))

    def test_pattern_addresses_unique_and_stimulus_replay(self):
        self.assertEqual(len(set(memory_model.pattern_words())),16384)
        a=memory_model.stimuli(1);b=memory_model.stimuli(20261104)
        self.assertEqual(a,memory_model.stimuli(1));self.assertNotEqual(a,b)
        self.assertEqual({r[2] for r in a if r[1]},set(range(16384)))
        self.assertEqual({r[4] for r in a if r[3]},set(range(16384)))
        self.assertEqual({r[7] for r in a},set(range(16)))


if __name__=='__main__':unittest.main(verbosity=2)
