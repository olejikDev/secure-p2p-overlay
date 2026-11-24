"""Run two independent peers using only their configuration files."""
import argparse
import json
import pathlib
import socket
import subprocess
import sys
import time

root = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
from overlay.config import Config


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--node1', default='configs/node1.json')
    parser.add_argument('--node2', default='configs/node2.json')
    args = parser.parse_args()
    paths = [(root / p).resolve() for p in (args.node1, args.node2)]
    a, b = map(Config.load, paths)
    if a.port == b.port or a.peer_port != b.port or b.peer_port != a.port:
        raise ValueError('Configure distinct listening ports and reciprocal peer_port values')
    out = root / 'results'
    out.mkdir(exist_ok=True)
    # Each process listens on its configured port; node2 also initiates RPC.
    with (out / 'node1.log').open('w', encoding='utf8') as log1, (out / 'node2.log').open('w', encoding='utf8') as log2:
        p = subprocess.Popen([sys.executable, 'main.py', str(paths[0]), 'serve'], cwd=root, stdout=log1, stderr=log1)
        try:
            deadline = time.monotonic() + max(5, a.timeout * 3)
            while time.monotonic() < deadline:
                if p.poll() is not None:
                    raise RuntimeError('node1 failed; inspect node1.log')
                if 'READY' in (out / 'node1.log').read_text(encoding='utf8'):
                    break
                time.sleep(.05)
            else:
                raise RuntimeError('startup timeout')
            subprocess.run([sys.executable, 'main.py', str(paths[1]), 'ping'], cwd=root, stdout=log2, stderr=log2, check=True, timeout=max(5, b.timeout * 4))
            with socket.create_connection((a.host, a.port), timeout=a.timeout) as s:
                s.settimeout(a.timeout + max(1, a.timeout))
                if s.recv(1) != b'':
                    raise RuntimeError('idle connection was not closed')
        finally:
            p.terminate()
            try:
                p.wait(timeout=max(5, a.timeout * 2))
            except subprocess.TimeoutExpired:
                p.kill(); p.wait()
    print('Demo OK; results/node1.log, results/node2.log')


if __name__ == '__main__':
    main()
