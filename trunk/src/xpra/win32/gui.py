# This file is part of Parti.
# Copyright (C) 2011 Antoine Martin <antoine@nagafix.co.uk>
# Copyright (C) 2010 Nathaniel Smith <njs@pobox.com>
# Parti is released under the terms of the GNU GPL v2, or, at your option, any
# later version. See the file COPYING for details.

# Platform-specific code for Win32 -- the parts that may import gtk.

import os.path

from xpra.platform.client_extras_base import ClientExtrasBase, WIN32_LAYOUTS
from xpra.platform.default_clipboard import ClipboardProtocolHelper
from wimpiggy.log import Logger
log = Logger()


class ClientExtras(ClientExtrasBase):
    def __init__(self, client, opts):
        ClientExtrasBase.__init__(self, client, opts)
        self.setup_menu()
        self.setup_tray(opts.tray_icon)
        self.setup_clipboard_helper(ClipboardProtocolHelper)

    def exit(self):
        if self.tray:
            self.tray.close()

    def can_notify(self):
        return  True

    def show_notify(self, dbus_id, id, app_name, replaces_id, app_icon, summary, body, expire_timeout):
        if self.notify:
            self.notify(self.tray.getHWND(), summary, body, expire_timeout)


    def setup_tray(self, tray_icon_filename):
        self.tray = None
        self.notify = None
        #we wait for session_name to be set during the handshake
        #the alternative would be to implement a set_name() method
        #on the Win32Tray - but this looks too complicated
        self.client.connect("handshake-complete", self.do_setup_tray, tray_icon_filename)

    def do_setup_tray(self, client, tray_icon_filename):
        self.tray = None
        self.notify = None
        if not tray_icon_filename or not os.path.exists(tray_icon_filename):
            tray_icon_filename = self.get_icon_filename('xpra.ico')
        if not tray_icon_filename or not os.path.exists(tray_icon_filename):
            log.error("invalid tray icon filename: '%s'" % tray_icon_filename)

        try:
            from xpra.win32.win32_tray import Win32Tray
            self.tray = Win32Tray(self.client.session_name, self.activate_menu, self.quit, tray_icon_filename)
        except Exception, e:
            log.error("failed to load native Windows NotifyIcon: %s", e)
            return  #cant do balloon without tray!
        try:
            from xpra.win32.win32_balloon import notify
            self.notify = notify
        except Exception, e:
            log.error("failed to load native win32 balloon: %s", e)

    def get_layout_spec(self):
        layout = None
        variant = None
        variants = None
        try:
            import win32api         #@UnresolvedImport
            id = win32api.GetKeyboardLayout(0) & 0xffff
            if id in WIN32_LAYOUTS:
                code, _, _, _, layout, variants = WIN32_LAYOUTS.get(id)
                log.debug("found keyboard layout '%s' with variants=%s, code '%s' for id=%s", layout, variants, code, id)
            if not layout:
                log.debug("unknown keyboard layout for id: %s", id)
        except Exception, e:
            log.error("failed to detect keyboard layout: %s", e)
        return layout,variant,variants

    def get_keyboard_repeat(self):
        try:
            import win32con         #@UnresolvedImport
            import win32gui         #@UnresolvedImport
            _delay = win32gui.SystemParametersInfo(win32con.SPI_GETKEYBOARDDELAY)
            _speed = win32gui.SystemParametersInfo(win32con.SPI_GETKEYBOARDSPEED)
            #now we need to normalize those weird win32 values:
            #0=250, 3=1000:
            delay = (_delay+1) * 250
            #0=1000/30, 31=1000/2.5
            _speed = min(31, max(0, _speed))
            speed = int(1000/(2.5+27.5*_speed/31))
            log.debug("keyboard repeat speed(%s)=%s, delay(%s)=%s", _speed, speed, _delay, delay)
            return  delay,speed
        except Exception, e:
            log.error("failed to get keyboard rate: %s", e)
        return None

    def popup_menu_workaround(self, menu):
        self.add_popup_menu_workaround(menu)
