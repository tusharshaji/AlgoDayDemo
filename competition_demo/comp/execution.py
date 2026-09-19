"""Run contestant code separately from trusted market data and accounting.

The child receives only visible history and returns bounded JSON position
messages. This is a data/protocol boundary, not an OS file/network sandbox.
"""
from __future__ import annotations

import json
import struct
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
from pathlib import Path

import numpy as np

from . import config as C

MAX_RESPONSE_BYTES = 65536


def run_strategy(strategy, close, volume, sectors, *, start=None, end=None,
                 collect_book=False, time_limit=C.MAX_SECONDS_PER_BACKTEST, seed=0):
    """Keep all future prices, limits, P&L and metrics in this parent process.

    A cumulative deadline covers startup, imports, requests and responses.
    No Python objects received from the child are unpickled or executed.
    """
    from .evaluator import run_backtest, validate_market
    if not np.isfinite(time_limit) or time_limit <= 0:
        raise ValueError("time_limit must be finite and positive")
    close, volume, sectors = validate_market(close, volume, sectors)
    strategy = str(Path(strategy).resolve(strict=True))
    started = time.perf_counter()
    deadline = started + time_limit
    process = subprocess.Popen(
        [sys.executable, '-u', str(Path(__file__).with_name('_strategy_worker.py')),
         strategy, str(seed)], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    io = ThreadPoolExecutor(max_workers=1)

    def exchange(packet=None):
        if packet is not None:
            process.stdin.write(packet)
            process.stdin.flush()
        line = process.stdout.readline(MAX_RESPONSE_BYTES + 1)
        if not line:
            raise RuntimeError("strategy process exited without a response")
        if len(line) > MAX_RESPONSE_BYTES or not line.endswith(b'\n'):
            raise RuntimeError("strategy response exceeds the size limit")
        try:
            message = json.loads(line)
        except (ValueError, UnicodeError):
            raise RuntimeError("strategy returned malformed JSON") from None
        if not isinstance(message, dict):
            raise RuntimeError("strategy response must be a JSON object")
        if 'error' in message:
            raise RuntimeError(str(message['error'])[:4096])
        return message

    def request(packet=None):
        remaining = deadline - time.perf_counter()
        if remaining <= 0:
            raise TimeoutError(f"strategy exceeded {time_limit:g}s wall-clock deadline")
        try:
            return io.submit(exchange, packet).result(timeout=remaining)
        except FutureTimeout:
            raise TimeoutError(f"strategy exceeded {time_limit:g}s wall-clock deadline") from None
        except (BrokenPipeError, OSError) as exc:
            raise RuntimeError(f"strategy communication failed: {exc}") from None

    sent_rows = 0

    def positions(ctx):
        nonlocal sent_rows
        # Send only new visible rows. There is never a future row in a packet.
        rows = len(ctx.close) - sent_rows
        header = struct.pack('<III', ctx.day, ctx.n_inst, rows)
        payload = b''.join((header,
            np.asarray(ctx.close[sent_rows:], dtype='<f8').tobytes(),
            np.asarray(ctx.volume[sent_rows:], dtype='<f8').tobytes(),
            np.asarray(ctx.positions, dtype='<f8').tobytes(),
            np.asarray(ctx.sectors, dtype='<i8').tobytes()))
        message = request(struct.pack('<I', len(payload)) + payload)
        raw = message.get('positions')
        if (set(message) != {'positions'} or not isinstance(raw, list)
                or len(raw) != ctx.n_inst
                or any(type(x) not in (int, float) for x in raw)):
            raise RuntimeError(f"strategy must return {ctx.n_inst} numeric positions")
        sent_rows = len(ctx.close)
        return np.asarray(raw, dtype=float)

    try:
        if request() != {'ready': True}:
            raise RuntimeError("invalid strategy startup response")
        result = run_backtest(positions, close, volume, sectors, start=start,
                              end=end, collect_book=collect_book, time_limit=time_limit)
        if time.perf_counter() > deadline:
            raise TimeoutError(f"strategy exceeded {time_limit:g}s wall-clock deadline")
        result['wall_elapsed'] = time.perf_counter() - started
        return result
    finally:
        # Kill before joining the I/O thread: a partial response cannot evade
        # the deadline by leaving readline blocked on an unfinished message.
        if process.poll() is None:
            process.terminate()
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=2)
        io.shutdown(wait=True, cancel_futures=True)
        process.stdin.close()
        process.stdout.close()
