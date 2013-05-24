# This file is part of Xpra.
# Copyright (C) 2008 Nathaniel Smith <njs@pobox.com>
# Copyright (C) 2012, 2013 Antoine Martin <antoine@devloop.org.uk>
# Xpra is released under the terms of the GNU GPL v2, or, at your option, any
# later version. See the file COPYING for details.

import os
import zlib

from xpra.log import Logger
log = Logger()

from threading import Lock
from xpra.codecs.xor import xor_str
from xpra.net.mmap_pipe import mmap_read
from xpra.os_util import BytesIOClass

try:
    from xpra.codecs.x264.decoder import Decoder as x264_Decoder     #@UnresolvedImport
except:
    pass
try:
    from xpra.codecs.vpx.decoder import Decoder as vpx_Decoder       #@UnresolvedImport
except:
    pass
#have/use PIL?
has_PIL = False
try:
    import Image
    has_PIL = True
except:
    pass

#logging in the draw path is expensive:
DRAW_DEBUG = os.environ.get("XPRA_DRAW_DEBUG", "0")=="1"


def fire_paint_callbacks(callbacks, success):
    for x in callbacks:
        try:
            x(success)
        except KeyboardInterrupt:
            raise
        except:
            log.error("error calling %s(%s)", x, success, exc_info=True)

"""
Generic superclass for all Backing code,
see CairoBacking and GTKWindowBacking for actual implementations
"""
class WindowBackingBase(object):
    def __init__(self, wid, idle_add):
        self.wid = wid
        self.idle_add = idle_add
        self._has_alpha = False
        self._backing = None
        self._last_pixmap_data = None
        self._video_use_swscale = True
        self._video_decoder = None
        self._video_decoder_lock = Lock()
        self.draw_needs_refresh = True
        self.mmap = None
        self.mmap_enabled = False

    def enable_mmap(self, mmap_area):
        self.mmap = mmap_area
        self.mmap_enabled = True

    def close(self):
        log("%s.close() video_decoder=%s", type(self), self._video_decoder)
        if self._video_decoder:
            try:
                self._video_decoder_lock.acquire()
                self._video_decoder.clean()
                self._video_decoder = None
            finally:
                self._video_decoder_lock.release()


    def jpegimage(self, img_data, width, height):
        """ can be called from any thread """
        assert has_PIL
        buf = BytesIOClass(img_data)
        return Image.open(buf)

    def rgb24image(self, img_data, width, height, rowstride):
        """ can be called from any thread """
        assert has_PIL
        if rowstride>0:
            assert len(img_data) == rowstride * height
        else:
            assert len(img_data) == width * 3 * height
        return Image.fromstring("RGB", (width, height), img_data, 'raw', 'RGB', rowstride, 1)

    def process_delta(self, raw_data, width, height, rowstride, options):
        """
            Can be called from any thread, decompresses and xors the rgb raw_data,
            then stores it for later xoring if needed.
        """
        img_data = raw_data
        if options and options.get("zlib", 0)>0:
            img_data = zlib.decompress(raw_data)
        assert len(img_data) == rowstride * height, "expected %s bytes for %sx%s with rowstride=%s but received %s (%s compressed)" % (rowstride * height, width, height, rowstride, len(img_data), len(raw_data))
        delta = options.get("delta", -1)
        rgb_data = img_data
        if delta>=0:
            if not self._last_pixmap_data:
                raise Exception("delta region references pixmap data we do not have!")
            lwidth, lheight, store, ldata = self._last_pixmap_data
            assert width==lwidth and height==lheight and delta==store
            rgb_data = xor_str(img_data, ldata)
        #store new pixels for next delta:
        store = options.get("store", -1)
        if store>=0:
            self._last_pixmap_data =  width, height, store, rgb_data
        return rgb_data


    def paint_image(self, coding, img_data, x, y, width, height, options, callbacks):
        """ can be called from any thread """
        #log("paint_image(%s, %s bytes, %s, %s, %s, %s, %s, %s)", coding, len(img_data), x, y, width, height, options, callbacks)
        assert has_PIL
        buf = BytesIOClass(img_data)
        img = Image.open(buf)
        assert img.mode in ("L", "P", "RGB", "RGBA"), "invalid image mode: %s" % img.mode
        if img.mode in ("P", "L"):
            #TODO: use RGB for images without transparency
            img = img.convert("RGB")
        raw_data = img.tostring("raw", img.mode)
        if img.mode=="RGB":
            #PIL flattens the data to a continuous straightforward RGB format:
            rowstride = width*3
            img_data = self.process_delta(raw_data, width, height, rowstride, options)
            self.idle_add(self.do_paint_rgb24, img_data, x, y, width, height, rowstride, options, callbacks)
        elif img.mode=="RGBA":
            rowstride = width*4
            img_data = self.process_delta(raw_data, width, height, rowstride, options)
            self.idle_add(self.do_paint_rgb32, img_data, x, y, width, height, rowstride, options, callbacks)
        return False

    def paint_webp(self, img_data, x, y, width, height, options, callbacks):
        """ can be called from any thread """
        from xpra.codecs.webm.decode import DecodeRGB
        rgb24 = DecodeRGB(img_data)
        rowstride = width*3
        self.idle_add(self.do_paint_rgb24, str(rgb24.bitmap), x, y, width, height, rowstride, options, callbacks)
        return  False

    def paint_rgb24(self, raw_data, x, y, width, height, rowstride, options, callbacks):
        """ called from non-UI thread
            this method calls process_delta before calling do_paint_rgb24 from the UI thread via idle_add
        """
        rgb24_data = self.process_delta(raw_data, width, height, rowstride, options)
        self.idle_add(self.do_paint_rgb24, rgb24_data, x, y, width, height, rowstride, options, callbacks)
        return  False

    def do_paint_rgb24(self, img_data, x, y, width, height, rowstride, options, callbacks):
        """ must be called from UI thread
            this method is only here to ensure that we always fire the callbacks,
            the actual paint code is in _do_paint_rgb24
        """
        try:
            success = self._do_paint_rgb24(img_data, x, y, width, height, rowstride, options, callbacks)
            fire_paint_callbacks(callbacks, success)
        except KeyboardInterrupt:
            raise
        except:
            log.error("do_paint_rgb24 error", exc_info=True)
            fire_paint_callbacks(callbacks, False)

    def _do_paint_rgb24(self, img_data, x, y, width, height, rowstride, options, callbacks):
        raise Exception("override me!")


    def paint_rgb32(self, raw_data, x, y, width, height, rowstride, options, callbacks):
        """ called from non-UI thread
            this method calls process_delta before calling do_paint_rgb32 from the UI thread via idle_add
        """
        rgb32_data = self.process_delta(raw_data, width, height, rowstride, options)
        self.idle_add(self.do_paint_rgb32, rgb32_data, x, y, width, height, rowstride, options, callbacks)
        return  False

    def do_paint_rgb32(self, img_data, x, y, width, height, rowstride, options, callbacks):
        """ must be called from UI thread
            this method is only here to ensure that we always fire the callbacks,
            the actual paint code is in _do_paint_rgb32
        """
        try:
            success = self._do_paint_rgb32(img_data, x, y, width, height, rowstride, options, callbacks)
            fire_paint_callbacks(callbacks, success)
        except KeyboardInterrupt:
            raise
        except:
            log.error("do_paint_rgb32 error", exc_info=True)
            fire_paint_callbacks(callbacks, False)

    def _do_paint_rgb32(self, img_data, x, y, width, height, rowstride, options, callbacks):
        raise Exception("override me!")


    def paint_with_video_decoder(self, factory, coding, img_data, x, y, width, height, options, callbacks):
        assert x==0 and y==0
        try:
            self._video_decoder_lock.acquire()
            if self._video_decoder:
                if self._video_decoder.get_type()!=coding:
                    if DRAW_DEBUG:
                        log.info("paint_with_video_decoder: encoding changed from %s to %s", self._video_decoder.get_type(), coding)
                    self._video_decoder.clean()
                    self._video_decoder = None
                elif self._video_decoder.get_width()!=width or self._video_decoder.get_height()!=height:
                    if DRAW_DEBUG:
                        log.info("paint_with_video_decoder: window dimensions have changed from %s to %s", (self._video_decoder.get_width(), self._video_decoder.get_height()), (width, height))
                    self._video_decoder.clean()
                    self._video_decoder.init_context(width, height, self._video_use_swscale, options)
            if self._video_decoder is None:
                if DRAW_DEBUG:
                    log.info("paint_with_video_decoder: new %s(%s,%s,%s)", factory, width, height, options)
                self._video_decoder = factory()
                self._video_decoder.init_context(width, height, self._video_use_swscale, options)
            if DRAW_DEBUG:
                log.info("paint_with_video_decoder: options=%s, decoder=%s", options, type(self._video_decoder))
            self.do_video_paint(coding, img_data, x, y, width, height, options, callbacks)
        finally:
            self._video_decoder_lock.release()
        return  False

    def do_video_paint(self, coding, img_data, x, y, width, height, options, callbacks):
        if DRAW_DEBUG:
            log.info("paint_with_video_decoder: options=%s, decoder=%s", options, type(self._video_decoder))
        err, data, rowstride = self._video_decoder.decompress_image_to_rgb(img_data, options)
        success = err==0 and data is not None and rowstride>0
        if not success:
            raise Exception("paint_with_video_decoder: %s decompression error %s on %s bytes of picture data for %sx%s pixels, options=%s" % (
                      coding, err, len(img_data), width, height, options))
        #this will also take care of firing callbacks (from the UI thread):
        self.idle_add(self.do_paint_rgb24, data, x, y, width, height, rowstride, options, callbacks)

    def paint_mmap(self, img_data, x, y, width, height, rowstride, options, callbacks):
        """ must be called from UI thread """
        #we could run just paint_rgb24 from the UI thread,
        #but this would not make much of a difference
        #and would complicate the code (add a callback to free mmap area)
        """ see _mmap_send() in server.py for details """
        assert self.mmap_enabled
        data = mmap_read(self.mmap, img_data)
        rgb_format = options.get("rgb_format", "rgb24")
        if rgb_format=="RGB":
            self.do_paint_rgb24(data, x, y, width, height, rowstride, options, callbacks)
        elif rgb_format=="RGBA":
            self.do_paint_rgb32(data, x, y, width, height, rowstride, options, callbacks)
        else:
            raise Exception("invalid rgb format: %s" % rgb_format)
        return  False


    def draw_region(self, x, y, width, height, coding, img_data, rowstride, options, callbacks):
        """ dispatches the paint to one of the paint_XXXX methods """
        if DRAW_DEBUG:
            log.info("draw_region(%s, %s, %s, %s, %s, %s bytes, %s, %s, %s)", x, y, width, height, coding, len(img_data), rowstride, options, callbacks)
        if coding == "mmap":
            self.idle_add(self.paint_mmap, img_data, x, y, width, height, rowstride, options, callbacks)
        elif coding == "rgb24":
            if rowstride==0:
                rowstride = width * 3
            self.paint_rgb24(img_data, x, y, width, height, rowstride, options, callbacks)
        elif coding == "rgb32":
            if rowstride==0:
                rowstride = width * 4
            self.paint_rgb32(img_data, x, y, width, height, rowstride, options, callbacks)
        elif coding == "x264":
            self.paint_with_video_decoder(x264_Decoder, "x264", img_data, x, y, width, height, options, callbacks)
        elif coding == "vpx":
            self.paint_with_video_decoder(vpx_Decoder, "vpx", img_data, x, y, width, height, options, callbacks)
        elif coding == "webp":
            self.paint_webp(img_data, x, y, width, height, options, callbacks)
        elif coding.startswith("png") or coding=="jpeg":
            self.paint_image(coding, img_data, x, y, width, height, options, callbacks)
        else:
            raise Exception("invalid encoding: %s" % coding)
