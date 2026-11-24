import json
from dataclasses import dataclass
@dataclass(frozen=True)
class Config:
    name:str; host:str; port:int; peer_port:int; timeout:float; version:int; MAX_FRAME_PAYLOAD:int; max_connections:int; max_frames:int
    @classmethod
    def load(cls,path):
        with open(path,encoding='utf8') as f: c=cls(**json.load(f))
        if not (0<c.MAX_FRAME_PAYLOAD<=65536 and c.timeout>0 and c.max_connections>0 and c.max_frames>0 and 0<c.version<256): raise ValueError('invalid config')
        return c
