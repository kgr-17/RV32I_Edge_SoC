"""Byte-addressed independent model for registered primitive memory ports."""
import random


def pattern_words():
    return [((index*0x9e3779b1)^0xa5a50000)&0xffffffff for index in range(16384)]


def stimuli(seed):
    rng=random.Random(seed)
    rows=[(1,1,0,1,16383,1,0,15,0xffffffff)]
    for addr in range(16384):rows.append((0,1,addr,1,16383-addr,1,addr,15,((addr+1)*0x10203041^seed)&0xffffffff))
    for addr in range(16384):rows.append((0,int(addr%3!=0),addr,int(addr%5!=0),16383-addr,1,addr,0,0))
    for addr in (0,1,16383):
        for mask in range(16):
            rows.extend([(0,1,addr,1,addr,1,addr,mask,rng.getrandbits(32)),(0,0,0,0,0,1,addr,0,0)])
    for i in range(256):rows.append((int(i%61 in (0,1)),rng.randrange(2),rng.randrange(16384),rng.randrange(2),rng.randrange(16384),rng.randrange(2),rng.randrange(16384),rng.randrange(16),rng.getrandbits(32)))
    rows.append((1,1,0,1,16383,1,0,15,0xffffffff))
    for addr in (0,1,16383):rows.append((0,1,addr,1,16383-addr,1,addr,0,0))
    return rows


def expected(stimulus,boot):
    pattern=pattern_words();ram=bytearray(65536);held=[0]*5;result=[]
    for reset,ae,aa,be,ba,re,ra,mask,data in stimulus:
        if reset:
            held=[0]*5;valid=[0]*3
        else:
            valid=[ae,be,re]
            if ae:held[0]=pattern[aa];held[2]=boot[aa]
            if be:held[1]=pattern[ba];held[3]=boot[ba]
            if re:
                pos=ra*4;held[4]=int.from_bytes(ram[pos:pos+4],'little')
                payload=data.to_bytes(4,'little')
                for lane in range(4):
                    if mask & (1<<lane):ram[pos+lane]=payload[lane]
        result.append((reset,ae,aa,be,ba,re,ra,mask,data,*held,*valid))
    return result


def vectors(seed,boot):
    return ''.join(' '.join('%x'%v for v in row)+'\n' for row in expected(stimuli(seed),boot))
