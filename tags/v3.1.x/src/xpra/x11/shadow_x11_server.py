#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This file is part of Xpra.
# Copyright (C) 2012-2018 Antoine Martin <antoine@xpra.org>
# Xpra is released under the terms of the GNU GPL v2, or, at your option, any
# later version. See the file COPYING for details.

from xpra.x11.x11_server_core import X11ServerCore
from xpra.os_util import monotonic_time, is_Wayland
from xpra.util import envbool, envint, merge_dicts
from xpra.gtk_common.gtk_util import get_xwindow, is_gtk3
from xpra.server.shadow.gtk_shadow_server_base import GTKShadowServerBase
from xpra.server.shadow.gtk_root_window_model import GTKImageCapture
from xpra.server.shadow.shadow_server_base import ShadowServerBase
from xpra.x11.bindings.ximage import XImageBindings     #@UnresolvedImport
from xpra.gtk_common.error import xsync, xlog
from xpra.log import Logger

log = Logger("x11", "shadow")

XImage = XImageBindings()

USE_XSHM = envbool("XPRA_XSHM", True)
POLL_CURSOR = envint("XPRA_POLL_CURSOR", 20)
USE_NVFBC = envbool("XPRA_NVFBC", True)
USE_NVFBC_CUDA = envbool("XPRA_NVFBC_CUDA", True)
if USE_NVFBC:
    try:
        from xpra.codecs.nvfbc.fbc_capture_linux import (        #@UnresolvedImport
            init_module, NvFBC_SysCapture, NvFBC_CUDACapture,
            )
        init_module()
    except Exception:
        log("NvFBC Capture is not available", exc_info=True)
        USE_NVFBC = False


class XImageCapture(object):
    def __init__(self, xwindow):
        self.xshm = None
        self.xwindow = xwindow
        assert USE_XSHM and XImage.has_XShm(), "no XShm support"
        if is_Wayland():
            log.warn("Warning: shadow servers do not support Wayland")
            log.warn(" switch to X11")

    def __repr__(self):
        return "XImageCapture(%#x)" % self.xwindow

    def clean(self):
        self.close_xshm()

    def close_xshm(self):
        xshm = self.xshm
        if self.xshm:
            self.xshm = None
            with xlog:
                xshm.cleanup()

    def _err(self, e, op="capture pixels"):
        if getattr(e, "msg", None)=="BadMatch":
            log("BadMatch - temporary error in %s of window #%x", op, self.xwindow, exc_info=True)
        else:
            log.warn("Warning: failed to %s of window %#x:", self.xwindow)
            log.warn(" %s", e)
        self.close_xshm()

    def refresh(self):
        if self.xshm:
            #discard to ensure we will call XShmGetImage next time around
            self.xshm.discard()
            return True
        try:
            with xsync:
                log("%s.refresh() xshm=%s", self, self.xshm)
                self.xshm = XImage.get_XShmWrapper(self.xwindow)
                self.xshm.setup()
        except Exception as e:
            self.xshm = None
            self._err(e, "xshm setup")
        return True

    def get_image(self, x, y, width, height):
        if self.xshm is None:
            log("no xshm, cannot get image")
            return None
        try:
            start = monotonic_time()
            with xsync:
                log("X11 shadow get_image, xshm=%s", self.xshm)
                image = self.xshm.get_image(self.xwindow, x, y, width, height)
                return image
        except Exception as e:
            self._err(e)
            return None
        finally:
            end = monotonic_time()
            log("X11 shadow captured %s pixels at %i MPixels/s using %s",
                width*height, (width*height/(end-start))//1024//1024, ["GTK", "XSHM"][USE_XSHM])


def setup_capture(window):
    ww, wh = window.get_geometry()[2:4]
    capture = None
    if USE_NVFBC:
        try:
            log("setup_capture(%s) USE_NVFBC_CUDA=%s", window, USE_NVFBC_CUDA)
            if USE_NVFBC_CUDA:
                capture = NvFBC_CUDACapture()
            else:
                capture = NvFBC_SysCapture()
            capture.init_context(ww, wh)
            capture.refresh()
            image = capture.get_image(0, 0, ww, wh)
            assert image, "test capture failed"
        except Exception as e:
            log("get_image() NvFBC test failed", exc_info=True)
            log("not using %s: %s", capture, e)
            capture = None
    if not capture and XImage.has_XShm() and USE_XSHM:
        capture = XImageCapture(get_xwindow(window))
    if not capture:
        capture = GTKImageCapture(window)
    log("setup_capture(%s)=%s", window, capture)
    return capture


#FIXME: warning: this class inherits from ServerBase twice..
#so many calls will happen twice there (__init__ and init)
class ShadowX11Server(GTKShadowServerBase, X11ServerCore):

    def __init__(self):
        GTKShadowServerBase.__init__(self)
        X11ServerCore.__init__(self)
        self.session_type = "shadow"

    def init(self, opts):
        GTKShadowServerBase.init(self, opts)
        #don't call init on X11ServerCore,
        #this would call up to GTKServerBase.init(opts) again:
        X11ServerCore.do_init(self, opts)

    def cleanup(self):
        GTKShadowServerBase.cleanup(self)
        X11ServerCore.cleanup(self)     #@UndefinedVariable


    def setup_capture(self):
        return setup_capture(self.root)


    def last_client_exited(self):
        GTKShadowServerBase.last_client_exited(self)
        X11ServerCore.last_client_exited(self)


    def do_get_cursor_data(self):
        return X11ServerCore.get_cursor_data(self)


    def make_hello(self, source):
        capabilities = X11ServerCore.make_hello(self, source)
        capabilities.update(GTKShadowServerBase.make_hello(self, source))
        capabilities["server_type"] = "Python/gtk2/x11-shadow"
        return capabilities

    def get_info(self, proto, *_args):
        info = X11ServerCore.get_info(self, proto)
        merge_dicts(info, ShadowServerBase.get_info(self, proto))
        info.setdefault("features", {})["shadow"] = True
        info.setdefault("server", {})["type"] = "Python/gtk%i/x11-shadow" % (2+is_gtk3())
        return info

    def do_make_screenshot_packet(self):
        capture = GTKImageCapture(self.root)
        w, h, encoding, rowstride, data = capture.take_screenshot()
        assert encoding=="png"  #use fixed encoding for now
        from xpra.net.compression import Compressed
        return ["screenshot", w, h, encoding, rowstride, Compressed(encoding, data)]


def main(filename):
    from io import BytesIO
    from xpra.os_util import memoryview_to_bytes
    from xpra.gtk_common.gtk_util import get_default_root_window, get_root_size
    root = get_default_root_window()
    capture = setup_capture(root)
    capture.refresh()
    w, h = get_root_size()
    image = capture.get_image(0, 0, w, h)
    from PIL import Image
    fmt = image.get_pixel_format().replace("X", "A")
    pixels = memoryview_to_bytes(image.get_pixels())
    log("converting %i bytes in format %s to RGBA", len(pixels), fmt)
    if len(fmt)==3:
        target = "RGB"
    else:
        target = "RGBA"
    pil_image = Image.frombuffer(target, (w, h), pixels, "raw", fmt, image.get_rowstride())
    if target!="RGB":
        pil_image = pil_image.convert("RGB")
    buf = BytesIO()
    pil_image.save(buf, "png")
    data = buf.getvalue()
    buf.close()
    with open(filename, "wb") as f:
        f.write(data)
    return 0

if __name__ == "__main__":
    import sys
    if len(sys.argv)!=2:
        print("usage: %s filename.png" % sys.argv[0])
        v = 1
    else:
        v = main(sys.argv[1])
    sys.exit(v)
