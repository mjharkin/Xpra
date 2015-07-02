# This file is part of Xpra.
# Copyright (C) 2010 Nathaniel Smith <njs@pobox.com>
# Copyright (C) 2011-2015 Antoine Martin <antoine@devloop.org.uk>
# Xpra is released under the terms of the GNU GPL v2, or, at your option, any
# later version. See the file COPYING for details.

# Platform-specific settings for Win32.
CAN_DAEMONIZE = False
MMAP_SUPPORTED = False
SYSTEM_TRAY_SUPPORTED = True
DEFAULT_SSH_CMD = "plink"

GOT_PASSWORD_PROMPT_SUGGESTION = \
   'Perhaps you need to set up Pageant, or (less secure) use --ssh="plink -pw YOUR-PASSWORD"?\n'
CLIPBOARDS=["CLIPBOARD"]
CLIPBOARD_GREEDY = True
CLIPBOARD_NATIVE_CLASS = ("xpra.clipboard.translated_clipboard", "TranslatedClipboardProtocolHelper", {})

#these don't make sense on win32:
DEFAULT_PULSEAUDIO_COMMAND = ""
DEFAULT_XVFB_COMMAND = ""
PRINT_COMMAND = ""
