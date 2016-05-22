# This file is part of Xpra.
# Copyright (C) 2011 Serviware (Arthur Huillet, <ahuillet@serviware.com>)
# Copyright (C) 2010-2014 Antoine Martin <antoine@devloop.org.uk>
# Copyright (C) 2008, 2010 Nathaniel Smith <njs@pobox.com>
# Xpra is released under the terms of the GNU GPL v2, or, at your option, any
# later version. See the file COPYING for details.

import os
from xpra.client.gtk2.gtk2_window_base import GTK2WindowBase


USE_CAIRO = os.environ.get("XPRA_USE_CAIRO_BACKING", "0")=="1"
if USE_CAIRO:
    from xpra.client.gtk2.cairo_backing import CairoBacking
    BACKING_CLASS = CairoBacking
else:
    from xpra.client.gtk2.pixmap_backing import PixmapBacking
    BACKING_CLASS = PixmapBacking


"""
Actual instantiable plain GTK2 Client Window,
either using CairoBacking or PixmapBacking.
"""
class ClientWindow(GTK2WindowBase):

    __common_gsignals__ = GTK2WindowBase.__common_gsignals__

    def get_backing_class(self):
        return BACKING_CLASS
