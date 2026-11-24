import asyncio, logging
from collections import deque
from .protocol import Decoder, ProtocolError
log=logging.getLogger('transport')
class Connection:
    def __init__(self,reader,writer,c):
        self.reader=reader; self.writer=writer; self.c=c; self.decoder=Decoder(c.MAX_FRAME_PAYLOAD,c.version); self.pending=deque()
    async def receive(self):
        async with asyncio.timeout(self.c.timeout):
            while not self.pending:
                data=await self.reader.read(4096)
                if not data:
                    self.decoder.eof(); return None
                self.pending.extend(self.decoder.feed(data))
            return self.pending.popleft()
    async def send(self,frame):
        self.writer.write(frame.encode(self.c.MAX_FRAME_PAYLOAD)); await asyncio.wait_for(self.writer.drain(),self.c.timeout)
    async def close(self):
        self.writer.close()
        try: await asyncio.wait_for(self.writer.wait_closed(),self.c.timeout)
        except (OSError,TimeoutError): pass
