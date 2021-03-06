# -*- coding: utf-8 -*-
'''
Listener worker process
'''
from __future__ import absolute_import

# Import pythond stdlib
import os
import time
import logging
import threading

# Import third party libs
import zmq
import umsgpack
import nacl.utils
import nacl.secret

# Import napalm-logs pkgs
from napalm_logs.config import PUB_IPC_URL
from napalm_logs.proc import NapalmLogsProc
from napalm_logs.transport import get_transport

log = logging.getLogger(__name__)


class NapalmLogsPublisherProc(NapalmLogsProc):
    '''
    publisher sub-process class.
    '''
    def __init__(self,
                 address,
                 port,
                 transport_type,
                 private_key,
                 signing_key,
                 disable_security=False):
        self.__up = False
        self.address = address
        self.port = port
        self.disable_security = disable_security
        self._transport_type = transport_type
        if not disable_security:
            self.__safe = nacl.secret.SecretBox(private_key)
            self.__signing_key = signing_key
        self._setup_transport()

    def _setup_ipc(self):
        '''
        Subscribe to the pub IPC
        and publish the messages
        on the right transport.
        '''
        ctx = zmq.Context()
        self.sub = ctx.socket(zmq.SUB)
        self.sub.bind(PUB_IPC_URL)
        self.sub.setsockopt(zmq.SUBSCRIBE, '')

    def _setup_transport(self):
        '''
        Setup the transport.
        '''
        transport_class = get_transport(self._transport_type)
        self.transport = transport_class(self.address,
                                         self.port)

    def _prepare(self, obj):
        '''
        Prepare the object to be sent over the untrusted channel.
        '''
        # generating a nonce
        nonce = nacl.utils.random(nacl.secret.SecretBox.NONCE_SIZE)
        # encrypting using the nonce
        encrypted = self.__safe.encrypt(obj, nonce)
        # sign the message
        signed = self.__signing_key.sign(encrypted)
        return signed

    def start(self):
        '''
        Listen to messages and publish them.
        '''
        self._setup_ipc()
        # Start suicide polling thread
        thread = threading.Thread(target=self._suicide_when_without_parent, args=(os.getppid(),))
        thread.start()
        self.transport.start()
        self.__up = True
        while self.__up:
            bin_obj = self.sub.recv()  # already serialized
            if not self.disable_security:
                bin_obj = self._prepare(bin_obj)
            self.transport.publish(bin_obj)

    def stop(self):
        self.__up = False
        self.sub.close()
