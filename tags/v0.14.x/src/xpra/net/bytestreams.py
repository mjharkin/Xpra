# This file is part of Xpra.
# Copyright (C) 2011-2013 Antoine Martin <antoine@devloop.org.uk>
# Copyright (C) 2008, 2009, 2010 Nathaniel Smith <njs@pobox.com>
# Xpra is released under the terms of the GNU GPL v2, or, at your option, any
# later version. See the file COPYING for details.

import time
import sys
import os
import errno
import socket

from xpra.log import Logger
log = Logger("network", "protocol")

#on some platforms (ie: OpenBSD), reading and writing from sockets
#raises an IOError but we should continue if the error code is EINTR
#this wrapper takes care of it.
CONTINUE = {errno.EINTR : "EINTR"}
ABORT = {
    errno.ECONNRESET    : "ECONNRESET",
    errno.EPIPE         : "EPIPE"}
continue_wait = 0
if sys.platform.startswith("win"):
    #on win32, we have to deal with a few more odd error codes:
    #(it would be nicer if those were wrapped using errno instead..)
    WSAEWOULDBLOCK = 10035
    CONTINUE[WSAEWOULDBLOCK] = "WSAEWOULDBLOCK"

    #some of these may be redundant or impossible to hit? (does not hurt I think)
    WSAENETDOWN     = 10050
    WSAENETUNREACH  = 10051
    WSAECONNABORTED = 10053         #this one has been seen, see ticket #492
    WSAECONNRESET   = 10054
    WSAENOTCONN     = 10057
    WSAESHUTDOWN    = 10058
    WSAETIMEDOUT    = 10060
    WSAEHOSTUNREACH = 10065
    WSAEDISCON      = 10101
    ABORT.update({
        WSAECONNABORTED     : "WSAECONNABORTED",
        WSAECONNRESET       : "WSAECONNRESET",
        WSAENETDOWN         : "WSAENETDOWN",
        WSAENETUNREACH      : "WSAENETUNREACH",
        WSAENOTCONN         : "WSAENOTCONN",
        WSAESHUTDOWN        : "WSAESHUTDOWN",
        WSAETIMEDOUT        : "WSAETIMEDOUT",
        WSAEHOSTUNREACH     : "WSAEHOSTUNREACH",
        WSAEDISCON          : "WSAEDISCON",
        })

def set_continue_wait(v):
    global continue_wait
    continue_wait = v

def untilConcludes(is_active_cb, f, *a, **kw):
    wait = 0
    while is_active_cb():
        try:
            return f(*a, **kw)
        except socket.timeout, e:
            log("untilConcludes(%s, %s, %s, %s) %s", is_active_cb, f, a, kw, e)
            continue
        except (IOError, OSError), e:
            code = e.args[0]
            can_continue = CONTINUE.get(code)
            if can_continue:
                log("untilConcludes(%s, %s, %s, %s) %s / %s (continue)", is_active_cb, f, a, kw, can_continue, e)
                time.sleep(wait/1000.0)     #wait is in milliseconds, sleep takes seconds
                if wait<continue_wait:
                    wait += 1
                continue
            log("untilConcludes(%s, %s, %s, %s) %s / %s (raised)", is_active_cb, f, a, kw, ABORT.get(code, code), e)
            raise


class Connection(object):
    def __init__(self, target, info):
        if type(target)==tuple:
            target = ":".join([str(x) for x in target])
        self.target = target
        self.info = info
        self.input_bytecount = 0
        self.output_bytecount = 0
        self.filename = None            #only used for unix domain sockets!
        self.active = True
        self.timeout = 0

    def is_active(self):
        return self.active

    def set_active(self, active):
        self.active = active

    def close(self):
        self.set_active(False)

    def untilConcludes(self, *args):
        return untilConcludes(self.is_active, *args)

    def _write(self, *args):
        w = self.untilConcludes(*args)
        self.output_bytecount += w or 0
        return w

    def _read(self, *args):
        r = self.untilConcludes(*args)
        self.input_bytecount += len(r or "")
        return r

    def get_info(self):
        return {
                "type"              : self.info or "",
                "endpoint"          : self.target or "",
                "input.bytecount"   : self.input_bytecount,
                "output.bytecount"  : self.output_bytecount,
                }


# A simple, portable abstraction for a blocking, low-level
# (os.read/os.write-style interface) two-way byte stream:
# client.py relies on self.filename to locate the unix domain
# socket (if it exists)
class TwoFileConnection(Connection):
    def __init__(self, writeable, readable, abort_test=None, target=None, info="", close_cb=None):
        Connection.__init__(self, target, info)
        self._writeable = writeable
        self._readable = readable
        self._abort_test = abort_test
        self._close_cb = close_cb

    def may_abort(self, action):
        """ if abort_test is defined, run it """
        if self._abort_test:
            self._abort_test(action)

    def read(self, n):
        self.may_abort("read")
        return self._read(os.read, self._readable.fileno(), n)

    def write(self, buf):
        self.may_abort("write")
        return self._write(os.write, self._writeable.fileno(), buf)

    def close(self):
        Connection.close(self)
        try:
            self._writeable.close()
            self._readable.close()
        except:
            pass
        if self._close_cb:
            self._close_cb()

    def __repr__(self):
        return "TwoFileConnection(%s)" % str(self.target)


class SocketConnection(Connection):
    def __init__(self, socket, local, remote, target, info):
        Connection.__init__(self, target, info)
        self._socket = socket
        self.local = local
        self.remote = remote
        if type(remote)==str:
            self.filename = remote

    def read(self, n):
        return self._read(self._socket.recv, n)

    def write(self, buf):
        return self._write(self._socket.send, buf)

    def close(self):
        Connection.close(self)
        self._socket.close()

    def __repr__(self):
        if self.remote:
            return "SocketConnection(%s - %s)" % (self.local, self.remote)
        return "SocketConnection(%s)" % self.local
