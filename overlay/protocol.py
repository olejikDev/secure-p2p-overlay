import struct, json, uuid
from dataclasses import dataclass
from enum import IntEnum
HEADER = struct.Struct('!BBH16sI')
class Type(IntEnum):
    PING=1; PONG=2; FIND_NODE_REQUEST=3; FIND_NODE_RESPONSE=4; STORE_REQUEST=5; STORE_RESPONSE=6; FIND_VALUE_REQUEST=7; FIND_VALUE_RESPONSE=8; TUNNEL_BUILD=9; TUNNEL_BUILD_OK=10; TUNNEL_BUILD_FAIL=11; TUNNEL_DATA=12; TUNNEL_ACK=13; TUNNEL_CLOSE=14; APP_MESSAGE=15; APP_ACK=16; ERROR=17
class ProtocolError(ValueError): pass
@dataclass(frozen=True)
class Frame:
    type: Type
    request_id: bytes
    payload: bytes
    flags: int=0
    version: int=1
    def encode(self, limit=65536):
        if len(self.payload)>limit or len(self.request_id)!=16: raise ProtocolError('invalid length')
        return HEADER.pack(self.version,self.type,self.flags,self.request_id,len(self.payload))+self.payload
    @classmethod
    def make(cls, kind, obj, request_id=None, flags=0, version=1):
        return cls(kind,request_id or uuid.uuid4().bytes,json.dumps(obj,ensure_ascii=False,allow_nan=False,separators=(',',':')).encode(),flags,version)
    def object(self):
        try:
            obj=json.loads(self.payload.decode(),parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
            if not isinstance(obj,dict): raise ValueError('expected object')
            return obj
        except (ValueError,UnicodeError,RecursionError) as e: raise ProtocolError('invalid JSON') from e
class Decoder:
    def __init__(self,limit=65536,version=1):
        self.limit=limit; self.version=version; self.header=bytearray(); self.body=bytearray(); self.meta=None
    def feed(self,data):
        out=[]; pos=0
        while pos<len(data):
            if self.meta is None:
                n=min(HEADER.size-len(self.header),len(data)-pos); self.header.extend(data[pos:pos+n]); pos+=n
                if len(self.header)<HEADER.size: continue
                v,t,f,r,size=HEADER.unpack(self.header); self.header.clear()
                if size>self.limit: raise ProtocolError('oversized payload')
                if v!=self.version: raise ProtocolError('unknown version')
                try: t=Type(t)
                except ValueError as e: raise ProtocolError('unknown type') from e
                if f & ~7: raise ProtocolError('unknown flags')
                self.meta=(v,t,f,r,size)
            v,t,f,r,size=self.meta
            n=min(size-len(self.body),len(data)-pos); self.body.extend(data[pos:pos+n]); pos+=n
            if len(self.body)==size:
                out.append(Frame(t,r,bytes(self.body),f,v)); self.body.clear(); self.meta=None
        return out
    def eof(self):
        if self.header or self.meta is not None: raise ProtocolError('truncated frame')
def correlate(request,response):
    if response.request_id!=request.request_id or response.type!=Type.PONG or response.flags!=1: raise ProtocolError('RPC correlation failed')
    return response.object()
