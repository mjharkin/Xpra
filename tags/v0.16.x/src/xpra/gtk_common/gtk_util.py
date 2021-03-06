# coding=utf8
# This file is part of Xpra.
# Copyright (C) 2011-2015 Antoine Martin <antoine@devloop.org.uk>
# Xpra is released under the terms of the GNU GPL v2, or, at your option, any
# later version. See the file COPYING for details.

import sys
import os.path

import array
from xpra.os_util import strtobytes
from xpra.gtk_common.gobject_compat import import_gtk, import_gdk, import_pixbufloader, import_pango, import_cairo, import_gobject, is_gtk3
gtk     = import_gtk()
gdk     = import_gdk()
pango   = import_pango()
cairo   = import_cairo()
gobject = import_gobject()
PixbufLoader = import_pixbufloader()

from xpra.log import Logger
log = Logger("gtk", "util")


WIN32 = sys.platform.startswith("win")

GTK_VERSION_INFO = {}
def get_gtk_version_info():
    #update props given:
    global GTK_VERSION_INFO
    if not GTK_VERSION_INFO:
        if hasattr(gtk, "pygtk_version"):
            GTK_VERSION_INFO["pygtk.version"] = gtk.pygtk_version
        if hasattr(gtk, "gtk_version"):
            #GTK2:
            GTK_VERSION_INFO["gtk.version"] = gtk.gtk_version
        elif hasattr(gtk, "_version"):
            #GTK3:
            GTK_VERSION_INFO["gtk.version"] = gtk._version
        if hasattr(gdk, "__version__"):
            #GTK2:
            GTK_VERSION_INFO["gdk.version"] = gdk.__version__
        elif hasattr(gdk, "_version"):
            #GTK3:
            GTK_VERSION_INFO["gdk.version"] = gdk._version
        if is_gtk3():
            try:
                import gi
                GTK_VERSION_INFO["gi.version"] = gi.__version__
            except:
                pass
        if hasattr(gobject, "pygobject_version"):
            GTK_VERSION_INFO["gobject.version"] = gobject.pygobject_version
        elif hasattr(gobject, "_version"):
            GTK_VERSION_INFO["gobject.version"] = gobject._version
        if hasattr(cairo, "version"):
            GTK_VERSION_INFO["cairo.version"] = cairo.version
        if hasattr(pango, "version_string"):
            GTK_VERSION_INFO["pango.version"] = pango.version_string()
        try:
            import glib
            GTK_VERSION_INFO["glib.version"] = glib.glib_version
            GTK_VERSION_INFO["pyglib.version"] = glib.pyglib_version
        except:
            pass
    return GTK_VERSION_INFO.copy()


if is_gtk3():
    def is_realized(widget):
        return widget.get_realized()

    def color_parse(*args):
        ok, v = gdk.Color.parse(*args)
        if not ok:
            return None
        return v
    def get_xwindow(w):
        return w.get_xid()
    def get_default_root_window():
        return gdk.Screen.get_default().get_root_window()
    def get_root_size():
        if WIN32:
            #FIXME: hopefully, we can remove this code once GTK3 on win32 is fixed?
            #we do it the hard way because the root window geometry is invalid on win32:
            #and even just querying it causes this warning:
            #"GetClientRect failed: Invalid window handle."
            display = gdk.Display.get_default()
            n = display.get_n_screens()
            w, h = 0, 0
            for i in range(n):
                screen = display.get_screen(i)
                w += screen.get_width()
                h += screen.get_height()
        else:
            #the easy way for platforms that work out of the box:
            root = get_default_root_window()
            w, h = root.get_geometry()[2:4]
        if w<=0 or h<=0 or w>32768 or h>32768:
            log.warn("Warning: Gdk returned invalid root window dimensions: %ix%i", w, h)
            w, h = 1920, 1080
            log.warn(" using %ix%i instead", w, h)
        return w, h

    keymap_get_for_display  = gdk.Keymap.get_for_display

    def get_default_cursor():
        return gdk.Cursor.new(gdk.CursorType.X_CURSOR)
    new_Cursor_for_display  = gdk.Cursor.new_for_display
    new_Cursor_from_pixbuf  = gdk.Cursor.new_from_pixbuf
    from gi.repository import GdkPixbuf     #@UnresolvedImport
    image_new_from_pixbuf   = gtk.Image.new_from_pixbuf
    pixbuf_new_from_file    = GdkPixbuf.Pixbuf.new_from_file
    window_set_default_icon = gtk.Window.set_default_icon
    icon_theme_get_default  = gtk.IconTheme.get_default

    def gdk_cairo_context(cairo_context):
        return cairo_context
    def pixbuf_new_from_data(*args):
        args = list(args)+[None, None]
        return GdkPixbuf.Pixbuf.new_from_data(*args)
    get_default_keymap      = gdk.Keymap.get_default
    display_get_default     = gdk.Display.get_default
    screen_get_default      = gdk.Screen.get_default
    cairo_set_source_pixbuf = gdk.cairo_set_source_pixbuf
    COLORSPACE_RGB          = GdkPixbuf.Colorspace.RGB
    INTERP_HYPER    = GdkPixbuf.InterpType.HYPER
    INTERP_BILINEAR = GdkPixbuf.InterpType.BILINEAR
    RELIEF_NONE     = gtk.ReliefStyle.NONE
    RELIEF_NORMAL   = gtk.ReliefStyle.NORMAL
    FILL            = gtk.AttachOptions.FILL
    EXPAND          = gtk.AttachOptions.EXPAND
    STATE_NORMAL    = gtk.StateType.NORMAL
    WIN_POS_CENTER  = gtk.WindowPosition.CENTER
    RESPONSE_CANCEL = gtk.ResponseType.CANCEL
    RESPONSE_OK     = gtk.ResponseType.OK
    WINDOW_TOPLEVEL = gdk.WindowType.TOPLEVEL
    FILE_CHOOSER_ACTION_SAVE    = gtk.FileChooserAction.SAVE
    FILE_CHOOSER_ACTION_OPEN    = gtk.FileChooserAction.OPEN
    PROPERTY_CHANGE_MASK = gdk.EventMask.PROPERTY_CHANGE_MASK
    BUTTON_PRESS_MASK    = gdk.EventMask.BUTTON_PRESS_MASK
    ACCEL_LOCKED = gtk.AccelFlags.LOCKED
    ACCEL_VISIBLE = gtk.AccelFlags.VISIBLE
    JUSTIFY_LEFT    = gtk.Justification.LEFT
    JUSTIFY_RIGHT   = gtk.Justification.RIGHT
    POINTER_MOTION_MASK         = gdk.EventMask.POINTER_MOTION_MASK
    POINTER_MOTION_HINT_MASK    = gdk.EventMask.POINTER_MOTION_HINT_MASK
    MESSAGE_INFO    = gtk.MessageType.INFO
    BUTTONS_CLOSE   = gtk.ButtonsType.CLOSE
    DIALOG_DESTROY_WITH_PARENT  = 0

    WINDOW_POPUP    = gtk.WindowType.POPUP
    WINDOW_TOPLEVEL = gtk.WindowType.TOPLEVEL

    LSB_FIRST       = gdk.ByteOrder.LSB_FIRST
    MSB_FIRST       = gdk.ByteOrder.MSB_FIRST
    STATIC_GRAY     = gdk.VisualType.STATIC_GRAY
    GRAYSCALE       = gdk.VisualType.GRAYSCALE
    STATIC_COLOR    = gdk.VisualType.STATIC_COLOR
    PSEUDO_COLOR    = gdk.VisualType.PSEUDO_COLOR
    TRUE_COLOR      = gdk.VisualType.TRUE_COLOR
    DIRECT_COLOR    = gdk.VisualType.DIRECT_COLOR

    mt = gdk.ModifierType
    SHIFT_MASK      = mt.SHIFT_MASK
    LOCK_MASK       = mt.LOCK_MASK
    META_MASK       = mt.META_MASK
    CONTROL_MASK    = mt.CONTROL_MASK
    MOD1_MASK       = mt.MOD1_MASK
    MOD2_MASK       = mt.MOD2_MASK
    MOD3_MASK       = mt.MOD3_MASK
    MOD4_MASK       = mt.MOD4_MASK
    MOD5_MASK       = mt.MOD5_MASK

    BUTTON_MASK = {mt.BUTTON1_MASK : 1,
                   mt.BUTTON2_MASK : 2,
                   mt.BUTTON3_MASK : 3,
                   mt.BUTTON4_MASK : 4,
                   mt.BUTTON5_MASK : 5}
    del mt

    em = gdk.EventMask
    WINDOW_EVENT_MASK = em.STRUCTURE_MASK | em.KEY_PRESS_MASK | em.KEY_RELEASE_MASK \
            | em.POINTER_MOTION_MASK | em.BUTTON_PRESS_MASK | em.BUTTON_RELEASE_MASK \
            | em.PROPERTY_CHANGE_MASK | em.SCROLL_MASK
    del em

    WINDOW_NAME_TO_HINT = {
                "NORMAL"        : gdk.WindowTypeHint.NORMAL,
                "DIALOG"        : gdk.WindowTypeHint.DIALOG,
                "MENU"          : gdk.WindowTypeHint.MENU,
                "TOOLBAR"       : gdk.WindowTypeHint.TOOLBAR,
                "SPLASH"        : gdk.WindowTypeHint.SPLASHSCREEN,
                "UTILITY"       : gdk.WindowTypeHint.UTILITY,
                "DOCK"          : gdk.WindowTypeHint.DOCK,
                "DESKTOP"       : gdk.WindowTypeHint.DESKTOP,
                "DROPDOWN_MENU" : gdk.WindowTypeHint.DROPDOWN_MENU,
                "POPUP_MENU"    : gdk.WindowTypeHint.POPUP_MENU,
                "TOOLTIP"       : gdk.WindowTypeHint.TOOLTIP,
                "NOTIFICATION"  : gdk.WindowTypeHint.NOTIFICATION,
                "COMBO"         : gdk.WindowTypeHint.COMBO,
                "DND"           : gdk.WindowTypeHint.DND
                }

    from gi.repository.Gtk import Clipboard     #@UnresolvedImport
    CLIPBOARD_SELECTION = {}
    #gtk2: uses strings:
    for x in ("PRIMARY", "SECONDARY", "CLIPBOARD"):
        CLIPBOARD_SELECTION[x] = getattr(gdk, "SELECTION_%s" % x)
    def GetClipboard(selection):
        return Clipboard.get(CLIPBOARD_SELECTION[selection])

    #copied from pygtkcompat - I wished I had found this earlier..
    orig_pack_end = gtk.Box.pack_end
    def pack_end(self, child, expand=True, fill=True, padding=0):
        orig_pack_end(self, child, expand, fill, padding)
    gtk.Box.pack_end = pack_end
    orig_pack_start = gtk.Box.pack_start
    def pack_start(self, child, expand=True, fill=True, padding=0):
        orig_pack_start(self, child, expand, fill, padding)
    gtk.Box.pack_start = pack_start
    gtk.combo_box_new_text = gtk.ComboBoxText

    class OptionMenu(gtk.MenuButton):
        pass

    gdk_window_process_all_updates = gdk.Window.process_all_updates
    def gtk_main():
        gdk.threads_init()
        try:
            gdk.threads_enter()
            gtk.main()
        finally:
            gdk.threads_leave()

else:
    def get_xwindow(w):
        return w.xid
    #gtk2:
    if gtk.gtk_version<(2,18):
        raise Exception("your version of PyGTK is too old: %s" % str(gtk.pygtk_version))

    if not hasattr(gtk.Widget, "get_realized"):
        def is_realized(widget):
            return widget.flags() & gtk.REALIZED
    else:
        def is_realized(widget):
            return widget.get_realized()

    get_default_root_window = gdk.get_default_root_window
    def get_root_size():
        return get_default_root_window().get_size()
    keymap_get_for_display  = gdk.keymap_get_for_display

    def get_default_cursor():
        return gdk.Cursor(gdk.X_CURSOR)
    color_parse             = gdk.color_parse
    new_Cursor_for_display  = gdk.Cursor
    new_Cursor_from_pixbuf  = gdk.Cursor
    image_new_from_pixbuf   = gtk.image_new_from_pixbuf
    pixbuf_new_from_file    = gdk.pixbuf_new_from_file
    pixbuf_new_from_data    = gdk.pixbuf_new_from_data
    get_default_keymap      = gdk.keymap_get_default
    display_get_default     = gdk.display_get_default
    screen_get_default      = gdk.screen_get_default
    window_set_default_icon = gtk.window_set_default_icon
    icon_theme_get_default  = gtk.icon_theme_get_default

    def gdk_cairo_context(cairo_context):
        return gdk.CairoContext(cairo_context)
    def cairo_set_source_pixbuf(cr, pixbuf, x, y):
        cr.set_source_pixbuf(pixbuf, x, y)
    COLORSPACE_RGB          = gdk.COLORSPACE_RGB
    INTERP_HYPER    = gdk.INTERP_HYPER
    INTERP_BILINEAR = gdk.INTERP_BILINEAR
    RELIEF_NONE     = gtk.RELIEF_NONE
    RELIEF_NORMAL   = gtk.RELIEF_NORMAL
    FILL            = gtk.FILL
    EXPAND          = gtk.EXPAND
    STATE_NORMAL    = gtk.STATE_NORMAL
    WIN_POS_CENTER  = gtk.WIN_POS_CENTER
    RESPONSE_CANCEL = gtk.RESPONSE_CANCEL
    RESPONSE_OK     = gtk.RESPONSE_OK
    WINDOW_TOPLEVEL = gdk.WINDOW_TOPLEVEL
    FILE_CHOOSER_ACTION_SAVE    = gtk.FILE_CHOOSER_ACTION_SAVE
    FILE_CHOOSER_ACTION_OPEN    = gtk.FILE_CHOOSER_ACTION_OPEN
    PROPERTY_CHANGE_MASK = gdk.PROPERTY_CHANGE_MASK
    BUTTON_PRESS_MASK    = gdk.BUTTON_PRESS_MASK
    ACCEL_LOCKED = gtk.ACCEL_LOCKED
    ACCEL_VISIBLE = gtk.ACCEL_VISIBLE
    JUSTIFY_LEFT    = gtk.JUSTIFY_LEFT
    JUSTIFY_RIGHT   = gtk.JUSTIFY_RIGHT
    POINTER_MOTION_MASK         = gdk.POINTER_MOTION_MASK
    POINTER_MOTION_HINT_MASK    = gdk.POINTER_MOTION_HINT_MASK
    MESSAGE_INFO    = gtk.MESSAGE_INFO
    BUTTONS_CLOSE   = gtk.BUTTONS_CLOSE
    DIALOG_DESTROY_WITH_PARENT = gtk.DIALOG_DESTROY_WITH_PARENT

    WINDOW_POPUP    = gtk.WINDOW_POPUP
    WINDOW_TOPLEVEL = gtk.WINDOW_TOPLEVEL

    LSB_FIRST       = gdk.LSB_FIRST
    MSB_FIRST       = gdk.MSB_FIRST
    STATIC_GRAY     = gdk.VISUAL_STATIC_GRAY
    GRAYSCALE       = gdk.VISUAL_GRAYSCALE
    STATIC_COLOR    = gdk.VISUAL_STATIC_COLOR
    PSEUDO_COLOR    = gdk.VISUAL_PSEUDO_COLOR
    TRUE_COLOR      = gdk.VISUAL_TRUE_COLOR
    DIRECT_COLOR    = gdk.VISUAL_DIRECT_COLOR

    SHIFT_MASK      = gdk.SHIFT_MASK
    LOCK_MASK       = gdk.LOCK_MASK
    META_MASK       = gdk.META_MASK
    CONTROL_MASK    = gdk.CONTROL_MASK
    MOD1_MASK       = gdk.MOD1_MASK
    MOD2_MASK       = gdk.MOD2_MASK
    MOD3_MASK       = gdk.MOD3_MASK
    MOD4_MASK       = gdk.MOD4_MASK
    MOD5_MASK       = gdk.MOD5_MASK

    BUTTON_MASK = {gdk.BUTTON1_MASK : 1,
                   gdk.BUTTON2_MASK : 2,
                   gdk.BUTTON3_MASK : 3,
                   gdk.BUTTON4_MASK : 4,
                   gdk.BUTTON5_MASK : 5}

    WINDOW_EVENT_MASK = gdk.STRUCTURE_MASK | gdk.KEY_PRESS_MASK | gdk.KEY_RELEASE_MASK \
            | gdk.POINTER_MOTION_MASK | gdk.BUTTON_PRESS_MASK | gdk.BUTTON_RELEASE_MASK \
            | gdk.PROPERTY_CHANGE_MASK

    WINDOW_NAME_TO_HINT = {
                "NORMAL"        : gdk.WINDOW_TYPE_HINT_NORMAL,
                "DIALOG"        : gdk.WINDOW_TYPE_HINT_DIALOG,
                "MENU"          : gdk.WINDOW_TYPE_HINT_MENU,
                "TOOLBAR"       : gdk.WINDOW_TYPE_HINT_TOOLBAR,
                "SPLASH"        : gdk.WINDOW_TYPE_HINT_SPLASHSCREEN,
                "UTILITY"       : gdk.WINDOW_TYPE_HINT_UTILITY,
                "DOCK"          : gdk.WINDOW_TYPE_HINT_DOCK,
                "DESKTOP"       : gdk.WINDOW_TYPE_HINT_DESKTOP,
                "DROPDOWN_MENU" : gdk.WINDOW_TYPE_HINT_DROPDOWN_MENU,
                "POPUP_MENU"    : gdk.WINDOW_TYPE_HINT_POPUP_MENU,
                "TOOLTIP"       : gdk.WINDOW_TYPE_HINT_TOOLTIP,
                "NOTIFICATION"  : gdk.WINDOW_TYPE_HINT_NOTIFICATION,
                "COMBO"         : gdk.WINDOW_TYPE_HINT_COMBO,
                "DND"           : gdk.WINDOW_TYPE_HINT_DND
                }

    OptionMenu  = gtk.OptionMenu

    def GetClipboard(selection):
        return gtk.Clipboard(selection=selection)

    gdk_window_process_all_updates = gdk.window_process_all_updates
    def gtk_main():
        if gtk.main_level()==0:
            gdk.threads_init()
            try:
                gdk.threads_enter()
                gtk.main()
            finally:
                gdk.threads_leave()


def get_display_info():
    display = display_get_default()
    info = {
            "root"                  : get_default_root_window().get_geometry(),
            "root-size"             : get_root_size(),
            "screens"               : display.get_n_screens(),
            "name"                  : display.get_name(),
            "pointer"               : display.get_pointer()[1:3],
            "devices"               : len(display.list_devices()),
            "default_cursor_size"   : display.get_default_cursor_size(),
            "maximal_cursor_size"   : display.get_maximal_cursor_size(),
            "pointer_is_grabbed"    : display.pointer_is_grabbed(),
            }
    for x in ("composite", "cursor_alpha", "cursor_color", "selection_notification", "clipboard_persistence", "shapes"):
        f = "supports_"+x
        if hasattr(display, f):
            fn = getattr(display, f)
            info[x]  = fn()
    for i in range(display.get_n_screens()):
        screen = display.get_screen(i)
        sk = "screen[%s]" % i
        try:
            w = screen.get_root_window()
            info[sk+".root"] = w.get_geometry()
        except:
            pass
        info[sk+".name"] = screen.make_display_name()
        for x in ("width", "height", "width_mm", "height_mm", "resolution", "primary_monitor"):
            fn = getattr(screen, "get_"+x)
            try:
                info[sk+"."+x] = int(fn())
            except:
                pass
        info[sk+".monitors"] = screen.get_n_monitors()
        for j in range(screen.get_n_monitors()):
            mk = "screen[%s].monitor[%s]" % (i, j)
            geom = screen.get_monitor_geometry(j)
            for x in ("x", "y", "width", "height"):
                info[mk+"."+x] = getattr(geom, x)
            if hasattr(screen, "get_monitor_plug_name"):
                info[mk+".plug_name"] = screen.get_monitor_plug_name(j) or ""
            for x in ("scale_factor", "width_mm", "height_mm"):
                try:
                    fn = getattr(screen, "get_monitor_"+x)
                    info[mk+"."+x] = int(fn(j))
                except:
                    pass
            if hasattr(screen, "get_monitor_workarea"): #GTK3.4:
                rectangle = screen.get_monitor_workarea(j)
                for x in ("x", "y", "width", "height"):
                    info[mk+".workarea."+x] = getattr(rectangle, x)
        try:
            import cairo
            fo = screen.get_font_options()
            #win32 and osx return nothing here...
            if fo:
                fk = sk+".fontoptions"
                for x,vdict in {
                                "antialias"     : {cairo.ANTIALIAS_DEFAULT      : "default", cairo.ANTIALIAS_NONE       : "none",   cairo.ANTIALIAS_GRAY        : "gray",   cairo.ANTIALIAS_SUBPIXEL    : "subpixel"},
                                "hint_metrics"  : {cairo.HINT_METRICS_DEFAULT   : "default", cairo.HINT_METRICS_OFF     : "off",    cairo.HINT_METRICS_ON       : "on"},
                                "hint_style"    : {cairo.HINT_STYLE_DEFAULT     : "default", cairo.HINT_STYLE_NONE      : "none",   cairo.HINT_STYLE_SLIGHT     : "slight", cairo.HINT_STYLE_MEDIUM     : "medium", cairo.HINT_STYLE_FULL       : "full"},
                                "subpixel_order": {cairo.SUBPIXEL_ORDER_DEFAULT : "default", cairo.SUBPIXEL_ORDER_RGB   : "RGB",    cairo.SUBPIXEL_ORDER_BGR    : "BGR",    cairo.SUBPIXEL_ORDER_VRGB   : "VRGB",   cairo.SUBPIXEL_ORDER_VBGR   : "VBGR"},
                                }.items():
                    fn = getattr(fo, "get_"+x)
                    val = fn()
                    info[fk+"."+x] = vdict.get(val, val)
        except:
            pass
        def visual(k, v):
            if not v:
                return
            vk = sk+"."+k       #ie: screen[0].rgb
            for x, vdict in {"bits_per_rgb" : {},
                             "byte_order"   : {LSB_FIRST    : "LSB", MSB_FIRST  : "MSB"},
                             "colormap_size": {},
                             "depth"        : {},
                             "red_pixel_details"    : {},
                             "green_pixel_details"  : {},
                             "blue_pixel_details"   : {},
                             "visual_type"  : {STATIC_GRAY : "STATIC_GRAY", GRAYSCALE : "GRAYSCALE",  STATIC_COLOR : "STATIC_COLOR", PSEUDO_COLOR : "PSEUDO_COLOR", TRUE_COLOR : "TRUE_COLOR", DIRECT_COLOR : "DIRECT_COLOR"},
                             }.items():
                val = None
                try:
                    val = getattr(v, x.replace("visual_"))  #ugly workaround for "visual_type" -> "type" for GTK2...
                except:
                    try:
                        fn = getattr(v, "get_"+x)
                        val = fn()
                    except:
                        pass
                if val is not None:
                    info[vk+"."+x] = vdict.get(val, val)
        try:
            visual("rgb", screen.get_rgb_visual())
        except:
            pass    #not in gtk3?
        visual("rgba", screen.get_rgba_visual())
        visual("system_visual", screen.get_system_visual())
        visuals = screen.list_visuals()
        info[sk+".visuals"] = len(visuals)
        #gtk.settings
        if is_gtk3():
            def get_setting(key):
                #try string first, then int
                for t in (gobject.TYPE_STRING, gobject.TYPE_INT):
                    v = gobject.Value()
                    v.init(t)
                    if screen.get_setting(key, v):
                        return v.get_value()
                return None
        else:
            settings = gtk.settings_get_for_screen(screen)
            def get_setting(key):
                return settings.get_property(key)
        try:
            ssk = "%s.settings" % sk
            for x in ("antialias", "dpi", "hinting", "hintstyle", "rgba"):
                try:
                    v = get_setting("gtk-xft-"+x)
                except:
                    continue
                if v is None:
                    v = ""
                info[ssk+"."+x] = v
        except:
            pass
    if is_gtk3():
        dm = display.get_device_manager()
        for dt, name in {gdk.DeviceType.MASTER  : "master",
                         gdk.DeviceType.SLAVE   : "slave",
                         gdk.DeviceType.FLOATING: "floating"}.items():
            dk = "devices.%s" % name
            devices = dm.list_devices(dt)
            info[dk] = len(devices)
            for i, d in enumerate(devices):
                info[dk+"[%s]" % i] = d.get_name()
    else:
        devices = display.list_devices()
        info["devices"] = len(devices)
        for i, d in enumerate(devices):
            info["device[%s]" % i] = d.get_name()
    return info


def get_preferred_size(widget):
    if is_gtk3():
        #ignore "min", we only care about "natural":
        _, w = widget.get_preferred_width()
        _, h = widget.get_preferred_height()
        return w, h
    return widget.size_request()

def scaled_image(pixbuf, icon_size=None):
    if icon_size:
        pixbuf = pixbuf.scale_simple(icon_size, icon_size, INTERP_BILINEAR)
    return image_new_from_pixbuf(pixbuf)


def get_pixbuf_from_data(rgb_data, has_alpha, w, h, rowstride):
    if is_gtk3():
        data = array.array('B', strtobytes(rgb_data))
        return GdkPixbuf.Pixbuf.new_from_data(data, GdkPixbuf.Colorspace.RGB,
                                         True, 8, w, h, rowstride,
                                         None, None)
    return gdk.pixbuf_new_from_data(rgb_data, gdk.COLORSPACE_RGB, has_alpha, 8, w, h, rowstride)


def get_icon_from_file(filename):
    try:
        if not os.path.exists(filename):
            log.warn("%s does not exist", filename)
            return    None
        with open(filename, mode='rb') as f:
            data = f.read()
        loader = PixbufLoader()
        loader.write(data)
        loader.close()
    except Exception as e:
        log.error("get_icon_from_file(%s) %s", filename, e)
        return    None
    pixbuf = loader.get_pixbuf()
    return pixbuf


def imagebutton(title, icon, tooltip=None, clicked_callback=None, icon_size=32, default=False, min_size=None, label_color=None):
    button = gtk.Button(title)
    settings = button.get_settings()
    settings.set_property('gtk-button-images', True)
    if icon:
        button.set_image(scaled_image(icon, icon_size))
    if tooltip:
        button.set_tooltip_text(tooltip)
    if min_size:
        button.set_size_request(min_size, min_size)
    if clicked_callback:
        button.connect("clicked", clicked_callback)
    if default:
        if is_gtk3():
            button.set_can_default(True)
        else:
            button.set_flags(gtk.CAN_DEFAULT)
    if label_color:
        alignment = button.get_children()[0]
        b_hbox = alignment.get_children()[0]
        label = b_hbox.get_children()[1]
        label.modify_fg(STATE_NORMAL, label_color)
    return button

def menuitem(title, image=None, tooltip=None, cb=None):
    """ Utility method for easily creating an ImageMenuItem """
    menu_item = gtk.ImageMenuItem(title)
    if image:
        menu_item.set_image(image)
        #override gtk defaults: we *want* icons:
        settings = menu_item.get_settings()
        settings.set_property('gtk-menu-images', True)
        if hasattr(menu_item, "set_always_show_image"):
            menu_item.set_always_show_image(True)
    if tooltip:
        menu_item.set_tooltip_text(tooltip)
    if cb:
        menu_item.connect('activate', cb)
    menu_item.show()
    return menu_item


def add_close_accel(window, callback):
    if is_gtk3():
        def connect(ag, *args):
            ag.connect(*args)
    else:
        def connect(ag, *args):
            ag.connect_group(*args)
    accel_group = gtk.AccelGroup()
    key, mod = gtk.accelerator_parse('<control>F4')
    connect(accel_group, key, mod, ACCEL_LOCKED, callback)
    window.add_accel_group(accel_group)
    accel_group = gtk.AccelGroup()
    key, mod = gtk.accelerator_parse('<Alt>F4')
    connect(accel_group, key, mod, ACCEL_LOCKED, callback)
    escape_key, modifier = gtk.accelerator_parse('Escape')
    connect(accel_group, escape_key, modifier, ACCEL_LOCKED |  ACCEL_VISIBLE, callback)
    window.add_accel_group(accel_group)


def label(text="", tooltip=None, font=None):
    l = gtk.Label(text)
    if font:
        fontdesc = pango.FontDescription(font)
        l.modify_font(fontdesc)
    if tooltip:
        l.set_tooltip_text(tooltip)
    return l


def title_box(label_str):
    eb = gtk.EventBox()
    l = label(label_str)
    l.modify_fg(STATE_NORMAL, gdk.Color(red=48*256, green=0, blue=0))
    al = gtk.Alignment(xalign=0.0, yalign=0.5, xscale=0.0, yscale=0.0)
    al.set_padding(0, 0, 10, 10)
    al.add(l)
    eb.add(al)
    eb.modify_bg(STATE_NORMAL, gdk.Color(red=219*256, green=226*256, blue=242*256))
    return eb



#utility method to ensure there is always only one CheckMenuItem
#selected in a submenu:
def ensure_item_selected(submenu, item):
    if not isinstance(item, gtk.CheckMenuItem):
        return
    if item.get_active():
        #deactivate all except this one
        def deactivate(items, skip=None):
            for x in items:
                if x==skip:
                    continue
                if isinstance(x, gtk.MenuItem):
                    submenu = x.get_submenu()
                    if submenu:
                        deactivate(submenu.get_children(), skip)
                if isinstance(x, gtk.CheckMenuItem):
                    if x!=item and x.get_active():
                        x.set_active(False)
        deactivate(submenu.get_children(), item)
        return item
    #ensure there is at least one other active item
    def get_active_item(items):
        for x in items:
            if isinstance(x, gtk.MenuItem):
                submenu = x.get_submenu()
                if submenu:
                    a = get_active_item(submenu.get_children())
                    if a:
                        return a
            if isinstance(x, gtk.CheckMenuItem):
                if x.get_active():
                    return x
        return None
    active = get_active_item(submenu.get_children())
    if active:
        return  active
    #if not then keep this one active:
    item.set_active(True)
    return item


def CheckMenuItem(label, tooltip=None):
    """ adds a get_label() method for older versions of gtk which do not have it
        beware that this label is not mutable!
    """
    cmi = gtk.CheckMenuItem(label)
    if not hasattr(cmi, "get_label"):
        def get_label():
            return  label
        cmi.get_label = get_label
    if tooltip:
        cmi.set_tooltip_text(tooltip)
    return cmi


class TableBuilder(object):

    def __init__(self, rows=1, columns=2, homogeneous=False):
        self.table = gtk.Table(rows, columns, homogeneous)
        self.table.set_col_spacings(0)
        self.table.set_row_spacings(0)
        self.row = 0
        self.widget_xalign = 0.0

    def get_table(self):
        return self.table

    def add_row(self, label, *widgets):
        if label:
            l_al = gtk.Alignment(xalign=1.0, yalign=0.5, xscale=0.0, yscale=0.0)
            l_al.add(label)
            self.attach(l_al, 0)
        if widgets:
            i = 1
            for w in widgets:
                if w:
                    w_al = gtk.Alignment(xalign=self.widget_xalign, yalign=0.5, xscale=0.0, yscale=0.0)
                    w_al.add(w)
                    self.attach(w_al, i)
                i += 1
        self.inc()

    def attach(self, widget, i, count=1, xoptions=FILL, xpadding=10):
        self.table.attach(widget, i, i+count, self.row, self.row+1, xoptions=xoptions, xpadding=xpadding)

    def inc(self):
        self.row += 1

    def new_row(self, row_label_str, value1, value2=None, label_tooltip=None):
        row_label = label(row_label_str, label_tooltip)
        self.add_row(row_label, value1, value2)


def choose_file(parent_window, title, action, action_button, callback, file_filter=None):
    log("choose_file%s", (parent_window, title, action, action_button, callback, file_filter))
    chooser = gtk.FileChooserDialog(title,
                                parent=parent_window, action=action,
                                buttons=(gtk.STOCK_CANCEL, RESPONSE_CANCEL, action_button, RESPONSE_OK))
    chooser.set_select_multiple(False)
    chooser.set_default_response(RESPONSE_OK)
    if file_filter:
        chooser.add_filter(file_filter)
    response = chooser.run()
    filenames = chooser.get_filenames()
    chooser.hide()
    chooser.destroy()
    if response!=RESPONSE_OK or len(filenames)!=1:
        return
    filename = filenames[0]
    callback(filename)
