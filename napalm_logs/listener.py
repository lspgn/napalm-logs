# -*- coding: utf-8 -*-
'''
Listener worker process
'''
from __future__ import absolute_import
from __future__ import unicode_literals

# Import pythond stdlib
import os
import logging
import threading

# Import third party libs
import zmq
import umsgpack

# Import napalm-logs pkgs
from napalm_logs.config import LST_IPC_URL
from napalm_logs.config import BUFFER_SIZE
from napalm_logs.proc import NapalmLogsProc

log = logging.getLogger(__name__)


class NapalmLogsListenerProc(NapalmLogsProc):
    '''
    Listener sub-process class.
    '''
    def __init__(self, socket):
        self.socket = socket
        self.__up = False

    def _setup_ipc(self):
        '''
        Setup the IPC publisher.
        '''
        ctx = zmq.Context()
        self.pub = ctx.socket(zmq.PUB)
        self.pub.connect(LST_IPC_URL)

    def start(self):
        '''
        Listen to messages and queue them.
        '''
        self._setup_ipc()
        # Start suicide polling thread
        thread = threading.Thread(target=self._suicide_when_without_parent, args=(os.getppid(),))
        thread.start()
        self.__up = True
        while self.__up:
            msg, addr = self.socket.recvfrom(BUFFER_SIZE)
            # Addr contains (IP, port), we only care about the IP
            obj = (msg, addr[0])
            bin_obj = umsgpack.packb(obj)
            self.pub.send(bin_obj)

    def stop(self):
        self.__up = False
        self.pub.close()
