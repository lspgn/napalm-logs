# -*- coding: utf-8 -*-
'''
ZeroMQ transport for napalm-logs.
'''
from __future__ import absolute_import
from __future__ import unicode_literals

# Import stdlib
import json
import logging

# Import third party libs
import zmq

# Import napalm-logs pkgs
from napalm_logs.exceptions import BindException
from napalm_logs.transport.base import TransportBase

log = logging.getLogger(__name__)


class ZMQTransport(TransportBase):
    '''
    ZMQ transport class.
    '''
    def __init__(self, addr, port):
        self.addr = addr
        self.port = port

    def start(self):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PUB)
        try:
            self.socket.bind('tcp://{addr}:{port}'.format(
                addr=self.addr,
                port=self.port)
            )
        except zmq.error.ZMQError as err:
            log.error(err, exc_info=True)
            raise BindException(err)

    def publish(self, obj):
        self.socket.send(obj)

    def stop(self):
        if hasattr(self, 'socket'):
            self.socket.close()
        if hasattr(self, 'context'):
            self.context.term()
