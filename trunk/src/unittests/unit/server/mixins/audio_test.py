#!/usr/bin/env python
# This file is part of Xpra.
# Copyright (C) 2018 Antoine Martin <antoine@xpra.org>
# Xpra is released under the terms of the GNU GPL v2, or, at your option, any
# later version. See the file COPYING for details.

import time
import unittest

from xpra.util import AdHocStruct
from unit.server.mixins.servermixintest_util import ServerMixinTest


class AudioMixinTest(ServerMixinTest):

    def test_audio(self):
        from xpra.server.mixins.audio_server import AudioServer
        from xpra.server.source.audio_mixin import AudioMixin
        opts = AdHocStruct()
        opts.sound_source = ""
        opts.speaker = "on"
        opts.speaker_codec = ["mp3"]
        opts.microphone = "on"
        opts.microphone_codec = ["mp3"]
        opts.pulseaudio = False
        opts.pulseaudio_command = "/bin/true"
        opts.pulseaudio_configure_commands = []
        self._test_mixin_class(AudioServer, opts, {
            "sound.receive" : True,
            "sound.decoders" : ("mp3",),
            }, AudioMixin)
        self.handle_packet(("sound-control", "start", "mp3"))
        time.sleep(1)
        self.handle_packet(("sound-control", "fadeout"))
        time.sleep(1)
        self.handle_packet(("sound-control", "stop"))

def main():
    unittest.main()


if __name__ == '__main__':
    main()
