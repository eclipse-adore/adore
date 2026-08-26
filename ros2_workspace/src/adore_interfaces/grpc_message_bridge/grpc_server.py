#!/usr/bin/env python3
"""
Standalone local gRPC server implementing the RosBridge service.
No ROS required. Published messages are fanned out to all active
subscribers on the same topic.

Usage:
    python3 grpc_server.py [--host 0.0.0.0] [--port 50051]
"""
import argparse
import collections
import logging
import queue
import signal
import sys
import threading
from concurrent import futures

import grpc

from grpc_message_bridge import ros_bridge_pb2, ros_bridge_pb2_grpc

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
log = logging.getLogger(__name__)


class RosBridgeServicer(ros_bridge_pb2_grpc.RosBridgeServicer):
    def __init__(self):
        self._lock        = threading.Lock()
        self._subscribers = collections.defaultdict(list)  # topic -> [Queue]

    def Publish(self, request_iterator, context):
        for msg in request_iterator:
            if not context.is_active():
                break
            log.info('publish topic=%s seq=%d', msg.topic, msg.seq)
            with self._lock:
                queues = list(self._subscribers.get(msg.topic, []))
            for q in queues:
                try:
                    q.put_nowait(msg)
                except queue.Full:
                    pass
        return ros_bridge_pb2.Ack(ok=True)

    def Subscribe(self, request, context):
        q = queue.Queue(maxsize=256)
        topic = request.topic
        with self._lock:
            self._subscribers[topic].append(q)
        log.info('subscriber connected topic=%s', topic)
        try:
            while context.is_active():
                try:
                    msg = q.get(timeout=0.1)
                    yield msg
                except queue.Empty:
                    continue
        finally:
            with self._lock:
                subs = self._subscribers.get(topic, [])
                if q in subs:
                    subs.remove(q)
            log.info('subscriber disconnected topic=%s', topic)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default='0.0.0.0')
    parser.add_argument('--port', type=int, default=50051)
    args = parser.parse_args()

    address = f'{args.host}:{args.port}'
    server  = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    ros_bridge_pb2_grpc.add_RosBridgeServicer_to_server(RosBridgeServicer(), server)
    server.add_insecure_port(address)
    server.start()
    log.info('gRPC server listening on %s', address)

    stop = threading.Event()
    signal.signal(signal.SIGINT,  lambda *_: stop.set())
    signal.signal(signal.SIGTERM, lambda *_: stop.set())
    stop.wait()

    log.info('shutting down')
    server.stop(grace=2)


if __name__ == '__main__':
    main()
