# This file is part of Xpra.
# Copyright (C) 2010-2018 Antoine Martin <antoine@xpra.org>
# Copyright (C) 2008 Nathaniel Smith <njs@pobox.com>
# Xpra is released under the terms of the GNU GPL v2, or, at your option, any
# later version. See the file COPYING for details.

# DO NOT IMPORT GTK HERE: see
#  http://lists.partiwm.org/pipermail/parti-discuss/2008-September/000041.html
#  http://lists.partiwm.org/pipermail/parti-discuss/2008-September/000042.html
# (also do not import anything that imports gtk)
import sys
import os.path
import atexit
import traceback

from xpra.scripts.main import info, warn, no_gtk, validate_encryption, parse_env, configure_env
from xpra.scripts.config import InitException, TRUE_OPTIONS, FALSE_OPTIONS
from xpra.os_util import (
    SIGNAMES, POSIX, WIN32, OSX,
    FDChangeCaptureContext, get_ssh_port,
    get_username_for_uid, get_home_for_uid, get_shell_for_uid, getuid, setuidgid,
    get_hex_uuid, get_status_output, strtobytes, bytestostr, get_util_logger, osexpand,
    )
from xpra.util import envbool, csv
from xpra.platform.dotxpra import DotXpra


_cleanups = []
def run_cleanups():
    global _cleanups
    cleanups = _cleanups
    _cleanups = []
    for c in cleanups:
        try:
            c()
        except:
            print("error running cleanup %s" % c)
            traceback.print_exception(*sys.exc_info())

_when_ready = []

def add_when_ready(f):
    _when_ready.append(f)

def add_cleanup(f):
    _cleanups.append(f)

def insert_cleanup(f):
    _cleanups.insert(0, f)


def deadly_signal(signum):
    info("got deadly signal %s, exiting\n" % SIGNAMES.get(signum, signum))
    run_cleanups()
    # This works fine in tests, but for some reason if I use it here, then I
    # get bizarre behavior where the signal handler runs, and then I get a
    # KeyboardException (?!?), and the KeyboardException is handled normally
    # and exits the program (causing the cleanup handlers to be run again):
    #signal.signal(signum, signal.SIG_DFL)
    #kill(os.getpid(), signum)
    os._exit(128 + signum)


def _root_prop_set(prop_name, ptype="u32", value=0):
    from xpra.gtk_common.gtk_util import get_default_root_window
    from xpra.x11.gtk_x11.prop import prop_set
    prop_set(get_default_root_window(), prop_name, ptype, value)
def _root_prop_get(prop_name, ptype="u32"):
    from xpra.gtk_common.gtk_util import get_default_root_window
    from xpra.x11.gtk_x11.prop import prop_get
    try:
        return prop_get(get_default_root_window(), prop_name, ptype)
    except Exception:
        return None

def _save_int(prop_name, pid):
    _root_prop_set(prop_name, "u32", pid)

def _get_int(prop_name):
    return _root_prop_get(prop_name, "u32")

def _save_str(prop_name, s):
    _root_prop_set(prop_name, "latin1", s)

def _get_str(prop_name):
    v = _root_prop_get(prop_name, "latin1")
    if v is not None:
        return v.encode("latin1")
    return v


def save_xvfb_pid(pid):
    _save_int(b"_XPRA_SERVER_PID", pid)

def get_xvfb_pid():
    return _get_int(b"_XPRA_SERVER_PID")


def save_uinput_id(uuid):
    _save_str(b"_XPRA_UINPUT_ID", (uuid or b"").decode())

#def get_uinput_id():
#    return _get_str("_XPRA_UINPUT_ID")


def validate_pixel_depth(pixel_depth, starting_desktop=False):
    try:
        pixel_depth = int(pixel_depth)
    except ValueError:
        raise InitException("invalid value '%s' for pixel depth, must be a number" % pixel_depth)
    if pixel_depth==0:
        pixel_depth = 24
    if pixel_depth not in (8, 16, 24, 30):
        raise InitException("invalid pixel depth: %s" % pixel_depth)
    if not starting_desktop and pixel_depth==8:
        raise InitException("pixel depth 8 is only supported in 'start-desktop' mode")
    return pixel_depth


def display_name_check(display_name):
    """ displays a warning
        when a low display number is specified """
    if not display_name.startswith(":"):
        return
    n = display_name[1:].split(".")[0]    #ie: ":0.0" -> "0"
    try:
        dno = int(n)
        if 0<=dno<10:
            warn("WARNING: low display number: %s" % dno)
            warn(" You are attempting to run the xpra server")
            warn(" against a low X11 display number: '%s'." % (display_name,))
            warn(" This is generally not what you want.")
            warn(" You should probably use a higher display number")
            warn(" just to avoid any confusion and this warning message.")
    except IOError:
        pass

def close_gtk_display():
    # Close our display(s) first, so the server dying won't kill us.
    # (if gtk has been loaded)
    gdk_mod = sys.modules.get("gtk.gdk") or sys.modules.get("gi.repository.Gdk")
    if gdk_mod and envbool("XPRA_CLOSE_GTK_DISPLAY", True):
        from xpra.gtk_common.gobject_compat import import_gdk, is_gtk3
        gdk = import_gdk()
        if is_gtk3():
            displays = gdk.DisplayManager.get().list_displays()
        else:
            displays = gdk.display_manager_get().list_displays()
        for d in displays:
            d.close()


def print_DE_warnings():
    de = os.environ.get("XDG_SESSION_DESKTOP") or os.environ.get("SESSION_DESKTOP")
    if not de:
        return
    log = get_util_logger()
    log.warn("Warning: xpra start from an existing '%s' desktop session", de)
    log.warn(" without using dbus-launch,")
    log.warn(" notifications forwarding may not work")
    log.warn(" try using a clean environment, a dedicated user,")
    log.warn(" or disable xpra's notifications option")


def sanitize_env():
    def unsetenv(*varnames):
        for x in varnames:
            try:
                del os.environ[x]
            except KeyError:
                pass
    #we don't want client apps to think these mean anything:
    #(if set, they belong to the desktop the server was started from)
    #TODO: simply whitelisting the env would be safer/better
    unsetenv("DESKTOP_SESSION",
             "GDMSESSION",
             "GNOME_DESKTOP_SESSION_ID",
             "SESSION_MANAGER",
             "XDG_VTNR",
             #we must keep this value on Debian / Ubuntu
             #to avoid breaking menu loading:
             #"XDG_MENU_PREFIX",
             "XDG_CURRENT_DESKTOP",
             "XDG_SESSION_DESKTOP",
             "XDG_SESSION_TYPE",
             "XDG_SESSION_ID",
             "XDG_SEAT",
             "XDG_VTNR",
             "QT_GRAPHICSSYSTEM_CHECKED",
             "CKCON_TTY",
             "CKCON_X11_DISPLAY",
             "CKCON_X11_DISPLAY_DEVICE",
             )

def configure_imsettings_env(input_method):
    im = (input_method or "").lower()
    if im in ("none", "no"):
        #the default: set DISABLE_IMSETTINGS=1, fallback to xim
        #that's because the 'ibus' 'immodule' breaks keyboard handling
        #unless its daemon is also running - and we don't know if it is..
        imsettings_env(True, "xim", "xim", "xim", "none", "@im=none")
    elif im=="keep":
        #do nothing and keep whatever is already set, hoping for the best
        pass
    elif im in ("xim", "IBus", "SCIM", "uim"):
        #ie: (False, "ibus", "ibus", "IBus", "@im=ibus")
        imsettings_env(True, im.lower(), im.lower(), im.lower(), im, "@im=%s" % im.lower())
    else:
        v = imsettings_env(True, im.lower(), im.lower(), im.lower(), im, "@im=%s" % im.lower())
        warn("using input method settings: %s" % str(v))
        warn("unknown input method specified: %s" % input_method)
        warn(" if it is correct, you may want to file a bug to get it recognized")

def imsettings_env(disabled, gtk_im_module, qt_im_module, clutter_im_module, imsettings_module, xmodifiers):
    #for more information, see imsettings:
    #https://code.google.com/p/imsettings/source/browse/trunk/README
    if disabled is True:
        os.environ["DISABLE_IMSETTINGS"] = "1"                  #this should override any XSETTINGS too
    elif disabled is False and ("DISABLE_IMSETTINGS" in os.environ):
        del os.environ["DISABLE_IMSETTINGS"]
    v = {
         "GTK_IM_MODULE"      : gtk_im_module,            #or "gtk-im-context-simple"?
         "QT_IM_MODULE"       : qt_im_module,             #or "simple"?
         "QT4_IM_MODULE"      : qt_im_module,
         "CLUTTER_IM_MODULE"  : clutter_im_module,
         "IMSETTINGS_MODULE"  : imsettings_module,        #or "xim"?
         "XMODIFIERS"         : xmodifiers,
         #not really sure what to do with those:
         #"IMSETTINGS_DISABLE_DESKTOP_CHECK"   : "true",   #
         #"IMSETTINGS_INTEGRATE_DESKTOP" : "no"}           #we're not a real desktop
        }
    os.environ.update(v)
    return v

def create_runtime_dir(xrd, uid, gid):
    if not POSIX or OSX or getuid()!=0 or (uid==0 and gid==0):
        return
    #workarounds:
    #* some distros don't set a correct value,
    #* or they don't create the directory for us,
    #* or pam_open is going to create the directory but needs time to do so..
    if xrd and xrd.endswith("/user/0"):
        #don't keep root's directory, as this would not work:
        xrd = None
    if not xrd:
        #find the "/run/user" directory:
        run_user = "/run/user"
        if not os.path.exists(run_user):
            run_user = "/var/run/user"
        if os.path.exists(run_user):
            xrd = os.path.join(run_user, str(uid))
    if not xrd:
        return None
    if not os.path.exists(xrd):
        os.mkdir(xrd, 0o700)
        os.lchown(xrd, uid, gid)
    xpra_dir = os.path.join(xrd, "xpra")
    if not os.path.exists(xpra_dir):
        os.mkdir(xpra_dir, 0o700)
        os.lchown(xpra_dir, uid, gid)
    return xrd


def guess_xpra_display(socket_dir, socket_dirs):
    dotxpra = DotXpra(socket_dir, socket_dirs)
    results = dotxpra.sockets()
    live = [display for state, display in results if state==DotXpra.LIVE]
    if not live:
        raise InitException("no existing xpra servers found")
    if len(live)>1:
        raise InitException("too many existing xpra servers found, cannot guess which one to use")
    return live[0]


def show_encoding_help(opts):
    #avoid errors and warnings:
    opts.encoding = ""
    opts.clipboard = False
    opts.notifications = False
    print("xpra server supports the following encodings:")
    print("(please wait, encoder initialization may take a few seconds)")
    #disable info logging which would be confusing here
    from xpra.log import get_all_loggers, set_default_level
    import logging
    set_default_level(logging.WARN)
    logging.root.setLevel(logging.WARN)
    for x in get_all_loggers():
        x.logger.setLevel(logging.WARN)
    from xpra.server.server_base import ServerBase
    sb = ServerBase()
    sb.init(opts)
    from xpra.codecs.codec_constants import PREFERED_ENCODING_ORDER, HELP_ORDER
    if "help" in opts.encodings:
        sb.allowed_encodings = PREFERED_ENCODING_ORDER
    from xpra.codecs.video_helper import getVideoHelper
    getVideoHelper().init()
    sb.init_encodings()
    from xpra.codecs.loader import encoding_help
    for e in (x for x in HELP_ORDER if x in sb.encodings):
        print(" * %s" % encoding_help(e))
    return 0


def set_server_features(opts):
    def b(v):
        return str(v).lower() not in FALSE_OPTIONS
    #turn off some server mixins:
    from xpra.server import server_features
    impwarned = []
    def impcheck(*modules):
        for mod in modules:
            try:
                __import__("xpra.%s" % mod, {}, {}, [])
            except ImportError:
                if mod not in impwarned:
                    impwarned.append(mod)
                    log = get_util_logger()
                    log.warn("Warning: missing %s module", mod)
                return False
        return True
    server_features.notifications   = opts.notifications and impcheck("notifications")
    server_features.webcam          = b(opts.webcam) and impcheck("codecs")
    server_features.clipboard       = b(opts.clipboard) and impcheck("clipboard")
    server_features.audio           = (b(opts.speaker) or b(opts.microphone)) and impcheck("sound")
    server_features.av_sync         = server_features.audio and b(opts.av_sync)
    server_features.fileprint       = b(opts.printing) or b(opts.file_transfer)
    server_features.mmap            = b(opts.mmap)
    server_features.input_devices   = not opts.readonly and impcheck("keyboard")
    server_features.commands        = impcheck("server.control_command")
    server_features.dbus            = opts.dbus_proxy and impcheck("dbus")
    server_features.encoding        = impcheck("codecs")
    server_features.logging         = b(opts.remote_logging)
    #server_features.network_state   = ??
    server_features.display         = opts.windows
    server_features.windows         = opts.windows and impcheck("codecs")
    server_features.rfb             = b(opts.rfb_upgrade) and impcheck("server.rfb")


def make_desktop_server(clobber):
    from xpra.x11.desktop_server import XpraDesktopServer
    return XpraDesktopServer(clobber)

def make_server(clobber):
    from xpra.x11.server import XpraServer
    return XpraServer(clobber)

def make_shadow_server():
    from xpra.platform.shadow_server import ShadowServer
    return ShadowServer()

def make_proxy_server():
    from xpra.server.proxy.proxy_server import ProxyServer
    return ProxyServer()


def hosts(host_str):
    if host_str=="*":
        from xpra.server.socket_util import has_dual_stack
        if has_dual_stack():
            #IPv6 will also listen for IPv4:
            return ["::"]
        #no dual stack, so we have to listen on both IPv4 and IPv6 explicitly:
        return ["0.0.0.0", "::"]
    return [host_str]

def add_mdns(mdns_recs, socktype, host_str, port):
    recs = mdns_recs.setdefault(socktype.lower(), [])
    for host in hosts(host_str):
        rec = (host, port)
        if rec not in recs:
            recs.append(rec)

def create_sockets(opts, error_cb):
    from xpra.server.socket_util import (
        parse_bind_ip, parse_bind_vsock, get_network_logger, setup_tcp_socket, setup_udp_socket, setup_vsock_socket,
        )
    log = get_network_logger()

    bind_tcp = parse_bind_ip(opts.bind_tcp)
    bind_udp = parse_bind_ip(opts.bind_udp)
    bind_ssl = parse_bind_ip(opts.bind_ssl)
    bind_ssh = parse_bind_ip(opts.bind_ssh)
    bind_ws  = parse_bind_ip(opts.bind_ws)
    bind_wss = parse_bind_ip(opts.bind_wss)
    bind_rfb = parse_bind_ip(opts.bind_rfb, 5900)
    bind_vsock = parse_bind_vsock(opts.bind_vsock)

    mdns_recs = {}
    sockets = []

    rfb_upgrades = int(opts.rfb_upgrade)>0
    #SSL sockets:
    wrap_socket_fn = None
    need_ssl = False
    ssl_opt = opts.ssl.lower()
    if ssl_opt in TRUE_OPTIONS or bind_ssl or bind_wss:
        need_ssl = True
    if opts.bind_tcp or opts.bind_ws:
        if ssl_opt=="auto" and opts.ssl_cert:
            need_ssl = True
        elif ssl_opt=="tcp" and opts.bind_tcp:
            need_ssl = True
        elif ssl_opt=="www":
            need_ssl = True
    if need_ssl:
        from xpra.scripts.main import ssl_wrap_socket_fn
        try:
            wrap_socket_fn = ssl_wrap_socket_fn(opts, server_side=True)
            log("wrap_socket_fn=%s", wrap_socket_fn)
        except Exception as e:
            log("SSL error", exc_info=True)
            cpaths = csv("'%s'" % x for x in (opts.ssl_cert, opts.ssl_key) if x)
            raise InitException("cannot create SSL socket, check your certificate paths (%s): %s" % (cpaths, e))

    min_port = int(opts.min_port)
    def add_tcp_socket(socktype, host_str, iport):
        if iport!=0 and iport<min_port:
            error_cb("invalid %s port number %i (minimum value is %i)" % (socktype, iport, min_port))
        for host in hosts(host_str):
            socket = setup_tcp_socket(host, iport, socktype)
            host, iport = socket[2]
            sockets.append(socket)
            add_mdns(mdns_recs, socktype, host, iport)
    def add_udp_socket(socktype, host_str, iport):
        if iport!=0 and iport<min_port:
            error_cb("invalid %s port number %i (minimum value is %i)" % (socktype, iport, min_port))
        for host in hosts(host_str):
            socket = setup_udp_socket(host, iport, socktype)
            host, iport = socket[2]
            sockets.append(socket)
            add_mdns(mdns_recs, socktype, host, iport)
    # Initialize the TCP sockets before the display,
    # That way, errors won't make us kill the Xvfb
    # (which may not be ours to kill at that point)
    ws_upgrades = opts.html and (os.path.isabs(opts.html) or opts.html.lower() in list(TRUE_OPTIONS)+["auto"])
    ssh_upgrades = opts.ssh_upgrade
    if ssh_upgrades:
        try:
            from xpra.net.ssh import nogssapi_context
            with nogssapi_context():
                import paramiko
            assert paramiko
        except ImportError as e:
            from xpra.log import Logger
            sshlog = Logger("ssh")
            sshlog("import paramiko", exc_info=True)
            sshlog.error("Error: cannot enable SSH socket upgrades:")
            sshlog.error(" %s", e)
    log("setting up SSL sockets: %s", csv(bind_ssl))
    for host, iport in bind_ssl:
        add_tcp_socket("ssl", host, iport)
        if ws_upgrades:
            add_tcp_socket("wss", host, iport)
    log("setting up SSH sockets: %s", csv(bind_ssh))
    for host, iport in bind_ssh:
        add_tcp_socket("ssh", host, iport)
    log("setting up https / wss (secure websockets): %s", csv(bind_wss))
    for host, iport in bind_wss:
        add_tcp_socket("wss", host, iport)
    tcp_ssl = ssl_opt in TRUE_OPTIONS or (ssl_opt=="auto" and opts.ssl_cert)
    log("setting up TCP sockets: %s", csv(bind_tcp))
    for host, iport in bind_tcp:
        add_tcp_socket("tcp", host, iport)
        if tcp_ssl:
            add_mdns(mdns_recs, "ssl", host, iport)
        if ws_upgrades:
            add_mdns(mdns_recs, "ws", host, iport)
        if ws_upgrades and tcp_ssl:
            add_mdns(mdns_recs, "wss", host, iport)
        if ssh_upgrades:
            add_mdns(mdns_recs, "ssh", host, iport)
        if rfb_upgrades:
            add_mdns(mdns_recs, "rfb", host, iport)
    log("setting up UDP sockets: %s", csv(bind_udp))
    for host, iport in bind_udp:
        add_udp_socket("udp", host, iport)
    log("setting up http / ws (websockets): %s", csv(bind_ws))
    for host, iport in bind_ws:
        add_tcp_socket("ws", host, iport)
        if tcp_ssl:
            add_mdns(mdns_recs, "wss", host, iport)
    log("setting up rfb sockets: %s", csv(bind_rfb))
    for host, iport in bind_rfb:
        add_tcp_socket("rfb", host, iport)
        add_mdns(mdns_recs, "rfb", host, iport)
    log("setting up vsock sockets: %s", csv(bind_vsock))
    for cid, iport in bind_vsock:
        socket = setup_vsock_socket(cid, iport)
        sockets.append(socket)
        #add_mdns(mdns_recs, "vsock", str(cid), iport)

    # systemd socket activation:
    if POSIX:
        try:
            from xpra.platform.xposix.sd_listen import get_sd_listen_sockets
        except ImportError:
            pass
        else:
            sd_sockets = get_sd_listen_sockets()
            log("systemd sockets: %s", sd_sockets)
            for stype, socket, addr in sd_sockets:
                sockets.append((stype, socket, addr))
                log("%s : %s", (stype, [addr]), socket)
                if stype=="tcp":
                    host, iport = addr
                    add_mdns(mdns_recs, "tcp", host, iport)
    return sockets, mdns_recs, wrap_socket_fn

def run_server(error_cb, opts, mode, xpra_file, extra_args, desktop_display=None):
    #add finally hook to ensure we will run the cleanups
    #even if we exit because of an exception:
    try:
        return do_run_server(error_cb, opts, mode, xpra_file, extra_args, desktop_display)
    finally:
        run_cleanups()
        import gc
        gc.collect()


def do_run_server(error_cb, opts, mode, xpra_file, extra_args, desktop_display=None):
    assert mode in (
        "start", "start-desktop",
        "upgrade", "upgrade-desktop",
        "shadow", "proxy",
        )

    try:
        cwd = os.getcwd()
    except OSError:
        cwd = os.path.expanduser("~")
        warn("current working directory does not exist, using '%s'\n" % cwd)
    validate_encryption(opts)
    if opts.encoding=="help" or "help" in opts.encodings:
        return show_encoding_help(opts)

    #remove anything pointing to dbus from the current env
    #(so we only detect a dbus instance started by pam,
    # and override everything else)
    for k in os.environ.keys():
        if k.startswith("DBUS_"):
            del os.environ[k]

    starting  = mode == "start"
    starting_desktop = mode == "start-desktop"
    upgrading = mode == "upgrade"
    upgrading_desktop = mode == "upgrade-desktop"
    shadowing = mode == "shadow"
    proxying  = mode == "proxy"
    clobber   = upgrading or upgrading_desktop or opts.use_display
    start_vfb = not (shadowing or proxying or clobber)

    if proxying or upgrading or upgrading_desktop:
        #when proxying or upgrading, don't exec any plain start commands:
        opts.start = opts.start_child = []
    elif opts.exit_with_children:
        assert opts.start_child, "exit-with-children was specified but start-child is missing!"
    elif opts.start_child:
        warn("Warning: the 'start-child' option is used,")
        warn(" but 'exit-with-children' is not enabled,")
        warn(" use 'start' instead")

    if opts.bind_rfb and (proxying or starting):
        get_util_logger().warn("Warning: bind-rfb sockets cannot be used with '%s' mode" % mode)
        opts.bind_rfb = ""

    if not shadowing and not starting_desktop:
        opts.rfb_upgrade = 0

    if upgrading or upgrading_desktop or shadowing:
        #there should already be one running
        opts.pulseaudio = False

    #get the display name:
    if shadowing and not extra_args:
        if WIN32 or OSX:
            #just a virtual name for the only display available:
            display_name = ":0"
        else:
            from xpra.scripts.main import guess_X11_display
            dotxpra = DotXpra(opts.socket_dir, opts.socket_dirs)
            display_name = guess_X11_display(dotxpra, desktop_display)
    elif (upgrading or upgrading_desktop) and not extra_args:
        display_name = guess_xpra_display(opts.socket_dir, opts.socket_dirs)
    else:
        if len(extra_args) > 1:
            error_cb("too many extra arguments (%i): only expected a display number" % len(extra_args))
        if len(extra_args) == 1:
            display_name = extra_args[0]
            if not shadowing and not proxying and not opts.use_display:
                display_name_check(display_name)
        else:
            if proxying:
                #find a free display number:
                dotxpra = DotXpra(opts.socket_dir, opts.socket_dirs)
                all_displays = dotxpra.sockets()
                #ie: [("LIVE", ":100"), ("LIVE", ":200"), ...]
                displays = [v[1] for v in all_displays]
                display_name = None
                for x in range(1000, 20000):
                    v = ":%s" % x
                    if v not in displays:
                        display_name = v
                        break
                if not display_name:
                    error_cb("you must specify a free virtual display name to use with the proxy server")
            elif opts.use_display:
                #only use automatic guess for xpra displays and not X11 displays:
                display_name = guess_xpra_display(opts.socket_dir, opts.socket_dirs)
            else:
                # We will try to find one automaticaly
                # Use the temporary magic value 'S' as marker:
                display_name = 'S' + str(os.getpid())

    if not (shadowing or proxying or upgrading or upgrading_desktop) and \
    opts.exit_with_children and not opts.start_child:
        error_cb("--exit-with-children specified without any children to spawn; exiting immediately")

    atexit.register(run_cleanups)

    # Generate the script text now, because os.getcwd() will
    # change if/when we daemonize:
    from xpra.server.server_util import (
        xpra_runner_shell_script,
        write_runner_shell_scripts,
        write_pidfile,
        find_log_dir,
        create_input_devices,
        )
    script = xpra_runner_shell_script(xpra_file, cwd, opts.socket_dir)

    uid = int(opts.uid)
    gid = int(opts.gid)
    username = get_username_for_uid(uid)
    home = get_home_for_uid(uid)
    xauth_data = None
    if start_vfb:
        xauth_data = get_hex_uuid()
    ROOT = POSIX and getuid()==0

    protected_fds = []
    protected_env = {}
    stdout = sys.stdout
    stderr = sys.stderr
    # Daemonize:
    if POSIX and opts.daemon:
        #daemonize will chdir to "/", so try to use an absolute path:
        if opts.password_file:
            opts.password_file = tuple(os.path.abspath(x) for x in opts.password_file)
        from xpra.server.server_util import daemonize
        daemonize()

    displayfd = 0
    if POSIX and opts.displayfd:
        try:
            displayfd = int(opts.displayfd)
            if displayfd>0:
                protected_fds.append(displayfd)
        except ValueError as e:
            stderr.write("Error: invalid displayfd '%s':\n" % opts.displayfd)
            stderr.write(" %s\n" % e)
            del e

    # if pam is present, try to create a new session:
    pam = None
    PAM_OPEN = POSIX and envbool("XPRA_PAM_OPEN", ROOT and uid!=0)
    if PAM_OPEN:
        try:
            from xpra.server.pam import pam_session #@UnresolvedImport
        except ImportError as e:
            stderr.write("Error: failed to import pam module\n")
            stderr.write(" %s" % e)
            del e
            PAM_OPEN = False
    if PAM_OPEN:
        fdc = FDChangeCaptureContext()
        with fdc:
            pam = pam_session(username)
            env = {
                   #"XDG_SEAT"               : "seat1",
                   #"XDG_VTNR"               : "0",
                   "XDG_SESSION_TYPE"       : "x11",
                   #"XDG_SESSION_CLASS"      : "user",
                   "XDG_SESSION_DESKTOP"    : "xpra",
                   }
            #maybe we should just bail out instead?
            if pam.start():
                pam.set_env(env)
                items = {}
                if display_name.startswith(":"):
                    items["XDISPLAY"] = display_name
                if xauth_data:
                    items["XAUTHDATA"] = xauth_data
                pam.set_items(items)
                if pam.open():
                    #we can't close it, because we're not going to be root any more,
                    #but since we're the process leader for the session,
                    #terminating will also close the session
                    #add_cleanup(pam.close)
                    protected_env = pam.get_envlist()
                    os.environ.update(protected_env)
        #closing the pam fd causes the session to be closed,
        #and we don't want that!
        protected_fds += fdc.get_new_fds()

    #get XDG_RUNTIME_DIR from env options,
    #which may not be have updated os.environ yet when running as root with "--uid="
    xrd = os.path.abspath(parse_env(opts.env).get("XDG_RUNTIME_DIR", ""))
    if ROOT and (uid>0 or gid>0):
        #we're going to chown the directory if we create it,
        #ensure this cannot be abused, only use "safe" paths:
        if not any(x for x in ("/run/user/%i" % uid, "/tmp", "/var/tmp") if xrd.startswith(x)):
            xrd = ""
        #these paths could cause problems if we were to create and chown them:
        if xrd.startswith("/tmp/.X11-unix") or xrd.startswith("/tmp/.XIM-unix"):
            xrd = ""
    if not xrd:
        xrd = os.environ.get("XDG_RUNTIME_DIR")
    xrd = create_runtime_dir(xrd, uid, gid)
    if xrd:
        #this may override the value we get from pam
        #with the value supplied by the user:
        protected_env["XDG_RUNTIME_DIR"] = xrd

    if opts.pidfile:
        write_pidfile(opts.pidfile, uid, gid)

    if POSIX and not ROOT:
        # Write out a shell-script so that we can start our proxy in a clean
        # environment:
        write_runner_shell_scripts(script)

    if start_vfb or opts.daemon:
        #we will probably need a log dir
        #either for the vfb, or for our own log file
        log_dir = opts.log_dir or ""
        if not log_dir or log_dir.lower()=="auto":
            log_dir = find_log_dir(username, uid=uid, gid=gid)
            if not log_dir:
                raise InitException("cannot find or create a logging directory")
        #expose the log-dir as "XPRA_LOG_DIR",
        #this is used by Xdummy for the Xorg log file
        if "XPRA_LOG_DIR" not in os.environ:
            os.environ["XPRA_LOG_DIR"] = log_dir

        if opts.daemon:
            from xpra.server.server_util import select_log_file, open_log_file, redirect_std_to_log
            log_filename0 = osexpand(select_log_file(log_dir, opts.log_file, display_name), username, uid, gid)
            logfd = open_log_file(log_filename0)
            if ROOT and (uid>0 or gid>0):
                try:
                    os.fchown(logfd, uid, gid)
                except:
                    pass
            stdout, stderr = redirect_std_to_log(logfd, *protected_fds)
            try:
                stderr.write("Entering daemon mode; "
                         + "any further errors will be reported to:\n"
                         + ("  %s\n" % log_filename0))
            except IOError:
                #we tried our best, logging another error won't help
                pass

    #warn early about this:
    if (starting or starting_desktop) and desktop_display and opts.notifications and not opts.dbus_launch:
        print_DE_warnings()

    from xpra.log import Logger
    log = Logger("server")
    sockets, mdns_recs, wrap_socket_fn = create_sockets(opts, error_cb)

    sanitize_env()
    if POSIX:
        if xrd:
            os.environ["XDG_RUNTIME_DIR"] = xrd
        os.environ["XDG_SESSION_TYPE"] = "x11"
        if not starting_desktop:
            os.environ["XDG_CURRENT_DESKTOP"] = opts.wm_name
        configure_imsettings_env(opts.input_method)
    if display_name[0] != 'S':
        os.environ["DISPLAY"] = display_name
        os.environ["CKCON_X11_DISPLAY"] = display_name
    else:
        try:
            del os.environ["DISPLAY"]
        except KeyError:
            pass
    os.environ.update(protected_env)
    log("env=%s", os.environ)

    UINPUT_UUID_LEN = 12
    UINPUT_UUID_MIN_LEN = 12
    UINPUT_UUID_MAX_LEN = 32
    # Start the Xvfb server first to get the display_name if needed
    odisplay_name = display_name
    xvfb = None
    xvfb_pid = None
    uinput_uuid = None
    if start_vfb:
        assert not proxying and xauth_data
        pixel_depth = validate_pixel_depth(opts.pixel_depth, starting_desktop)
        from xpra.x11.vfb_util import start_Xvfb, check_xvfb_process
        from xpra.server.server_util import has_uinput
        uinput_uuid = None
        if has_uinput() and opts.input_devices.lower() in ("uinput", "auto") and not shadowing:
            from xpra.os_util import get_rand_chars
            uinput_uuid = get_rand_chars(UINPUT_UUID_LEN)
        xvfb, display_name, cleanups = start_Xvfb(opts.xvfb, pixel_depth, display_name, cwd, uid, gid, username, xauth_data, uinput_uuid)
        for f in cleanups:
            add_cleanup(f)
        xvfb_pid = xvfb.pid
        #always update as we may now have the "real" display name:
        os.environ["DISPLAY"] = display_name
        os.environ["CKCON_X11_DISPLAY"] = display_name
        os.environ.update(protected_env)
        if display_name!=odisplay_name and pam:
            pam.set_items({"XDISPLAY" : display_name})

        def check_xvfb():
            return check_xvfb_process(xvfb)
    else:
        if POSIX and clobber:
            #if we're meant to be using a private XAUTHORITY file,
            #make sure to point to it:
            from xpra.x11.vfb_util import get_xauthority_path
            xauthority = get_xauthority_path(display_name, username, uid, gid)
            if os.path.exists(xauthority):
                os.environ["XAUTHORITY"] = xauthority
        def check_xvfb():
            return True

    if POSIX and not OSX and displayfd>0:
        from xpra.platform.displayfd import write_displayfd
        try:
            display_no = display_name[1:]
            #ensure it is a string containing the number:
            display_no = str(int(display_no))
            log("writing display_no='%s' to displayfd=%i", display_no, displayfd)
            assert write_displayfd(displayfd, display_no), "timeout"
        except Exception as e:
            log.error("write_displayfd failed", exc_info=True)
            log.error("Error: failed to write '%s' to fd=%s", display_name, displayfd)
            log.error(" %s", str(e) or type(e))
            del e
        try:
            os.fsync(displayfd)
        except (IOError, OSError):
            log("os.fsync(%i)", displayfd, exc_info=True)
        if displayfd>2:
            try:
                os.close(displayfd)
            except (IOError, OSError):
                log("os.close(%i)", displayfd, exc_info=True)

    if not proxying:
        add_cleanup(close_gtk_display)

    if opts.daemon:
        def noerr(fn, *args):
            try:
                fn(*args)
            except Exception:
                pass
        log_filename1 = osexpand(select_log_file(log_dir, opts.log_file, display_name), username, uid, gid)
        if log_filename0 != log_filename1:
            # we now have the correct log filename, so use it:
            os.rename(log_filename0, log_filename1)
            if odisplay_name!=display_name:
                #this may be used by scripts, let's try not to change it:
                noerr(stderr.write, "Actual display used: %s\n" % display_name)
            noerr(stderr.write, "Actual log file name is now: %s\n" % log_filename1)
            noerr(stderr.flush)
        noerr(stdout.close)
        noerr(stderr.close)
    #we should not be using stdout or stderr from this point:
    del stdout
    del stderr

    if not check_xvfb():
        #xvfb problem: exit now
        return  1

    #create devices for vfb if needed:
    devices = {}
    if not start_vfb and not proxying and not shadowing:
        #try to find the existing uinput uuid:
        #use a subprocess to avoid polluting our current process
        #with X11 connections before we get a chance to change uid
        prop = "_XPRA_UINPUT_ID"
        cmd = ["xprop", "-display", display_name, "-root", prop]
        log("looking for '%s' on display '%s' with XAUTHORITY='%s'", prop, display_name, os.environ.get("XAUTHORITY"))
        try:
            code, out, err = get_status_output(cmd)
        except Exception as e:
            log("failed to get existing uinput id: %s", e)
            del e
        else:
            log("Popen(%s)=%s", cmd, (code, out, err))
            if code==0 and out.find("=")>0:
                uinput_uuid = out.split("=", 1)[1]
                log("raw uinput uuid=%s", uinput_uuid)
                uinput_uuid = strtobytes(uinput_uuid.strip('\n\r"\\ '))
                if uinput_uuid:
                    if len(uinput_uuid)>UINPUT_UUID_MAX_LEN or len(uinput_uuid)<UINPUT_UUID_MIN_LEN:
                        log.warn("Warning: ignoring invalid uinput id:")
                        log.warn(" '%s'", uinput_uuid)
                        uinput_uuid = None
                    else:
                        log.info("retrieved existing uinput id: %s", bytestostr(uinput_uuid))
    if uinput_uuid:
        devices = create_input_devices(uinput_uuid, uid)

    if ROOT and (uid!=0 or gid!=0):
        log("root: switching to uid=%i, gid=%i", uid, gid)
        setuidgid(uid, gid)
        os.environ.update({
            "HOME"      : home,
            "USER"      : username,
            "LOGNAME"   : username,
            })
        shell = get_shell_for_uid(uid)
        if shell:
            os.environ["SHELL"] = shell
        #now we've changed uid, it is safe to honour all the env updates:
        configure_env(opts.env)
        os.environ.update(protected_env)

    if opts.chdir:
        os.chdir(opts.chdir)

    dbus_pid, dbus_env = 0, {}
    if not shadowing and POSIX and not clobber:
        no_gtk()
        assert starting or starting_desktop or proxying
        from xpra.server.dbus.dbus_start import start_dbus
        dbus_pid, dbus_env = start_dbus(opts.dbus_launch)
        if dbus_env:
            os.environ.update(dbus_env)

    display = None
    if not proxying:
        if POSIX and not OSX:
            no_gtk()
            if starting or starting_desktop or shadowing:
                #check that we can access the X11 display:
                from xpra.x11.vfb_util import verify_display_ready
                if not verify_display_ready(xvfb, display_name, shadowing):
                    return 1
                from xpra.x11.gtk_x11.gdk_display_source import verify_gdk_display
                display = verify_gdk_display(display_name)
                if not display:
                    return 1
        #on win32, this ensures that we get the correct screen size to shadow:
        from xpra.platform.gui import init as gui_init
        gui_init()

    #setup unix domain socket:
    from xpra.server.socket_util import get_network_logger, setup_local_sockets
    netlog = get_network_logger()
    if not opts.socket_dir and not opts.socket_dirs:
        #we always need at least one valid socket dir
        from xpra.platform.paths import get_socket_dirs
        opts.socket_dirs = get_socket_dirs()
    local_sockets = setup_local_sockets(opts.bind,
                                        opts.socket_dir, opts.socket_dirs,
                                        display_name, clobber,
                                        opts.mmap_group, opts.socket_permissions,
                                        username, uid, gid)
    netlog("setting up local sockets: %s", local_sockets)
    ssh_port = get_ssh_port()
    ssh_access = ssh_port>0 and opts.ssh.lower().strip() not in FALSE_OPTIONS
    for rec, cleanup_socket in local_sockets:
        socktype, socket, sockpath = rec
        #ie: ("unix-domain", sock, sockpath), cleanup_socket
        sockets.append(rec)
        netlog("%s %s : %s", socktype, sockpath, socket)
        add_cleanup(cleanup_socket)
        if opts.mdns and ssh_access:
            netlog("ssh %s:%s : %s", "", ssh_port, socket)
            add_mdns(mdns_recs, "ssh", "", ssh_port)
    if POSIX and (starting or upgrading or starting_desktop or upgrading_desktop):
        #all unix domain sockets:
        ud_paths = [sockpath for (stype, _, sockpath), _ in local_sockets if stype=="unix-domain"]
        if ud_paths:
            #choose one so our xdg-open override script can use to talk back to us:
            if opts.forward_xdg_open:
                for x in ("/usr/libexec/xpra", "/usr/lib/xpra"):
                    xdg_override = os.path.join(x, "xdg-open")
                    if os.path.exists(xdg_override):
                        os.environ["PATH"] = x+os.pathsep+os.environ.get("PATH", "")
                        os.environ["XPRA_SERVER_SOCKET"] = ud_paths[0]
                        break
        else:
            log.warn("Warning: no local server sockets,")
            if opts.forward_xdg_open:
                log.warn(" forward-xdg-open cannot be enabled")
            log.warn(" non-embedded ssh connections will not be available")

    set_server_features(opts)

    if not proxying and POSIX:
        if not check_xvfb():
            return  1
        assert starting or starting_desktop or upgrading or upgrading_desktop
        from xpra.x11.gtk_x11.gdk_display_source import init_gdk_display_source, close_gdk_display_source
        init_gdk_display_source()
        #(now we can access the X11 server)

    if shadowing:
        app = make_shadow_server()
    elif proxying:
        app = make_proxy_server()
    else:
        save_uinput_id(uinput_uuid)
        if starting or upgrading:
            app = make_server(clobber)
        else:
            assert starting_desktop or upgrading_desktop
            app = make_desktop_server(clobber)
        app.init_virtual_devices(devices)

    try:
        app._ssl_wrap_socket = wrap_socket_fn
        app.init_dbus(dbus_pid, dbus_env)
        if xvfb_pid or clobber:
            app.init_display_pid(xvfb_pid)
        app.original_desktop_display = desktop_display
        app.exec_cwd = opts.chdir or cwd
        app.init(opts)
        if not app.server_ready():
            return 1
        app.server_init()
        app.setup()
    except InitException as e:
        log.error("xpra server initialization error:")
        log.error(" %s", e)
        app.cleanup()
        return 1
    except Exception as e:
        log.error("Error: cannot start the %s server", app.session_type, exc_info=True)
        log.error(str(e))
        log.info("")
        app.cleanup()
        return 1

    #publish mdns records:
    if opts.mdns:
        from xpra.platform.info import get_username
        from xpra.server.socket_util import mdns_publish
        mdns_info = {
                     "display"  : display_name,
                     "username" : get_username(),
                     "uuid"     : app.uuid,
                     "platform" : sys.platform,
                     "type"     : app.session_type,
                     }
        MDNS_EXPOSE_NAME = envbool("XPRA_MDNS_EXPOSE_NAME", True)
        if MDNS_EXPOSE_NAME and app.session_name:
            mdns_info["name"] = app.session_name
        for mdns_mode, listen_on in mdns_recs.items():
            mdns_publish(display_name, mdns_mode, listen_on, mdns_info)

    del opts

    log("%s(%s)", app.init_sockets, sockets)
    app.init_sockets(sockets)
    log("%s(%s)", app.init_when_ready, _when_ready)
    app.init_when_ready(_when_ready)

    try:
        log("running %s", app.run)
        r = app.run()
        log("%s()=%s", app.run, r)
    except KeyboardInterrupt:
        log.info("stopping on KeyboardInterrupt")
        app.cleanup()
        return 0
    except Exception:
        log.error("server error", exc_info=True)
        app.cleanup()
        return -128
    else:
        if r>0:
            r = 0
    return r
