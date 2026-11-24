import json, msgpack, time, pathlib, platform
samples=[{'node':'node1','message':'Привет'*i,'sequence':i} for i in range(1,101)]
results={}
for name,encode,decode in [('JSON',lambda x:json.dumps(x,ensure_ascii=False,separators=(',',':')).encode(),json.loads),('MessagePack',lambda x:msgpack.packb(x,use_bin_type=True),lambda x:msgpack.unpackb(x,raw=False))]:
    start=time.perf_counter(); sizes=[]
    for _ in range(100):
        for obj in samples:
            raw=encode(obj); assert decode(raw)==obj; sizes.append(len(raw))
    results[name]={'operations':len(sizes),'mean_bytes':sum(sizes)/len(sizes),'total_seconds':time.perf_counter()-start}
path=pathlib.Path(__file__).resolve().parents[1]/'results'/'benchmark.json'; path.write_text(json.dumps({'python':platform.python_version(),'results':results},indent=2)); print(path.read_text())
