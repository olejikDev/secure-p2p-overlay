import argparse, asyncio, logging
from overlay.config import Config
from overlay.node import Node
async def main():
    p=argparse.ArgumentParser(); p.add_argument('config'); p.add_argument('mode',choices=['serve','ping']); a=p.parse_args()
    node=Node(Config.load(a.config))
    if a.mode=='ping':
        server=await node.start()
        async with server: await node.ping()
    else:
        server=await node.start()
        async with server: await server.serve_forever()
if __name__=='__main__':
    logging.basicConfig(level=logging.INFO,format='%(asctime)s %(levelname)s %(name)s %(message)s')
    try: asyncio.run(main())
    except KeyboardInterrupt: pass
