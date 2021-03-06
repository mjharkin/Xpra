# This file is part of Xpra.
# Copyright (C) 2011-2013 Antoine Martin <antoine@devloop.org.uk>
# Xpra is released under the terms of the GNU GPL v2, or, at your option, any
# later version. See the file COPYING for details.

DEFAULT_SSH_CMD = "ssh"
REINIT_WINDOWS = True
GOT_PASSWORD_PROMPT_SUGGESTION = "Perhaps you need to set up your ssh agent?\n"
SYSTEM_TRAY_SUPPORTED = True
CLIPBOARDS=["CLIPBOARD"]
CLIPBOARD_WANT_TARGETS = True
CLIPBOARD_GREEDY = True
CLIPBOARD_NATIVE_CLASS = ("xpra.platform.darwin.osx_clipboard", "OSXClipboardProtocolHelper", {})
SHADOW_SUPPORTED = True
CAN_DAEMONIZE = True
UI_THREAD_POLLING = 500    #poll every 500 ms
