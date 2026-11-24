import unittest, random, asyncio, struct
from dataclasses import replace
from overlay.protocol import *
from overlay.config import Config
from overlay.node import Node
class ProtocolTests(unittest.TestCase):
    def test_header(self):
        f=Frame.make(Type.PING,{'x':1}); raw=f.encode(); self.assertEqual(HEADER.size,24); self.assertEqual(raw[20:24],struct.pack('!I',len(f.payload))); self.assertEqual(Decoder().feed(raw),[f])
    def test_100(self):
        rng=random.Random(42); frames=[Frame.make(Type.PING,{'x':'a'*rng.randrange(500)}) for _ in range(100)]; raw=b''.join(f.encode() for f in frames); d=Decoder(); out=[]; i=0
        while i<len(raw):
            n=rng.randrange(1,800); out.extend(d.feed(raw[i:i+n])); i+=n
        d.eof(); self.assertEqual(out,frames)
    def test_split_and_glued(self):
        f=Frame.make(Type.PING,{}); raw=f.encode(); d=Decoder(); self.assertEqual(d.feed(raw[:5]),[]); self.assertEqual(d.feed(raw[5:25]),[]); self.assertEqual(d.feed(raw[25:]+raw),[f,f])
    def test_oversize(self):
        d=Decoder(); self.assertRaises(ProtocolError,d.feed,HEADER.pack(1,1,0,b'0'*16,65537)); self.assertEqual(len(d.body),0)
    def test_correlation(self):
        a=Frame.make(Type.PING,{}); b=Frame.make(Type.PONG,{},flags=1); self.assertRaises(ProtocolError,correlate,a,b)
    def test_invalid(self):
        for v,t in [(2,1),(1,255)]: self.assertRaises(ProtocolError,Decoder().feed,HEADER.pack(v,t,0,b'0'*16,0))
        d=Decoder(); d.feed(Frame.make(Type.PING,{}).encode()[:-1]); self.assertRaises(ProtocolError,d.eof)
        self.assertRaises(ProtocolError,Frame(Type.PING,b'0'*16,b'bad').object)
class NetworkTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.c=replace(Config.load('configs/node1.json'),port=0,timeout=.15,max_connections=1); self.node=Node(self.c); self.server=await self.node.start(); self.port=self.server.sockets[0].getsockname()[1]
    async def asyncTearDown(self): self.server.close(); await self.server.wait_closed(); await asyncio.sleep(.02)
    async def test_ping(self): self.assertEqual((await self.node.ping(self.port))['node'],'node1')
    async def test_bad_connections(self):
        for raw in [HEADER.pack(2,1,0,b'0'*16,0),HEADER.pack(1,255,0,b'0'*16,0),HEADER.pack(1,1,0,b'0'*16,65537),Frame(Type.PING,b'0'*16,b'bad').encode(),b'abc']:
            r,w=await asyncio.open_connection('127.0.0.1',self.port); w.write(raw); await w.drain(); w.write_eof(); self.assertEqual(await asyncio.wait_for(r.read(),1),b''); w.close(); await w.wait_closed(); await asyncio.sleep(.01)
        await self.node.ping(self.port)
    async def test_timeout_overload(self):
        r,w=await asyncio.open_connection('127.0.0.1',self.port); await asyncio.sleep(.02)
        r2,w2=await asyncio.open_connection('127.0.0.1',self.port); self.assertEqual(await asyncio.wait_for(r2.read(),1),b''); w2.close(); await w2.wait_closed(); self.assertEqual(await asyncio.wait_for(r.read(),1),b''); w.close(); await w.wait_closed(); await self.node.ping(self.port)
