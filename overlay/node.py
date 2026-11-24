import asyncio, logging
from .protocol import Frame,Type,ProtocolError,correlate
from .transport import Connection
log=logging.getLogger('node')
class Node:
    def __init__(self,c): self.c=c; self.active=0
    async def handle(self,r,w):
        conn=Connection(r,w,self.c)
        if self.active>=self.c.max_connections:
            log.warning('connection overload'); await conn.close(); return
        self.active+=1
        try:
            for _ in range(self.c.max_frames):
                f=await conn.receive()
                if f is None: log.info('peer disconnected'); return
                if f.type!=Type.PING or f.flags!=0: raise ProtocolError('unsupported request')
                obj=f.object()
                log.info('PING received id=%s',f.request_id.hex())
                await conn.send(Frame.make(Type.PONG,{'node':self.c.name,'echo':obj},f.request_id,1,self.c.version))
                log.info('PONG sent id=%s',f.request_id.hex())
            log.warning('frame quota reached')
        except (ProtocolError,OSError,TimeoutError) as e: log.warning('connection rejected: %s %s',type(e).__name__,e)
        finally: self.active-=1; await conn.close()
    async def start(self):
        server=await asyncio.start_server(self.handle,self.c.host,self.c.port,limit=8192)
        log.info('READY %s:%s',self.c.host,self.c.port); return server
    async def ping(self,port=None):
        r,w=await asyncio.wait_for(asyncio.open_connection(self.c.host,port or self.c.peer_port),self.c.timeout)
        conn=Connection(r,w,self.c)
        try:
            f=Frame.make(Type.PING,{'node':self.c.name},version=self.c.version)
            log.info('PING sent id=%s',f.request_id.hex()); await conn.send(f)
            response=await conn.receive()
            if response is None: raise ProtocolError('missing response')
            obj=correlate(f,response); log.info('PONG received id=%s %s',f.request_id.hex(),obj); return obj
        except (ProtocolError,OSError,TimeoutError) as e: log.warning('RPC failed: %s',e); raise
        finally: await conn.close()
