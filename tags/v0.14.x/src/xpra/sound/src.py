#!/usr/bin/env python
# This file is part of Xpra.
# Copyright (C) 2010-2014 Antoine Martin <antoine@devloop.org.uk>
# Xpra is released under the terms of the GNU GPL v2, or, at your option, any
# later version. See the file COPYING for details.

import sys, os

from xpra.sound.sound_pipeline import SoundPipeline, gobject
from xpra.gtk_common.gobject_util import n_arg_signal
from xpra.sound.pulseaudio_util import has_pa
from xpra.sound.gstreamer_util import plugin_str, get_encoder_formatter, MP3, CODECS, MUXER_DEFAULT_OPTIONS
from xpra.log import Logger
log = Logger("sound")


def normv(v):
    if v==2**64-1:
        return -1
    return v


SOURCES = ["autoaudiosrc"]
if has_pa():
    SOURCES.append("pulsesrc")
if sys.platform.startswith("darwin"):
    SOURCES.append("osxaudiosrc")
elif sys.platform.startswith("win"):
    SOURCES.append("directsoundsrc")
if os.name=="posix":
    SOURCES += ["alsasrc", "jackaudiosrc",
                "osssrc", "oss4src",
                "osxaudiosrc", "jackaudiosrc"]
SOURCES.append("audiotestsrc")


DEFAULT_SRC = os.environ.get("XPRA_SOUND_DEFAULT_SRC", SOURCES[0])
if DEFAULT_SRC not in SOURCES:
    log.error("invalid default sound source: '%s' is not in %s, using %s instead", DEFAULT_SRC, SOURCES, SOURCES[0])
    DEFAULT_SRC = SOURCES[0]


AUDIOCONVERT = True
AUDIORESAMPLE = False


class SoundSource(SoundPipeline):

    __gsignals__ = SoundPipeline.__generic_signals__.copy()
    __gsignals__.update({
        "new-buffer"    : n_arg_signal(2),
        })

    def __init__(self, src_type=DEFAULT_SRC, src_options={}, codec=MP3, volume=1.0, encoder_options={}):
        assert src_type in SOURCES
        encoder, fmt = get_encoder_formatter(codec)
        SoundPipeline.__init__(self, codec)
        self.src_type = src_type
        source_str = plugin_str(src_type, src_options)
        encoder_str = plugin_str(encoder, encoder_options)
        fmt_str = plugin_str(fmt, MUXER_DEFAULT_OPTIONS.get(fmt, {}))
        pipeline_els = [source_str]
        if AUDIOCONVERT:
            pipeline_els += ["audioconvert"]
        if AUDIORESAMPLE:
            pipeline_els += [
                         "audioresample",
                         "audio/x-raw-int,rate=44100,channels=2"]
        pipeline_els.append("volume name=volume volume=%s" % volume)
        pipeline_els += [encoder_str,
                        fmt_str,
                        "appsink name=sink"]
        self.setup_pipeline_and_bus(pipeline_els)
        self.volume = self.pipeline.get_by_name("volume")
        self.sink = self.pipeline.get_by_name("sink")
        self.sink.set_property("emit-signals", True)
        self.sink.set_property("max-buffers", 10)
        self.sink.set_property("drop", False)
        self.sink.set_property("sync", True)
        self.sink.set_property("qos", False)
        try:
            #Gst 1.0:
            self.sink.connect("new-sample", self.on_new_sample)
            self.sink.connect("new-preroll", self.on_new_preroll1)
        except:
            #Gst 0.10:
            self.sink.connect("new-buffer", self.on_new_buffer)
            self.sink.connect("new-preroll", self.on_new_preroll0)

    def set_volume(self, volume=1.0):
        if self.sink and self.volume:
            self.volume.set_property("volume", volume)

    def get_volume(self):
        if self.sink and self.volume:
            return self.volume.get_property("volume")
        return 0

    def cleanup(self):
        SoundPipeline.cleanup(self)
        self.src_type = ""
        self.sink = None


    def on_new_preroll1(self, appsink):
        sample = appsink.emit('pull-preroll')
        log('new preroll1: %s', sample)
        self.emit_buffer1(sample)

    def on_new_sample(self, bus):
        #Gst 1.0
        sample = self.sink.emit("pull-sample")
        self.emit_buffer1(sample)

    def emit_buffer1(self, sample):
        buf = sample.get_buffer()
        #info = sample.get_info()
        size = buf.get_size()
        data = buf.extract_dup(0, size)
        self.do_emit_buffer(data, {"timestamp"  : normv(buf.pts),
                                   "duration"   : normv(buf.duration)})


    def on_new_preroll0(self, appsink):
        buf = appsink.emit('pull-preroll')
        log('new preroll0: %s bytes', len(buf))
        self.emit_buffer0(buf)

    def on_new_buffer(self, bus):
        #pygst 0.10
        buf = self.sink.emit("pull-buffer")
        self.emit_buffer0(buf)


    def emit_buffer0(self, buf, metadata={}):
        """ convert pygst structure into something more generic for the wire """
        #none of the metadata is really needed at present, but it may be in the future:
        #metadata = {"caps"      : buf.get_caps().to_string(),
        #            "size"      : buf.size,
        #            "timestamp" : buf.timestamp,
        #            "duration"  : buf.duration,
        #            "offset"    : buf.offset,
        #            "offset_end": buf.offset_end}
        self.do_emit_buffer(buf.data, {"timestamp" : normv(buf.timestamp),
                                       "duration"  : normv(buf.duration)})


    def do_emit_buffer(self, data, metadata={}):
        self.buffer_count += 1
        self.byte_count += len(data)
        self.emit("new-buffer", data, metadata)

gobject.type_register(SoundSource)


def main():
    from xpra.platform import init, clean
    init("Sound-Play")
    try:
        import os.path
        if len(sys.argv) not in (2, 3):
            print("usage: %s filename [codec]" % sys.argv[0])
            return 1
        filename = sys.argv[1]
        if os.path.exists(filename):
            print("file %s already exists" % filename)
            return 2
        codec = None
        if len(sys.argv)==3:
            codec = sys.argv[2]
            if codec not in CODECS:
                print("invalid codec: %s, codecs supported: %s" % (codec, CODECS))
                return 2
        else:
            parts = filename.split(".")
            if len(parts)>1:
                extension = parts[-1]
                if extension.lower() in CODECS:
                    codec = extension.lower()
                    print("guessed codec %s from file extension %s" % (codec, extension))
            if codec is None:
                codec = MP3
                print("using default codec: %s" % codec)

        log.enable_debug()
        from threading import Lock
        f = open(filename, "wb")
        from xpra.sound.pulseaudio_util import get_pa_device_options
        monitor_devices = get_pa_device_options(True, False)
        log.info("found pulseaudio monitor devices: %s", monitor_devices)
        if len(monitor_devices)==0:
            log.warn("could not detect any pulseaudio monitor devices - will use a test source")
            ss = SoundSource("audiotestsrc", src_options={"wave":2, "freq":100, "volume":0.4}, codec=codec)
        else:
            monitor_device = monitor_devices.items()[0][0]
            log.info("using pulseaudio source device: %s", monitor_device)
            ss = SoundSource("pulsesrc", {"device" : monitor_device}, codec)
        lock = Lock()
        def new_buffer(ss, data, metadata):
            log.info("new buffer: %s bytes, metadata=%s" % (len(data), metadata))
            try:
                lock.acquire()
                if f:
                    f.write(data)
            finally:
                lock.release()
        ss.connect("new-buffer", new_buffer)
        ss.start()

        gobject_mainloop = gobject.MainLoop()
        gobject.threads_init()

        import signal
        def deadly_signal(*args):
            gobject.idle_add(gobject_mainloop.quit)
        signal.signal(signal.SIGINT, deadly_signal)
        signal.signal(signal.SIGTERM, deadly_signal)

        gobject_mainloop.run()

        f.flush()
        log.info("wrote %s bytes to %s", f.tell(), filename)
        try:
            lock.acquire()
            f.close()
            f = None
        finally:
            lock.release()
        return 0
    finally:
        clean()


if __name__ == "__main__":
    sys.exit(main())
