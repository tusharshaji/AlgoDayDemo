"""Private-to-the-process strategy host. Never receives complete future data."""
import json
import os
from pathlib import Path
import random
import struct
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from comp.evaluator import Context, load_strategy


def main():
    source, output = sys.stdin.buffer, sys.stdout.buffer
    # Ordinary strategy print() calls must not corrupt the protocol.
    sys.stdout = sys.stderr = open(os.devnull, 'w')

    def reply(value):
        output.write(json.dumps(value, separators=(',', ':')).encode() + b'\n')
        output.flush()

    def read_exact(size):
        value = source.read(size)
        if len(value) != size:
            raise EOFError('incomplete context packet')
        return value

    try:
        seed = int(sys.argv[2])
        random.seed(seed)
        np.random.seed(seed)
        fn = load_strategy(sys.argv[1])
        reply({'ready': True})
        close = volume = None
        while True:
            size_bytes = source.read(4)
            if not size_bytes:
                return
            if len(size_bytes) != 4:
                raise ValueError('invalid context header')
            size, = struct.unpack('<I', size_bytes)
            if not 12 <= size <= 64 * 1024 * 1024:
                raise ValueError('invalid context size')
            packet = read_exact(size)
            day, n_inst, rows = struct.unpack_from('<III', packet)
            if size != 12 + (2 * rows * n_inst + 2 * n_inst) * 8:
                raise ValueError('inconsistent context shape')
            offset = 12

            def array(count, dtype):
                nonlocal offset
                result = np.frombuffer(packet, dtype=dtype, count=count, offset=offset).copy()
                offset += count * 8
                return result

            new_close = array(rows * n_inst, '<f8').reshape(rows, n_inst)
            new_volume = array(rows * n_inst, '<f8').reshape(rows, n_inst)
            held = array(n_inst, '<f8')
            sectors = array(n_inst, '<i8')
            close = new_close if close is None else np.vstack([close, new_close])
            volume = new_volume if volume is None else np.vstack([volume, new_volume])
            if len(close) != day + 1:
                raise ValueError('inconsistent history length')
            ctx = Context(close.copy(), volume.copy(), sectors, held, day, n_inst)
            raw = np.asarray(fn(ctx), dtype=float)
            if raw.shape != (n_inst,):
                raise ValueError(f'strategy returned shape {raw.shape}, expected ({n_inst},)')
            reply({'positions': raw.tolist()})
    except BaseException as exc:
        reply({'error': f'{type(exc).__name__}: {exc}'[:4096]})


if __name__ == '__main__':
    main()
