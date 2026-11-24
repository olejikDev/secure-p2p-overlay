import asyncio
import unittest
from dataclasses import replace
from overlay.config import Config
from overlay.node import Node
from overlay.protocol import Frame, Type, ProtocolError, Decoder, HEADER
from overlay.transport import Connection


class ExtendedTests(unittest.IsolatedAsyncioTestCase):
    async def test_wrong_request_id_over_tcp(self):
        c = replace(Config.load('configs/node1.json'), port=0, timeout=1)
        async def wrong(reader, writer):
            conn = Connection(reader, writer, c)
            try:
                request = await conn.receive()
                bad_id = bytes([request.request_id[0] ^ 1]) + request.request_id[1:]
                await conn.send(Frame.make(Type.PONG, {}, bad_id, 1, c.version))
            finally:
                await conn.close()
        server = await asyncio.start_server(wrong, c.host, 0)
        async with server:
            with self.assertLogs('node', level='WARNING') as logs:
                with self.assertRaisesRegex(ProtocolError, 'RPC correlation failed'):
                    await Node(c).ping(server.sockets[0].getsockname()[1])
            self.assertTrue(any('RPC correlation failed' in line for line in logs.output))
            print('NETWORK NEGATIVE:', *logs.output, flush=True)

    async def test_configured_version_and_limit(self):
        c = replace(Config.load('configs/node1.json'), port=0, version=7, MAX_FRAME_PAYLOAD=128, timeout=1)
        node = Node(c)
        server = await node.start()
        async with server:
            port = server.sockets[0].getsockname()[1]
            self.assertEqual((await node.ping(port))['node'], c.name)
            r,w = await asyncio.open_connection(c.host, port)
            try:
                w.write(HEADER.pack(7,1,0,b'x'*16,129)); await w.drain()
                self.assertEqual(await asyncio.wait_for(r.read(), 2), b'')
            finally:
                w.close(); await w.wait_closed()
            self.assertEqual((await node.ping(port))['node'], c.name)

    def test_payload_boundary(self):
        f = Frame(Type.PING, b'x'*16, b'x'*65536)
        self.assertEqual(Decoder().feed(f.encode()), [f])
        d = Decoder()
        with self.assertRaisesRegex(ProtocolError, 'oversized'):
            d.feed(HEADER.pack(1,1,0,b'x'*16,65537) + b'x'*4096)
        self.assertEqual(len(d.body), 0)
