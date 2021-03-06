# This file is part of Xpra.
# Copyright (C) 2010-2014 Antoine Martin <antoine@devloop.org.uk>
# Xpra is released under the terms of the GNU GPL v2, or, at your option, any
# later version. See the file COPYING for details.

%define version 0.14.37
%{!?python_sitearch: %global python_sitearch %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib(1))")}
%if ! %{defined build_no}
%define build_no 0
%endif
%define include_egg 1
%define old_xdg 0

#some of these dependencies may get turned off (empty) on some platforms:
%define dummy --with-Xdummy
%define requires_lzo , python-lzo
%define requires_lz4 , python-lz4
%define requires_rencode , python-rencode
%define requires_pil , python-pillow
#OpenGL bits:
%define requires_opengl , PyOpenGL, PyOpenGL-accelerate, pygtkglext, numpy
#Anything extra (distro specific):
%define requires_extra %{nil}
%define requires_sound , gstreamer, gstreamer-plugins-base, gstreamer-plugins-good, gstreamer-python, pulseaudio, pulseaudio-utils
#This would add support for mp3, but is not in the default repositories:
#gstreamer-plugins-ugly
%define requires_xim , gtk2-immodule-xim

#Vfb (Xvfb or Xdummy):
%define xorg_deps xorg-x11-server-utils, xorg-x11-drv-dummy, xorg-x11-drv-void, xorg-x11-xauth
%define libvpx libvpx
#we cannot depend on 'avahi-ui-tools' which we need for mdns support
#(it provides the avahi python bindings)
#because Fedora and CentOS bring in some insane dependencies with it (vnc)
%define mdns_deps python-netifaces

# any centos / rhel supported:
%if 0%{?el5}%{?el6}%{?el7}
#not available:
%define requires_lzo %{nil}
#do not disable sound support, but do not declare deps for it either
#(so it can be installed if desired):
%define no_sound 0
%define requires_sound %{nil}
%endif

%if 0%{?el6}
#distro version is too old replace with our private libraries
%define libvpx libvpx-xpra
#only v6.4 onwards have Xdummy support:
%if %(egrep -q 'release 6.0|release 6.1|release 6.2|release 6.3' /etc/redhat-release && echo 1 || echo 0)
%define dummy --without-Xdummy
%else
%define dummy --with-Xdummy
%endif
#don't try to support opengl with anything older than 6.5:
%if %(egrep -q 'release 6.0|release 6.1|release 6.2|release 6.3|release 6.4' /etc/redhat-release && echo 1 || echo 0)
%define requires_opengl %{nil}
%endif
%endif

%if 0%{?el5}
#distro version is too old replace with our private libraries
%define libvpx libvpx-xpra
#does not build against python24:
%define requires_lz4 %{nil}
%define dummy --without-Xdummy
#not available:
%define requires_pil , python-imaging
%define requires_rencode %{nil}
%define requires_opengl %{nil}
%define requires_xim %{nil}
%define no_sound 1
%define no_pulseaudio 1
%define old_xdg 1
#uuidgen is in e2fsprogs! (no we don't do any fs stuff)
%define requires_extra , e2fsprogs, python-ctypes
%define xorg_deps xorg-x11-server-utils, xorg-x11-server-Xvfb, xorg-x11-xauth, libXfont
%define include_egg 0
%endif

%if 0%{?fedora} >= 22
#fedora 22 removed the void driver
%define xorg_deps xorg-x11-server-utils, xorg-x11-drv-dummy, xorg-x11-xauth
%endif
#Fedora 22+ have PyOpenGL... and they include PyOpenGL-accelerate bindings. PITA for us.
%if 0%{?fedora} >= 22
%define requires_opengl , PyOpenGL, pygtkglext, numpy
%endif


%if 0%{?no_sound}
%define requires_sound %{nil}
%endif


Name: xpra
Version: %{version}
Release: %{build_no}%{dist}
Summary: Xpra gives you "persistent remote applications" for X.

Group: Networking
License: GPL
URL: http://xpra.org/
Packager: Antoine Martin <antoine@devloop.org.uk>
Vendor: http://xpra.org/

Source: xpra-%{version}.tar.bz2
BuildRoot: %{_tmppath}/%{name}-%{version}-root

Requires(pre): shadow-utils
Requires: python %{requires_extra} %{requires_opengl} %{requires_sound} %{requires_lz4} %{requires_lzo} %{requires_rencode} %{requires_pil} %{requires_xim}
Requires: pygtk2
Requires: python-imaging
Requires: dbus-python
Requires: python-crypto
Requires: %{mdns_deps}
Requires: libfakeXinerama
Requires: %{xorg_deps}
Requires: %{libvpx}
Requires: x264-xpra
Requires: ffmpeg-xpra
%if 0%{?fedora}
Requires: libwebp
%endif

#v0.15.x onwards splits into two packages:
Conflicts: xpra-common

BuildRequires: pkgconfig
BuildRequires: Cython
BuildRequires: pygtk2-devel
BuildRequires: python, python-setuptools
BuildRequires: pygobject2-devel
BuildRequires: libxkbfile-devel
#used for locating the Xorg binary:
Requires: which
BuildRequires: libXtst-devel
BuildRequires: libXfixes-devel
BuildRequires: libXcomposite-devel
BuildRequires: libXdamage-devel
BuildRequires: libXrandr-devel
BuildRequires: %{libvpx}-devel
BuildRequires: x264-xpra-devel
BuildRequires: ffmpeg-xpra-devel
BuildRequires: desktop-file-utils
%if 0%{?fedora}
BuildRequires: libwebp-devel
%endif
Requires(post): desktop-file-utils
Requires(postun): desktop-file-utils

### Patches ###
Patch12: old-xdg-desktop.patch


%description
Xpra gives you "persistent remote applications" for X. That is, unlike normal X applications, applications run with xpra are "persistent" -- you can run them remotely, and they don't die if your connection does. You can detach them, and reattach them later -- even from another computer -- with no loss of state. And unlike VNC or RDP, xpra is for remote applications, not remote desktops -- individual applications show up as individual windows on your screen, managed by your window manager. They're not trapped in a box.

So basically it's screen for remote X apps.


%prep
rm -rf $RPM_BUILD_DIR/xpra-%{version}
bzcat $RPM_SOURCE_DIR/xpra-%{version}.tar.bz2 | tar -xf -
cd xpra-%{version}

%if 0%{?no_pulseaudio}
(sed -e -i s'/sound_ENABLED = True/sound_ENABLED = False/g' setup.py)
(echo "setup.py" >> %{S:ignored_changed_files.txt})
(echo "etc/*/xpra.conf" >> %{S:ignored_changed_files.txt})
%endif

%if 0%{?old_xdg}
%patch12 -p1
%endif


%debug_package


%build
cd xpra-%{version}
rm -rf build install

# set pkg_config_path for xpra video libs
PKG_CONFIG_PATH=%{_libdir}/xpra/pkgconfig:$PKG_CONFIG_PATH
export PKG_CONFIG_PATH

CFLAGS=-O2 LDFLAGS=-Wl,-rpath=%{_libdir}/xpra python setup.py build %{dummy}

%install
rm -rf $RPM_BUILD_ROOT
cd xpra-%{version}
%{__python} setup.py install -O1 %{dummy} --prefix /usr --skip-build --root %{buildroot}


%if 0%{?opengl}
#included by default
%else
rm -fr ${RPM_BUILD_ROOT}/%{python_sitearch}/xpra/client/gl
%endif

%if 0%{?no_sound}
rm -fr ${RPM_BUILD_ROOT}/%{python_sitearch}/xpra/sound
%endif


%clean
rm -rf $RPM_BUILD_ROOT


%files
%defattr(-,root,root)
%{_bindir}/xpra*
%{python_sitearch}/xpra
%if %{include_egg}
%{python_sitearch}/xpra-*.egg-info
%endif
%{_datadir}/xpra
%{_datadir}/man/man1/xpra*
%{_datadir}/applications/xpra_launcher.desktop
%{_datadir}/applications/xpra.desktop
%{_datadir}/appdata/xpra.appdata.xml
%{_datadir}/icons/xpra.png
%dir %{_sysconfdir}/xpra
%config(noreplace) %{_sysconfdir}/xpra/xorg.conf
%config(noreplace) %{_sysconfdir}/xpra/xpra.conf


%check
/usr/bin/desktop-file-validate %{buildroot}%{_datadir}/applications/xpra_launcher.desktop
/usr/bin/desktop-file-validate %{buildroot}%{_datadir}/applications/xpra.desktop


%post
/usr/bin/update-desktop-database &> /dev/null || :
/bin/touch --no-create %{_datadir}/icons/hicolor &>/dev/null || :


%postun
/usr/bin/update-desktop-database &> /dev/null || :
if [ $1 -eq 0 ] ; then
    /bin/touch --no-create %{_datadir}/icons/hicolor &>/dev/null
    /usr/bin/gtk-update-icon-cache %{_datadir}/icons/hicolor &>/dev/null || :
fi


%posttrans
/usr/bin/gtk-update-icon-cache %{_datadir}/icons/hicolor &>/dev/null || :


%changelog
* Wed Feb 01 2017 Antoine Martin <antoine@devloop.org.uk> 0.14.37-1
- build fix for gcc 4.1 and older
- build fix for python 2.4
- build fix for optimize flag
- fix compatibility with ancient pygtk versions (ie: CentOS 5.x)
- fix access to window from the wrong thread (can crash)
- fix unvalidated malloc in decoder
- remove unsafe 24-bit modes in x264 encoder

* Tue Aug 30 2016 Antoine Martin <antoine@devloop.org.uk> 0.14.36-1
- fix unnecessary delay in network layer of MS Windows clients
- fix sanitization of invalid aspect ratio size hints
- fix error handling in X11 keyboard detection code
- fix MS Windows shadow servers picture corruption
- fix size calculations for the 1 pixel bottom edge of video areas
- fix dbus crash on exit which prevented Xvfb from being killed
- fix run-xpra script accumulating duplicate paths
- fix libx264 API value for infinite key interval
- fix x265 encoder compilation with Python 3.x
- fix minor client logging error causing disconnection from proxy
- fix spurious "Connection lost" warning on disconnection
- fix compilation against ffmpeg 3.1 onwards
- fix video encoder context leak
- fix actual exception reported in GTK X11 errors

* Mon May 02 2016 Antoine Martin <antoine@devloop.org.uk> 0.14.35-2
- fix / workaround bug in Xorg server 1.18.1 and later
- fix support for broken system tray proxies (ie: KDE)
- fix transparency with webp encoding
- fix honour username via TCP
- fix build errors with sound disabled
- fix always use lossless when mmap is enabled (no video detection)
- fix error with unicode characters found in %PATH% on MS Windows
- fix support for Alpine Linux / musl C
- fix RPM packaging for automatic system installation
- fix clipboard timeouts and high CPU usage
- fix clipboard timeouts and high CPU usage
- fix out-of-date bug report data
- fix startup failures on some invalid MS Windows configurations
- fix current working directory of start commands
- fix compatibility with ffmpeg 3.0
- fix division by zero in encoding selection code
- fix 'show systray' menu shortcut code
- fix server deadlock on exit with tcp-proxy or html server
- fix encoding errors with zero dimension windows
- fix stop microphone forwarding, correctly notify the server
- more user friendly missing Xvfb error message
- fix MS Windows shadow server key mapping

* Sun Feb 14 2016 Antoine Martin <antoine@devloop.org.uk> 0.14.34-2
- rebuild with Python 2.4 compatibility fix

* Sat Feb 06 2016 Antoine Martin <antoine@devloop.org.uk> 0.14.34-1
- fix OSX crashes with python optimizations enable via env var
- fix OSX client preventing system shutdown
- fix OSX shadow server warning
- fix xpra upgrade
- fix build for FreeBSD DragonFly
- fix FreeBSD socket library location
- fix cleanup error on win32 shadow servers exit
- fix RPM dependency: we need "which" for the Xdummy wrapper
- fix spurious warnings when connecting very early to a server
- fix webp library conflicts
- fix magic key border toggle
- blacklist more spellings of the Intel driver name
- add new shortcut workaround for showing the system tray menu
- reduce log spam when pulseaudio is not reachable

* Wed Dec 16 2015 Antoine Martin <antoine@devloop.org.uk> 0.14.33-1
- fix OSX crashes caused by power events (disable the handler for now)
- fix libwebp dependency with CentOS 7
- fix network layer error with bencode and missing workspace attribute
- fix handling of window configure requests before the window is shown
- fix keyboard "nuisance" modifiers handling
- fix keyboard modifier synchronization (wrong keys pressed or stuck)
- fix mmap corner case handling: disable it rather than erroring out
- fix limit the number of authentication requests per connection
- fix compatibility with Pillow 3.x (fixes systray on MS Windows)
- fix video region stuttering and high network traffic
- fix bug report tool compatibility with Python 2.6 and earlier
- fix systray position on MS Windows with multiple monitors
- fix bug report tool colour scheme with KDE
- fix MS Windows disconnection error handling (new error codes)
- fix clean disconnection reported as error
- add keyboard shortcut for showing the bug report tool (Alt+Shift+F3)
- allow building against libvpx 1.5 on MS Windows

* Sun Nov 15 2015 Antoine Martin <antoine@devloop.org.uk> 0.14.32-2
- fix Xorg error when there are config files in the user's xpra directory
- fix logging error in authentication backport

* Fri Nov 13 2015 Antoine Martin <antoine@devloop.org.uk> 0.14.32-1
- fix OSX El Capitan sound compatibility issue
- fix potential security issue with password challenge
- fix unnecessary auto-refresh events
- fix x265 encoder
- fix libvpx bitrate calculations
- fix validation of mmap security token
- fix codec import error handler
- fix compatibility with Python Pillow 3.0.0 (logging issue)
- fix support for Ubuntu Vivid (Xorg still unusable)
- fix batch delay heuristics during resizing and queue overload
- fix "always batch" mode
- fix missing network-send-speed accounting
- fix error in override redirect window geometry handling
- fix invalid error logging call
- fix error in XSettings handling causing connection failures
- fix race condition causing corrupted video streams
- fix encoding bug triggered when dependencies are missing
- support Xorg location and arguments required by Arch Linux
- improved lz4 version detection workaround code
- support Xft/DPI
- safer OSX power event handling code
- workaround clients supplying a password when none is required
- log OpenGL driver information

* Tue Oct 13 2015 Antoine Martin <antoine@devloop.org.uk> 0.14.31-1
- fix inband info requests
- fix monitor hotplugging workaround code
- fix OSX menus which should not be shown
- fix cursor lookup by name in local theme
- fix repaint when using the magic key to toggle window borders
- fix connection error when there are XSettings already present
- fix parsing of invalid display structures
- fix video region detection after resize
- fix vpx quality setting
- fix cursor crashes on Ubuntu
- don't show opengl toggle menu if opengl is not supported
- add new common X11 modes (4k, 5k, etc)
- add missing logging category for x265 (fixes warnings on start)

* Sun Sep 13 2015 Antoine Martin <antoine@devloop.org.uk> 0.14.30-1
- fix missing auth argument with Xdummy
- fix server-side copy of the client's desktop dimensions
- fix paint errors with cairo backing
- fix window positioning issues when monitors are added (osx and win32)
- fix group warnings on MS Windows

* Sun Aug 30 2015 Antoine Martin <antoine@devloop.org.uk> 0.14.29-1
- fix encryption not enabled when pycrypto is missing: error out
- fix encryption information leak, free network packets after use
- fix authentication plugins
- fix latency with many sound codecs: vorbis, flac, opus, speex
- fix some subcommands when encryption is enabled
- fix spurious errors on closed connections
- fix incorrect colours using CSC Cython fallback module
- fix size limits on Cython fallback module
- fix some invalid Xorg dummy modelines
- fix errors in packet layer accounting
- fix regression in python-lz4 version guessing code
- fix RPM packaging: prefer our private libraries to the system ones
- fix pactl output parsing
- ship a default configuration file on OSX
- show maximum OpenGL texture size in diagnostics and bug reports

* Sun Aug 02 2015 Antoine Martin <antoine@devloop.org.uk> 0.14.28-1
- fix delta compression errors
- fix application deadlocks on exit
- fix invalid X11 atom
- fix csc Cython red and blue colours swapped on little endian systems
- fix byteswapping fallback code
- fix unhandled failure code from libav
- fix cleanup error on MS Windows, preventing process termination
- fix OpenGL paint early errors
- fix pulseaudio device count reported
- fix timer warnings in GTK2 notifier (mostly used on OSX)
- fix Xorg path detection for Fedora 22 onwards
- fix invalid list of output colorspaces with x264
- fix bug report tool window so it can be used more than once
- fix bug report tool log file error with Vista onwards
- fix bug report screenshots on MS Windows with multiple screens
- fix shadow mode on MS Windows with multiple screens
- fix OpenCL platform selection override
- fix Python3 Pillow encoding level (must be an integer)
- fix capture of subprocesses return code
- fix Xvfb dependencies for Ubuntu
- fix client error if built without webp support
- updated dependency list for Debian and Ubuntu distros
- safer x264 API initialization call
- safer lz4 version checking code
- don't require a nonsensical display name on OSX and win32
- workaround invalid "help" options in config files
- ensure any client decoding errors cause a window refresh
- more helpful dpi warning
- remove unused remnants of nvenc
- more reliable and clean shutdown of connections and threads
- skip sending invalid packet to client for the "name" control command
- MS Windows build environment cleanup

* Wed Jul 01 2015 Antoine Martin <antoine@devloop.org.uk> 0.14.27-4
- force rebuild with updated Fedora 22+ dependencies

* Mon Jun 29 2015 Antoine Martin <antoine@devloop.org.uk> 0.14.27-2
- force rebuild with decorations fixup

* Sun Jun 28 2015 Antoine Martin <antoine@devloop.org.uk> 0.14.27-1
- add missing file to clean list
- fix: rgb encodings can use speed setting
- fix propagation of dynamic attributes for OR windows
- fix invalid warnings in parsing client connection options
- fix handling of the window decorations flag

* Wed Jun 17 2015 Antoine Martin <antoine@devloop.org.uk> 0.14.26-1
- fix executable-not-elf-or-script warning in html5 client tree
- fix displayfd Xorg version check: require version 1.13
- fix GUI debug script on OSX
- fix typo in list of supported X11 atoms
- fix exit-with-children: support sharing mode
- fix pulseaudio not killed on exit on Ubuntu
- fix signal leak when client disconnects
- blacklist Ubuntu Vivid, which broke Xdummy, again
- don't reject clients providing a password when none is expected

* Tue Jun 02 2015 Antoine Martin <antoine@devloop.org.uk> 0.14.25-1
- fix exit path error causing failure to run cleanups
- fix Fedora 22 missing void driver
- fix microphone forwarding packet handling errors
- fix remote ssh start with OSX clients
- fix spinners race
- fix Fedora 22 Xorg binary location detection
- remove nvenc

* Mon May 18 2015 Antoine Martin <antoine@devloop.org.uk> 0.14.24-1
- fix launcher crash on encoding menu changes
- fix transient-for detection for override-redirect windows
- fix wait for connection exit when already closed
- fix proxy server protocol errors
- fix server and client process exit reliability
- fix reentrant errors in signal handler
- fix exit on signal from console
- fix crash when window spinners are shown
- fix invalid lz4 availability check
- fix protocol garbage collection (for consistency)
- fix error when only video encodings are available
- fix compatibility with newer PAM modules
- allow rgb32 for non-video (html5 client)
- add sanity checks to swscale module
- avoid warnings with some Java applications
- handle end-of-stream sound messages
- improved appdata information

* Tue Apr 28 2015 Antoine Martin <antoine@devloop.org.uk> 0.14.23-1
- fix tcp proxy network connection failures, protocol info bug
- fix OpenGL painting of dead connection spinners
- fix errors when windows are closed (a timer was still accessing them)
- fix GdkAtom native structure size error on 32-bit systems
- fix clipboard targets mistakenly honoured when meant to be filtered
- fix tray menu mixed click workaround (prevent firing multiple events)
- fix window group leader reference leak
- fix lack of space in keycode table
- fix icon error on suspend + resume

* Sun Apr 12 2015 Antoine Martin <antoine@devloop.org.uk> 0.14.22-2
- rebuild with python2.4 syntax fix

* Wed Apr 08 2015 Antoine Martin <antoine@devloop.org.uk> 0.14.37-1
- fix window state synchronization bugs
- fix format of modifiers list we send to the server
- fix double free on vpx encoder initialization failures
- fix sound overrun restarts
- fix OSX UI thread lockups detection
- disable vp9 YUV444 decoding via avcodec (fails with errors)
- make parsing of client supplied data more error resilient
- include appdata XML file

* Tue Mar 17 2015 Antoine Martin <antoine@devloop.org.uk> 0.14.21-1
- fix shadow mode
- fix bencoder problems with "xpra info" and video subregions
- fix win32 gradual busy wait delay

* Mon Mar 09 2015 Antoine Martin <antoine@devloop.org.uk> 0.14.20-1
- fix window iconification / maximization loops on win32
- fix handling of fullscreen requests
- fix group leader code (window and memory leak)
- fix drag and drop with Java applications with XPRA_REPARENT_ROOT=1
- fix window spinners
- fix xpra control sound-output subcommand

* Fri Jan 30 2015 Antoine Martin <antoine@devloop.org.uk> 0.14.19-1
- fix windows not showing when we fail to set their title
- fix workspace geometry calculations
- fix handling of null bytes in window and icon titles
- fix systray left over on connection failure (MS Windows)
- fix window flags not updated
- fix MS Windows build BAT file polluting the environment
- fix double menus on OSX
- fix rare errors on shutdown
- fix warning on _NET_WM_STRUT handling
- hide unusable encodings from menus on OSX
- increase window iconification delay to try to prevent loops
- show more helpful network error message
- improved benchmark test class
- add all known MS Windows event names to builtin list

* Sun Jan 18 2015 Antoine Martin <antoine@devloop.org.uk> 0.14.18-1
- fix lossy window paint not getting refreshed
- fix window configuration packet errors
- fix windows wrongly iconified on workspace change
- fix error with invalid _MOTIF_WM_HINTS values
- fix warning with invalid atoms in _NET_WM_STATE messages
- fix spurious NumLock key events on mouse move
- fix error in window-not-found handler
- fix spurious modifier key presses
- blacklist vulnerable flac DLL on MS Windows
- add new xorg resolutions

* Tue Jan 13 2015 Antoine Martin <antoine@devloop.org.uk> 0.14.17-1
- fix crash caused by X11 calls made in an unsafe order
- fix webp codec fallback selection code on older platforms
- fix packet compression and encoder switching on server request
- fix warning with expired nested loop timers
- fix for "MainWin" applications (env vars to workaround their bugs)
- fix check for availability of "initiate-moveresize" bindings

* Thu Jan 08 2015 Antoine Martin <antoine@devloop.org.uk> 0.14.16-1
- fix window decorations handling (large change): _MOTIF_WM_HINTS
- add support for _NET_WM_MOVERESIZE (needed by some undecorated windows)
- fix window iconification loop on connection
- fix maximized and fullscreen state synchronization
- fix OpenCL error with Nvidia hardware
- fix screen update region merging heuristics
- fix Fedora 21+ dummy detection when building from source
- fix build with limited Python environments
- fix network dropouts caused by invalid client properties stored
- fix throttling of video refresh
- fix webp transparency compression
- honour requests to raise window (Java toFront)
- add ability to disable region merging for debugging purposes
- add missing Ubuntu Utopic dependencies

* Mon Dec 29 2014 Antoine Martin <antoine@devloop.org.uk> 0.14.15-1
- fix VP9 decoding support
- fix full-window update heuristics
- fix library linking order (preserve pkg-config order)
- fix windows that iconify programmatically
- fix dialog windows wrongly shown as override redirect
- fix border paint mode with OpenGL
- fix maximize / unmaxmize and fullscreen state synchronization
- fix window WM_STATE property handling (Java applications)
- add missing "dbus-proxy" option

* Thu Dec 18 2014 Antoine Martin <antoine@devloop.org.uk> 0.14.14-1
- fix Python < 2.6 compatibility (syntax errors)
- remove window decorations from non-normal transient windows
- fix error message of X11 client started without a valid display
- fix invalid time recorded in statistics and heuristics
- fix video stream decoding errors by restarting the stream
- blacklist mesa's "Software Rasterizer" (user reported visual corruption)

* Tue Dec 09 2014 Antoine Martin <antoine@devloop.org.uk> 0.14.13-1
- fix cursor scaling (aka "giant cursors")
- fix auto-refresh: encoding selection and requirements
- fix exit-with-children with older python versions
- fix timer execution vs cleanup races
- fix screen information parsing error
- fix dummy Xorg resolutions and add new ones
- fix utility window decorations
- ignore message for background image changes on win32
- blacklist Intel OpenGL driver on MS Windows as well as OSX
- launcher fixes: ssh mode, honour encoding selection, tray cleanup on exit, improved debug mode
- fix pygst metadata signed long value
- fix encryption error handling
- fix Python Pillow server warning

* Wed Nov 19 2014 Antoine Martin <antoine@devloop.org.uk> 0.14.12-1
- fix PyOpenGL related crashes when "accelerate" module is missing
- fix error with automatic display selection and use-display switch
- fix csc modules error with missing but very rarely used function
- re-enable zero copy OpenGL pixel uploads when safe to do so
- add Python lz4 and PIL (or pillow) as dependencies for RPMs
- more accurate cursor shape transforms on MS Windows

* Sun Nov 09 2014 Antoine Martin <antoine@devloop.org.uk> 0.14.11-1
- fix crash with zero copy OpenGL pixel upload (now disabled)
- fix cursor forwarding with MS Windows clients
- fix for the tray menu to allow a mix of left and right clicks
- workaround for Java SDK6 and earlier miscalculating window insets
- fix transparency detection and encoding selection
- fix spurious warning on shadow connection close
- fix window class detection
- fix CUDA automatic device selection
- better client reporting of remote errors

* Sat Oct 25 2014 Antoine Martin <antoine@devloop.org.uk> 0.14.10-2
- fix crash with JPEG encoding and OpenGL
- fix deadlocks with sound on connection shutdown
- fix server errors with clients supporting very limited encodings
- fix compatibility with Fedora 21+ Xorg suid script
- fix compatibility with some login shells (ie: tcsh)
- fix warnings with NVENC and newer Nvidia driver versions
- fix warning with newer versions of Python Pillow

* Tue Oct 07 2014 Antoine Martin <antoine@devloop.org.uk> 0.14.9-2
- fix python 2.4 syntax compatibility
- fix x11 keymap layout detection
- fix IPv6 parsing
- fix shellshock bash env compatibility issue
- fix clipboard auto-disabled too early
- fix event handlers wrongly called twce
- fix command line error message format 

* Wed Oct 01 2014 Antoine Martin <antoine@devloop.org.uk> 0.14.8-1
- fix shadow servers
- fix DPI issues with MS Windows client and high DPI displays
- fix codec version lookup code and add numpy version
- fix command line parsing on builds without server components
- fix command line help text for system-tray option
- fix missing default config on osx
- fix bug in icon change handler
- fix MS Windows shadow servers using 100% CPU
- fix client side error message when windows disappear
- fix transparency detection for some windows
- use new icon consistently
- try harder to enable webp on some platforms
- honour nvenc GPU device selection
- remove old unused code

* Fri Sep 19 2014 Antoine Martin <antoine@devloop.org.uk> 0.14.7-1
- fix compressor fallback case
- fix python2.4 compatibility in bug report tool
- fix client hangs caused by system tray in gnome 3.12
- fix OpenGL double error in failure case
- fix system tray error message on client start
- fix missing default configuration file
- fix session-info window paint issue when switching tabs
- fix default window icon
- add new default resolutions for Xdummy

* Fri Sep 12 2014 Antoine Martin <antoine@devloop.org.uk> 0.14.6-2
- fix transparency support on legacy systems
- fix window icons colours swapped in rgb mode
- fix video region refresh error
- fix OpenGL error in logging code
- fix failures to daemonize
- reduce cost of rectangle calculations
- better window debugging information

* Mon Sep 08 2014 Antoine Martin <antoine@devloop.org.uk> 0.14.5-2
- fix sharing access mode
- fix proxy server error with missing compression algorithms
- fix initial position (honour only when requested)
- fix error wrongly reported after client command has been forwarded
- fix support for multiple keys pressed at the same time
- fix remote ssh start child command with spaces and quotes
- fix remote ssh start child from MS Windows and OSX clients
- handle small screen update storms better
- minor build tree cleanups and fixes
- improved bug report data

* Thu Aug 28 2014 Antoine Martin <antoine@devloop.org.uk> 0.14.4-2
- fix client disconnection on info request
- fix X11 server crash due to threading issues
- fix X11 server crash with BadCursor on some older platforms
- make install script more resilient
- new xorg modelines

* Sat Aug 23 2014 Antoine Martin <antoine@devloop.org.uk> 0.14.3-2
- fix webp issue caused by the 0.14.2 update
- fix system tray forwarding on many platforms
- fix proxy server mode
- fix osx focus click-through windows on osx

* Fri Aug 22 2014 Antoine Martin <antoine@devloop.org.uk> 0.14.2-2
- fix rgb encoding not honoured
- fix systray forwarding error with old gtk versions
- fix RPM netifaces dependencies
- fix webp encoding issues (without opengl or using tray)

* Wed Aug 20 2014 Antoine Martin <antoine@devloop.org.uk> 0.14.1-1
- fix invalid encoding switch
- fix GTK3 build
- fix start-child conflict with configuration files
- fix loading of per-user configuration files on *nix
- fix unnecessary warning if pulseaudio is missing
- fix compatibility with clients without rencode support (ie: html5)
- fix unlikely crash in nvenc encoder
- fix error during window cleanup
- fix OSX build script

* Thu Aug 14 2014 Antoine Martin <antoine@devloop.org.uk> 0.14.0-1
- support for lzo compression
- support for choosing the compressors enabled (lz4, lzo, zlib)
- support for choosing the packet encoders enabled (bencode, rencode, yaml)
- support for choosing the video decoders enabled
- built in bug report tool, capable of collecting debug information
- automatic display selection using Xorg "-displayfd"
- better video region support, increased quality for non-video regions
- more reliable exit and cleanup code, hooks and notifications
- prevent SSH timeouts on login password or passphrase input
- automatic launch the correct tool on MS Windows
- OSX: may use the Application Services folder for a global configuration
- removed python-webm, we now use the native cython codec only
- OpenCL: warn when AMD icd is present (causes problems with signals)
- better avahi mDNS error reporting
- better clipboard compression support
- better packet level network tuning
- support for input methods
- xpra info cleanups and improvments (show children, more versions, etc)
- integrated keyboard layout detection on *nix
- upgrade and shadow now ignore start child
- improved automatic encoding selection, also faster
- keyboard layout selection via system tray on *nix
- more Cython compile time optimizations
- some focus issues fixed

* Wed Aug 13 2014 Antoine Martin <antoine@devloop.org.uk> 0.13.9-1
- fix clipboard on OSX
- fix remote ssh start with start-child issues
- use secure "compare_digest" if available
- fix crashes in codec cleanup
- fix video encoding fallback code
- fix fakeXinerama setup wrongly skipped in some cases
- fix connection failures with large screens and uncompressed RGB
- fix Ubuntu trustyi Xvfb configuration
- fix clipboard errors with no data
- fix opencl platform initialization errors

* Wed Aug 06 2014 Antoine Martin <antoine@devloop.org.uk> 0.13.8-1
- fix server early exit when pulseaudio terminates
- fix SELinux static codec library label (make it persistent)
- fix missed auto-refresh when batching
- fix disabled clipboard packets coming through
- fix cleaner client connection shutdown sequence and exit code
- fix resource leak on connection error
- fix potential bug in fallback encoding selection
- fix deadlock on worker race it was meant to prevent
- fix remote ssh server start timeout
- fix avahi double free on exit
- fix png and jpeg painting via gdk pixbuf (when PIL is missing)
- fix webp refresh loops
- honour lz4-off environment variable
- fix proxy handling of raw RGB data for large screen sizes
- fix potential error from missing data in client packets

* Thu Jul 10 2014 Antoine Martin <antoine@devloop.org.uk> 0.13.7-3
- fix x11 server pixmap memory leak
- fix speed and quality values range (1 to 100)
- fix nvenc device allocation errors
- fix unnecessary refreshes with nvenc
- fix "initenv" compatibility with older servers
- don't start child when upgrading or shadowing

* Tue Jun 17 2014 Antoine Martin <antoine@devloop.org.uk> 0.13.6-3
- fix compatibility older versions of pygtk (centos5)
- fix compatibility with python 2.4 (centos5)
- fix AltGr workaround with win32 clients
- fix some missing keys with 'fr' keyboard layout (win32)
- fix installation on systems without python-glib (centos5)
- fix Xorg version detection for Fedora rawhide

* Sat Jun 14 2014 Antoine Martin <antoine@devloop.org.uk> 0.13.5-3
- re-fix opengl compatibility 

* Fri Jun 13 2014 Antoine Martin <antoine@devloop.org.uk> 0.13.5-1
- fix use correct dimensions when evaluating video
- fix invalid latency statistics recording
- fix auto-refresh wrongly cancelled
- fix connection via nested ssh commands
- fix statically linked builds of swscale codec
- fix system tray icons when upgrading server
- fix opengl compatibility with older libraries
- fix ssh connection with shells not starting in home directory
- fix keyboard layout change forwarding

* Tue Jun 10 2014 Antoine Martin <antoine@devloop.org.uk> 0.13.4-1
- fix numeric keypad period key mapping on some non-us keyboards
- fix client launcher GUI on OSX
- fix remote ssh start with clean user account
- fix remote shadow start with automatic display selection
- fix avoid scaling during resize
- fix changes of speed and quality via xpra control (make it stick)
- fix xpra info global batch statistics
- fix focus issue with some applications
- fix batch delay use

* Sun Jun 01 2014 Antoine Martin <antoine@devloop.org.uk> 0.13.3-1
- fix xpra upgrade
- fix xpra control error handling
- fix window refresh on inactive workspace
- fix slow cursor updates
- fix error in rgb strict mode
- add missing x11 server type information

* Sun Jun 01 2014 Antoine Martin <antoine@devloop.org.uk> 0.13.2-1
- fix painting of forwarded tray
- fix initial window workspace
- fix launcher with debug option in config file
- fix compilation of x265 encoder
- fix infinite recursion in cython csc module
- don't include sound utilities when building without sound

* Wed May 28 2014 Antoine Martin <antoine@devloop.org.uk> 0.13.1-1
- honour lossless encodings
- fix avcodec2 build for Debian jessie and sid
- fix pam authentication module
- fix proxy server launched without a display
- fix xpra info data format (wrong prefix)
- fix transparency with png/L mode
- fix loss of transparency when toggling OpenGL
- fix re-stride code for compatibility with ancient clients
- fix timer reference leak causing some warnings

* Thu May 22 2014 Antoine Martin <antoine@devloop.org.uk> 0.13.0-1
- Python3 / GTK3 client support
- NVENC module included in binary builds
- support for enhanced dummy driver with DPI option
- better build system with features auto-detection
- removed unsupported CUDA csc module
- improved buffer support
- faster webp encoder
- improved automatic encoding selection
- support running MS Windows installer under wine
- support for window opacity forwarding
- fix password mode in launcher
- edge resistance for automatic image downscaling
- increased default memory allocation of the dummy driver
- more detailed version information and tools
- stricter handling of server supplied values

* Fri May 16 2014 Antoine Martin <antoine@devloop.org.uk> 0.12.6-1
- fix invalid pixel buffer size causing encoding failures
- fix auto-refresh infinite loop, and honour refresh quality
- fix sound sink with older versions of GStreamer plugins
- fix Qt applications crashes caused by a newline in xsettings..
- fix error with graphics drivers only supporting OpenGL 2.x only
- fix OpenGL crash on OSX with the Intel driver (now blacklisted)
- fix global menu entry text on OSX
- fix error in cairo backing cleanup
- fix RGB pixel data buffer size (re-stride as needed)
- avoid buggy swscale 2.1.0 on Ubuntu

* Sat May 03 2014 Antoine Martin <antoine@devloop.org.uk> 0.12.5-1
- fix error when clients supply invalid screen dimensions
- fix MS Windows build without ffmpeg
- fix cairo backing alternative
- fix keyboard and sound test tools initialization and cleanup
- fix gcc version test used for enabling sanitizer build options
- fix exception handling in client when called from the launcher
- fix libav dependencies for Debian and Ubuntu builds

* Wed Apr 23 2014 Antoine Martin <antoine@devloop.org.uk> 0.12.4-1
- fix xpra shadow subcommand
- fix xpra shadow keyboard mapping support for non-posix clients
- avoid Xorg dummy warning in log

* Wed Apr 09 2014 Antoine Martin <antoine@devloop.org.uk> 0.12.3-1
- fix mispostioned windows
- fix quickly disappearing windows (often menus)
- fix server errors when closing windows
- fix NVENC server initialization crash with driver version mismatch
- fix rare invalid memory read with XShm
- fix webp decoder leak
- fix memory leak on client disconnection
- fix focus errors if windows disappear
- fix mmap errors on window close
- fix incorrect x264 encoder speed reported via "xpra info"
- fix potential use of mmap as an invalid fallback for video encoding
- fix logging errors in debug mode
- fix timer expired warning

* Sun Mar 30 2014 Antoine Martin <antoine@devloop.org.uk> 0.12.2-1
- fix switching to RGB encoding via client tray
- fix remote server start via SSH
- fix workspace change detection causing slow screen updates

* Thu Mar 27 2014 Antoine Martin <antoine@devloop.org.uk> 0.12.1-1
- fix 32-bit server timestamps
- fix client PNG handling on installations without PIL / Pillow

* Sun Mar 23 2014 Antoine Martin <antoine@devloop.org.uk> 0.12.0-1
- NVENC support for YUV444 mode, support for automatic bitrate tuning
- NVENC and CUDA load balancing for multiple cards
- proxy encoding: ability to encode on proxy server
- fix fullscreen on multiple monitors via fakeXinerama
- OpenGL rendering improvements (for transparent windows, etc)
- support window grabs (drop down menus, etc)
- support specifying the SSH port number more easily
- enabled TCP_NODELAY socket option by default (lower latency)
- add ability to easily select video encoders and csc modules
- add local unix domain socket support to proxy server instances
- add "xpra control" commands to control encoding speed and quality
- improved handling of window resizing
- improved compatibility with command line tools (xdotool, wmctrl)
- ensure windows on other workspaces do not waste bandwidth
- ensure iconified windows do not waste bandwidth
- ensure maximized and fullscreen windows are prioritised
- ensure we reset xsettings when client disconnects
- better bandwidth utilization of jittery connections
- faster network code (larger receive buffers)
- better automatic encoding selection for smaller regions
- improved command line options (add ability to enable options which are disabled in the config file)
- trimmed all the ugly PyOpenGL warnings on startup
- much improved logging and debugging tools
- make it easier to distinguish xpra windows from local windows (border command line option)
- improved build system: smaller and more correct build output (much smaller OSX images)
- automatically stop remote shadow servers when client disconnects

* Tue Mar 18 2014 Antoine Martin <antoine@devloop.org.uk> 0.11.6-1
- correct fix for system tray forwarding

* Tue Mar 18 2014 Antoine Martin <antoine@devloop.org.uk> 0.11.5-1
- fix "xpra info" with bencoder
- ensure we re-sanitize window size hints when they change
- workaround applications with nonsensical size hints (ie: handbrake)
- fix 32-bit painting with GTK pixbuf loader (when PIL is not installed or disabled)
- fix system tray forwarding geometry issues
- fix workspace restore
- fix compilation warning
- remove spurious cursor warnings

* Sat Mar 01 2014 Antoine Martin <antoine@devloop.org.uk> 0.11.4-1
- fix NVENC GPU memory leak
- fix video compatibility with ancient clients
- fix vpx decoding in ffmpeg decoders
- fix transparent system tray image with RGB encoding
- fix client crashes with system tray forwarding
- fix webp codec loader error handler

* Fri Feb 14 2014 Antoine Martin <antoine@devloop.org.uk> 0.11.3-1
- fix compatibility with ancient versions of GTK
- fix crashes with malformed socket names
- fix server builds without client modules
- honour mdns flag set in config file
- blacklist VMware OpenGL driver which causes client crashes
- ensure all "control" subcommands run in UI thread

* Wed Jan 29 2014 Antoine Martin <antoine@devloop.org.uk> 0.11.2-1
- fix Cython 0.20 compatibility
- fix OpenGL pixel upload alignment code
- fix xpra command line help page tokens
- fix compatibility with old versions of the python glib library

* Fri Jan 24 2014 Antoine Martin <antoine@devloop.org.uk> 0.11.1-1
- fix compatibility with old/unsupported servers
- fix shadow mode
- fix paint issue with transparent tooltips on OSX and MS Windows
- fix pixel format typo in OpenGL logging

* Mon Jan 20 2014 Antoine Martin <antoine@devloop.org.uk> 0.11.0-1
- NVENC hardware h264 encoding acceleration
- OpenCL and CUDA colourspace conversion acceleration
- proxy server mode for serving multiple sessions through one port
- support for sharing a TCP port with a web server
- server control command for modifying settings at runtime
- server exit command, which leaves Xvfb running
- publish session via mDNS
- OSX client two way clipboard support
- support for transparency with OpenGL window rendering
- support for transparency with 8-bit PNG modes
- support for more authentication mechanisms
- support remote shadow start via ssh
- support faster lz4 compression
- faster bencoder, rewritten in Cython
- builtin fallback colourspace conversion module
- real time frame latency graphs
- improved system tray forwarding support and native integration
- removed most of the Cython/C code duplication
- stricter and safer value parsing
- more detailed status information via UI and "xpra info"
- experimental HTML5 client
- drop non xpra clients with a more friendly response

* Tue Jan 14 2014 Antoine Martin <antoine@devloop.org.uk> 0.10.12-1
- fix missing auto-refresh with lossy colourspace conversion
- fix spurious warning from Nvidia OpenGL driver
- fix OpenGL client crash with some drivers (ie: VirtualBox)
- fix crash in bencoder caused by empty data to encode
- fix ffmpeg2 h264 decoding (ie: Fedora 20+)
- big warnings about webp leaking memory
- generated debuginfo RPMs

* Tue Jan 07 2014 Antoine Martin <antoine@devloop.org.uk> 0.10.11-1
- fix popup windows focus issue
- fix "xpra upgrade" subcommand
- fix server backtrace in error handler
- restore server target information in tray tooltip
- fix bencoder error with no-windows switch (missing encoding)
- add support for RGBX pixel format required by some clients
- avoid ffmpeg "data is not aligned" warning on client

* Wed Dec 04 2013 Antoine Martin <antoine@devloop.org.uk> 0.10.10-1
- fix focus regression
- fix MS Windows clipboard copy including null byte
- fix h264 decoding with old versions of avcodec
- fix potential invalid read past the end of the buffer
- fix static vpx build arguments
- fix RGB modes exposed for transparent windows
- fix crash on clipboard loops: detect and disable clipboard
- support for ffmpeg version 2.x
- support for video encoding of windows bigger than 4k
- support video encoders that re-start the stream
- fix crash in decoding error path
- forward compatibility with namespace changes
- forward compatibility with the new generic encoding names

* Tue Nov 05 2013 Antoine Martin <antoine@devloop.org.uk> 0.10.9-1
- fix h264 decoding of padded images
- fix plain RGB encoding with very old clients
- fix "xpra info" error when old clients are connected
- remove warning when "help" is specified as encoding

* Tue Oct 22 2013 Antoine Martin <antoine@devloop.org.uk> 0.10.8-1
- fix misapplied patch breaking all windows with transparency

* Tue Oct 22 2013 Antoine Martin <antoine@devloop.org.uk> 0.10.7-1
- fix client crash on Linux with AMD cards and fglrx driver
- fix missing WM_CLASS on X11 clients
- fix "xpra info" on shadow servers
- add usable 1366x768 dummy resolution

* Tue Oct 15 2013 Antoine Martin <antoine@devloop.org.uk> 0.10.6-1
- fix window titles reverting to "unknown host"
- fix tray forwarding bug causing client disconnections
- replace previous rencode fix with warning

* Thu Oct 10 2013 Antoine Martin <antoine@devloop.org.uk> 0.10.5-1
- fix client time out when the initial connection fails
- fix shadow mode
- fix connection failures when some system information is missing
- fix client disconnection requests
- fix encryption cipher error messages
- fix client errors when some features are disabled
- fix potential rencode bug with unhandled data types
- error out if the client requests authentication and none is available

* Tue Sep 10 2013 Antoine Martin <antoine@devloop.org.uk> 0.10.4-2
- fix modifier key handling (was more noticeable with MS Windows clients)
- fix auto-refresh

* Fri Sep 06 2013 Antoine Martin <antoine@devloop.org.uk> 0.10.3-2
- fix transient windows with no parent
- fix metadata updates handling (maximize, etc)

* Thu Aug 29 2013 Antoine Martin <antoine@devloop.org.uk> 0.10.2-2
- fix connection error with unicode user name
- fix vpx compilation warning
- fix python 2.4 compatibility
- fix handling of scaling attribute via environment override
- build fix: ensure all builds include source information


* Tue Aug 20 2013 Antoine Martin <antoine@devloop.org.uk> 0.10.1-1
- fix avcodec buffer pointer errors on some 32-bit Linux
- fix invalid time convertion
- fix OpenGL scaling with fractions
- compilation fix for some newer versions of libav
- honour scaling at high quality settings
- add ability to disable transparency via environment variable
- silence PyOpenGL warnings we can do nothing about
- fix CentOS 6.3 packaging dependencies

* Tue Aug 13 2013 Antoine Martin <antoine@devloop.org.uk> 0.10.0-3
- performance: X11 shared memory (XShm) pixels transfers
- performance: zero-copy window pixels to picture encoders
- performance: zero copy decoded pixels to window (but not with OpenGL..)
- performance: multi-threaded x264 encoding and decoding
- support for speed tuning (latency vs bandwidth) with more encodings (png, jpeg, rgb)
- support for grayscale and palette based png encoding
- support for window and tray transparency
- support webp lossless
- support x264's "ultrafast" preset
- support forwarding of group-leader application window information
- prevent slow encoding from creating backlogs
- OpenGL accelerated client rendering enabled by default wherever supported
- register as a generic URL handler
- fullscreen toggle support
- stricter Cython code
- better handling of sound buffering and overruns
- experimental support for a Qt based client
- support for different window layouts with custom widgets
- don't try to synchronize with clipboards that do not exist (for shadow servers mostly)
- refactoring: move features and components to sub-modules
- refactoring: split X11 bindings from pure gtk code
- refactoring: codecs split encoding and decoding side
- refactoring: move more common code to utility classes
- refactoring: remove direct dependency on gobject in many places
- refactoring: platform code better separated
- refactoring: move wimpiggy inside xpra, delete parti
- export and expose more version information (x264/vpx/webp/PIL, OpenGL..)
- export compiler information with build (Cython, C compiler, etc)
- export much more debugging information about system state and statistics
- simplify non-UI subcommands and their packets, also use rencode ("xpra info", "xpra version", etc)

* Mon Jul 29 2013 Antoine Martin <antoine@devloop.org.uk> 0.9.8-1
- fix client workarea size change detection (again)
- fix crashes handling info requests
- fix server hangs due to sound cleanup deadlock
- use lockless window video decoder cleanup (much faster)
- speedup server startup when no XAUTHORITY file exists yet

* Tue Jul 16 2013 Antoine Martin <antoine@devloop.org.uk> 0.9.7-1
- fix error in sound cleanup code
- fix network threads accounting
- fix missing window icons
- fix client availibility of remote session start feature

* Sun Jun 30 2013 Antoine Martin <antoine@devloop.org.uk> 0.9.6-1
- fix lost clicks on some popup menus (mostly with MS Windows clients)
- fix client workarea size change detection
- fix reading of unique "machine-id" on posix
- fix window reference leak for windows we fail to manage
- fix compatibility with pillow (PIL fork)
- fix session-info window graphs jumping (smoother motion)
- fix webp loading code for non-Linux posix systems
- fix window group-leader attribute setting
- fix man page indentation
- fix variable test vs use (correctness only)

* Thu Jun 06 2013 Antoine Martin <antoine@devloop.org.uk> 0.9.5-1
- fix auto-refresh: don't refresh unnecessarily
- fix wrong initial timeout when ssh takes a long time to connect
- fix client monitor/resolution size change detection
- fix attributes reported to clients when encoding overrides are used
- Gentoo ebuild uses virtual to allow one to choose pillow or PIL

* Mon May 27 2013 Antoine Martin <antoine@devloop.org.uk> 0.9.4-1
- revert cursor scaling fix which broke other applications
- fix auto refresh mis-firing
- fix type (atom) of the X11 visual property we expose

* Mon May 20 2013 Antoine Martin <antoine@devloop.org.uk> 0.9.3-1
- fix clipboard for *nix clients
- fix selection timestamp parsing
- fix crash due to logging code location
- fix pixel area request dimensions for lossless edges
- fix advertized tray visual property
- fix cursors are too small with some applications
- fix crash when low level debug code is enabled
- reset cursors when disabling cursor forwarding
- workaround invalid window size hints

* Mon May 13 2013 Antoine Martin <antoine@devloop.org.uk> 0.9.2-1
- fix double error when loading build information (missing about dialog)
- fix and simplify build "clean" subcommand
- fix OpenGL rendering alignment for padded rowstrides case
- fix potential double error when tray initialization fails
- fix window static properties usage

* Wed May 08 2013 Antoine Martin <antoine@devloop.org.uk> 0.9.1-1
- honour initial client window's requested position
- fix for hidden appindicator
- fix string formatting error in non-cython fallback math code
- fix error if ping packets fail from the start
- fix for windows without a valid window-type (ie: shadows)
- fix OpenGL missing required feature detection (and add debug)
- add required CentOS RPM libXfont dependency
- tag our /etc configuration files in RPM spec file

* Thu Apr 25 2013 Antoine Martin <antoine@devloop.org.uk> 0.9.0-1
- fix focus problems with old Xvfb display servers
- fix RPM SELinux labelling of static codec builds (CentOS)
- fix CentOS 5.x compatibility
- fix Python 2.4 and 2.5 compatibility (many)
- fix failed server upgrades killing the virtual display
- fix screenshot command with "OR" windows
- fix support "OR" windows that move and resize
- IPv6 server support
- support for many more audio codecs: flac, opus, wavpack, wav, speex
- support starting remote sessions with "xpra start"
- support for Xdummy with CentOS 6.4 onwards
- add --log-file command line option
- add clipboard regex string filtering
- add clipboard transfer in progress animation via system tray
- detect broken/slow connections and temporarily grey out windows
- reduce regular packet header sizes using numeric lookup tables
- allow more options in xpra config and launcher files
- safer test for windows to ignore (window IDs starts at 1 again)
- expose more version and statistical data via xpra info
- improved OpenGL client rendering (still disabled by default)
- upgrade to rencode 1.0.2

* Thu Mar 07 2013 Antoine Martin <antoine@devloop.org.uk> 0.8.8-1
- fix server deadlock on dead connections
- fix compatibility with older versions of Python
- fix sound capture script usage via command line
- fix screen number preserve code
- fix error in logs in shadow mode

* Wed Feb 27 2013 Antoine Martin <antoine@devloop.org.uk> 0.8.7-1
- fix x264 crash with older versions of libav
- fix 32-bit builds breakage introduce by python2.4 fix in 0.8.6
- fix missing sound forwarding when using the GUI launcher
- fix microphone forwarding errors
- fix client window properties store
- fix first workspace not preserved and other workspace issues

* Fri Feb 22 2013 Antoine Martin <antoine@devloop.org.uk> 0.8.6-1
- fix python2.4 compatibility in icon grabbing code
- fix exit message location

* Sun Feb 17 2013 Antoine Martin <antoine@devloop.org.uk> 0.8.5-1
- fix server crash with transient windows

* Wed Feb 13 2013 Antoine Martin <antoine@devloop.org.uk> 0.8.4-1
- fix hello packet encoding bug
- fix colours in launcher and session-info windows

* Tue Feb 12 2013 Antoine Martin <antoine@devloop.org.uk> 0.8.3-1
- Python 2.4 compatiblity fixes (CentOS 5.x)
- fix static builds of vpx and x264

* Sun Feb 10 2013 Antoine Martin <antoine@devloop.org.uk> 0.8.2-1
- fix libav uninitialized structure crash
- fix warning on installations without sound libraries
- fix warning when pulseaudio utils are not installed
- fix delta compression race
- fix the return of some ghost windows
- stop pulseaudio on exit, warn if it fails to start
- re-enable system tray forwarding
- remove spurious "too many receivers" warnings

* Mon Feb 04 2013 Antoine Martin <antoine@devloop.org.uk> 0.8.1-1
- fix server daemonize on some platforms
- fix server SSH support on platforms with old versions of glib
- fix "xpra upgrade" closing applications
- fix detection of almost-lossless frames with x264
- fix starting of a duplicate pulseaudio server on upgrade
- fix compatibility with older versions of pulseaudio (pactl)
- fix session-info window when a tray is being forwarded
- remove warning on builds with limited encoding support
- disable tray forwarding by default as it causes problems with some apps
- rename "Quality" to "Min Quality" in tray menu
- fix rpm packaging: remove unusable modules

* Thu Jan 31 2013 Antoine Martin <antoine@devloop.org.uk> 0.8.0-9
- fix modal windows support
- fix default mouse cursor: now uses the client's default cursor
- fix short lived windows: avoid doing unnecessary work, avoid re-registering handlers
- fix limit the number of raw packets per client to prevent DoS via memory exhaustion
- fix authentication: ensure salt is per connection
- fix for ubuntu global application menus
- fix proxy handling of deadly signals
- fix pixel queue size calculations used for performance tuning decisions
- edge resistance for colourspace conversion level changes to prevent yoyo effect
- more aggressive picture quality tuning
- better CPU utilization
- new command line options and tray menu to trade latency for bandwidth
- x264 disable unecessary I-frames and avoid IDR frames
- performance and latency optimizations in critical sections
- avoid server loops: prevent the client from connecting to itself
- group windows according to the remote application they belong to
- sound forwarding (initial code, high latency)
- faster and more reliable client and server exit (from signal or otherwise)
- "xpra shadow" mode to clone an existing X11 display (compositors not supported yet)
- support for delta pixels mode (most useful for shadow mode)
- avoid warnings and X11 errors with the screenshot command
- better mouse cursor support: send cursors by name so their size matches the client's settings
- mitigate bandwidth eating cursor change storms: introduce simple cursor update batching
- support system tray icon forwarding (limited)
- preserve window workspace
- AES packet encryption for TCP mode (without key secure exchange for now)
- launcher entry box for username in SSH mode
- launcher improvements: highlight the password field if needed, prevent warnings, etc
- better window manager specification compatibility (for broken applications or toolkits)
- use lossless encoders more aggressively when possible
- new x264 tuning options: profiles to use and thresholds
- better detection of dead server sockets: retry and remove them if needed
- improved session information dialog and graphs
- more detailed hierarchical per-window details via "xpra info"
- send window icons in dedicated compressed packet (smaller new-window packets, faster)
- detect overly large main packets
- partial/initial Java/AWT keyboard support


* Mon Oct 08 2012 Antoine Martin <antoine@devloop.org.uk> 0.7.0-1
- fix "AltGr" key handling with MS Windows clients (and others)
- fix crash with x264 encoding
- fix crash with fast disappearing tooltip windows
- avoid storing password in a file when using the launcher (except on MS Windows)
- many latency fixes and improvements: lower latency, better line congestion handling, etc
- lower client latency: decompress pictures in a dedicated thread (including rgb24+zlib)
- better launcher command feedback
- better automatic compression heuristics
- support for Xdummy on platforms with only a suid binary installed
- support for 'webp' lossy picture encoding (better and faster than jpeg)
- support fixed picture quality with x264, webp and jpeg (via command line and tray menu)
- support for multiple "start-child" options in config files or command line
- more reliable auto-refresh
- performance optimizations: caching results, avoid unnecessary video encoder re-initialization
- faster re-connection (skip keyboard re-configuration)
- better isolation of the virtual display process and child processes
- show performance statistics graphs on session info dialog (click to save)
- start with compression enabled, even for initial packet
- show more version and client information in logs and via "xpra info"
- client launcher improvements: prevent logging conflict, add version info
- large source layout cleanup, compilation warnings fixed

* Fri Oct 05 2012 Antoine Martin <antoine@devloop.org.uk> 0.6.4-1
- fix bencoder to properly handle dicts with non-string keys
- fix swscale bug with windows that are too small by switch encoding
- fix locking of video encoder resizing leading to missing video frames
- fix crash with compression turned off: fix unicode encoding
- fix lack of locking sometimes causing errors with "xpra info"
- fix password file handling: exceptions and ignore carriage returns
- prevent races during setup and cleanup of network connections
- take shortcut if there is nothing to send

* Thu Sep 27 2012 Antoine Martin <antoine@devloop.org.uk> 0.6.3-1
- fix memory leak in server after client disconnection
- fix launcher: clear socket timeout once connected and add missing options
- fix potential bug in network code (prevent disconnection)
- enable auto-refresh by default since we now use a lossy encoder by default

* Tue Sep 25 2012 Antoine Martin <antoine@devloop.org.uk> 0.6.2-1
- fix missing key frames with x264/vpx: always reset the video encoder when we skip some frames (forces a new key frame)
- fix server crash on invalid keycodes (zero or negative)
- fix latency: isolate per-window latency statistics from each other
- fix latency: ensure we never record zero or even negative decode time
- fix refresh: server error was causing refresh requests to be ignored
- fix window options handling: using it for more than one value would fail
- fix video encoder/windows dimensions mismatch causing missing key frames
- fix damage options merge code (options were being squashed)
- ensure that small lossless regions do not cancel the auto-refresh timer
- restore protocol main packet compression and single chunk sending
- drop unnecessary OpenGL dependencies from some deb/rpm packages

* Fri Sep 14 2012 Antoine Martin <antoine@devloop.org.uk> 0.6.1-1
- fix compress clipboard data (previous fix was ineffectual)

* Sat Sep 08 2012 Antoine Martin <antoine@devloop.org.uk> 0.6.0-1
- fix launcher: don't block the UI whilst connecting, and use a lower timeout, fix icon lookup on *nix
- fix clipboard contents too big (was causing connection drops): try to compress them and just drop them if they are still too big
- x264 or vpx are now the default encodings (if available)
- compress rgb24 pixel data with zlib from the damage thread (rather than later in the network layer)
- better build environment detection
- experimental multi-user support (see --enable-sharing)
- better, more accurate "xpra info" statistics (per encoding, etc)
- tidy up main source directory
- simplify video encoders/decoders setup and cleanup code
- remove 'nogil' switch (as 'nogil' is much faster)
- test all socket types with automated tests

* Sat Sep 08 2012 Antoine Martin <antoine@devloop.org.uk> 0.5.4-1
- fix man page typo
- fix non bash login shell compatibility
- fix xpra screenshot argument parsing error handling
- fix video encoding mismatch when switching encoding
- fix ssh mode on OpenBSD

* Wed Sep 05 2012 Antoine Martin <antoine@devloop.org.uk> 0.5.3-1
- zlib compatibility fix: use chunked decompression when supported (newer versions)

* Wed Aug 29 2012 Antoine Martin <antoine@devloop.org.uk> 0.5.2-1
- fix xpra launcher icon lookup on *nix
- fix big clipboard packets causing disconnection: just drop them instead
- fix zlib compression in raw packet mode: ensure we always flush the buffer for each chunk
- force disconnection after irrecoverable network parsing error
- fix window refresh: do not skip all windows after a hidden one!

* Mon Aug 27 2012 Antoine Martin <antoine@devloop.org.uk> 0.5.1-6
- fix xpra_launcher
- build against rpmfusion repository, with build fix for Fedora 16

* Sat Aug 25 2012 Antoine Martin <antoine@devloop.org.uk> 0.5.1-1
- fix DPI issue with Xdummy: set virtual screen to 96dpi by default
- avoid looping forever doing maths on 'infinity' value
- fix incomplete cloning of attributes causing default values to be used for batch configuration
- damage data queue batch factor was being calculated but not used
- ensure we update the data we use for calculations (was always using zero value)
- ensure "send_bell" is initialized before use
- add missing path string in warning message
- fix test code compatibility with older xpra versions
- statistics shown for 'damage_packet_queue_pixels' were incorrect

* Mon Aug 20 2012 Antoine Martin <antoine@devloop.org.uk> 0.5.0-1
- new packet encoder written in C (much faster and data is now smaller too)
- read provided /etc/xpra/xpra.conf and user's own ~/.xpra/xpra.conf
- support Xdummy out of the box on platforms with recent enough versions of Xorg (and not installed suid)
- pass dpi to server and allow clients to specify dpi on the command line
- fix xsettings endianness problems
- fix clipboard tokens sent twice on start
- new command line options and UI to disable notifications forwarding, cursors and bell
- x264: adapt colourspace conversion, encoding speed and picture quality according to link and encoding/decoding performance
- automatically change video encoding: handle small region updates (ie: blinking cursor or spinner) without doing a full video frame refresh
- fairer window batching calculations, better performance over low latency links and bandwidth constrained links
- lower tcp socket connection timeout (10 seconds)
- better compression of cursor data
- log date and time with messages, better log messages (ie: "Ignoring ClientMessage..")
- send more client and server version information (python, gtk, etc)
- build cleanups: let distutils clean take care of removing all generated .c files
- code cleanups: move all win32 specific headers to win32 tree, fix vpx compilation warnings, whitespace, etc
- removed old "--no-randr" option
- drop compatibility with versions older than 0.3: we now assume the "raw_packets" feature is supported

* Mon Jul 23 2012 Antoine Martin <antoine@devloop.org.uk> 0.4.0-1
- fix client application resizing its own window
- fix window dimensions hints not applied
- fix memleak in x264 cleanup code
- fix xpra command exit code (more complete fix)
- fix latency bottleneck in processing of damage requests
- fix free uninitialized pointers in video decoder initialization error codepath
- fix x264 related crash when resizing windows to one pixel width or height
- fix accounting of client decode time: ignore figure in case of decoding error
- fix subversion build information detection on MS Windows
- fix some binary packages which were missing some menu icons
- restore keyboard compatiblity code for MS Windows and OSX clients
- use padded buffers to prevent colourspace conversion from reading random memory
- release Python's GIL during vpx and x264 compression and colourspace conversion
- better UI launcher: UI improvements, detect encodings, fix standalone/win32 usage, minimize window once the client has started
- "xpra stop" disconnects all potential clients cleanly before exiting
- use memory aligned buffer for better performance with x264
- avoid vpx/x264 overhead for very small damage regions
- detect dead connection with ping packets: disconnect if echo not received
- force a full refresh when the encoding is changed
- more dynamic framerate performance adjustments, based on more metrics
- new menu option to toggle keyboard sync at runtime
- vpx/x264 runtime imports: detect broken installations and warn, but ignore when the codec is simply not installed
- enable environment debugging for damage batching via "XPRA_DEBUG_LATENCY" env variable
- simplify build by using setup file to generate all constants
- text clients now ignore packets they are not meant to handle
- removed compression menu since the default is good enough
- "xpra info" reports all build version information
- report server pygtk/gtk versions and show them on session info dialog and "xpra info"
- ignore dependency issues during sdist/clean phase of build
- record more statistics (mostly latency) in test reports
- documentation and logging added to code, moved test code out of main packages
- include distribution name in RPM version/filename
- CentOS 6 RPMs now depends on libvpx rather than a statically linked library
- CentOS static ffmpeg build with memalign for better performance
- no longer bundle parti window manager

* Tue Jul 10 2012 Antoine Martin <antoine@devloop.org.uk> 0.3.3-1
- do not try to free the empty x264/vpx buffers after a decompression failure
- fix xpra command exit code (zero) when no error occurred
- fix Xvfb deadlock on shutdown
- fix wrongly removing unix domain socket on startup failure
- fix wrongly killing Xvfb on startup failure
- fix race in network code and meta data packets
- ensure clients use raw_packets if the server supports it (fixes 'gibberish' compressed packet errors)
- fix screen resolution reported by the server
- fix maximum packet size check wrongly dropping valid connections
- honour the --no-tray command line argument
- detect Xvfb startup failures and avoid taking over other displays
- don't record invalid placeholder value for "server latency"
- fix missing "damage-sequence" packet for sequence zero
- fix window focus with some Tk based application (ie: git gui)
- prevent large clipboard packets from causing the connection to drop
- fix for connection with older clients and server without raw packet support and rgb24 encoding
- high latency fix: reduce batch delay when screen updates slow down
- non-US keyboard layout fix
- correctly calculate min_batch_delay shown in statistics via "xpra info"
- require x264-libs for x264 support on Fedora

* Wed Jun 06 2012 Antoine Martin <antoine@devloop.org.uk> 0.3.2-1
- fix missing 'a' key using OS X clients
- fix debian packaging for xpra_launcher
- fix unicode decoding problems in window title
- fix latency issue

* Tue May 29 2012 Antoine Martin <antoine@devloop.org.uk> 0.3.1-1
- fix DoS in network connections setup code
- fix for non-ascii characters in source file
- log remote IP or socket address
- more graceful disconnection of invalid clients
- updates to the man page and xpra command help page
- support running the automated tests against older versions
- "xpra info" to report the number of clients connected
- use xpra's own icon for its own windows (about and info dialogs)

* Sun May 20 2012 Antoine Martin <antoine@devloop.org.uk> 0.3.0-1
- zero-copy network code, per packet compression
- fix race causing DoS in threaded network protocol setup
- fix vpx encoder memory leak
- fix vpx/x264 decoding: recover from frame failures
- fix small per-window memory leak in server
- per-window update batching auto-tuning, which is fairer
- windows update batching now takes into account the number of pixels rather than just the number of regions to update
- support --socket-dir option over ssh
- IPv6 support using the syntax: ssh/::ffff:192.168.1.100/10 or tcp/::ffff:192.168.1.100/10000
- all commands now return a non-zero exit code in case of failure
- new "xpra info" command to report server statistics
- prettify some of the logging and error messages
- avoid doing most of the keyboard setup code when clients are in read-only mode
- automated regression and performance tests
- remove compatibility code for versions older than 0.1

* Fri Apr 20 2012 Antoine Martin <antoine@devloop.org.uk> 0.2.0-1
- x264 and vpx video encoding support
- gtk3 and python 3 partial support (client only - no keyboard support)
- detect missing X11 server extensions and exit with error
- X11 vfb servers no longer listens on a TCP port
- clipboard fixes for Qt/KDE applications
- option for clients not to supply any keyboard mapping data (the server will no longer complain)
- show more system version information in session information dialog
- hide window decorations for openoffice splash screen (workaround)

* Wed Mar 21 2012 Antoine Martin <antoine@devloop.org.uk> 0.1.0-1
- security: strict filtering of packet handlers until connection authenticated
- prevent DoS: limit number of concurrent connections attempting login (20)
- prevent DoS: limit initial packet size (memory exhaustion: 32KB)
- mmap: options to place sockets in /tmp and share mmap area across users via unix groups
- remove large amount of compatiblity code for older versions
- fix for Mac OS X clients sending hexadecimal keysyms
- fix for clipboard sharing and some applications (ie: Qt)
- notifications systems with dbus: re-connect if needed
- notifications: try not to interfere with existing notification services
- mmap: check for protected file access and ignore rather than error out (oops)
- clipboard: handle empty data rather than timing out
- spurious warnings: remove many harmless stacktraces/error messages
- detect and discard broken windows with invalid atoms, avoids vfb + xpra crash
- unpress keys all keys on start (if any)
- fix screen size check: also check vertical size is sufficient
- fix for invisible 0 by 0 windows: restore a minimum size
- fix for window dimensions causing enless resizing or missing window contents
- toggle cursors, bell and notifications by telling the server not to bother sending them, saves bandwidth
- build/deploy: don't modify file in source tree, generate it at build time only
- add missing GPL2 license file to show in about dialog
- Python 2.5: workarounds to restore support
- turn off compression over local connections (when mmap is enabled)
- clients can specify maximum refresh rate and screen update batching options

* Wed Feb 08 2012 Antoine Martin <antoine@devloop.org.uk> 0.0.7.36-1
- fix clipboard bug which was causing Java applications to crash
- ensure we always properly disconnect previous client when new connection is accepted
- avoid warnings with Java applications, focus errors, etc

* Wed Feb 01 2012 Antoine Martin <antoine@devloop.org.uk> 0.0.7.35-1
- ssh password input fix
- ability to take screenshots ("xpra screenshot")
- report server version ("xpra version")
- slave windows (drop down menus, etc) now move with their parent window
- show more session statistics: damage regions per second
- posix clients no longer interfere with the GTK/X11 main loop
- ignore missing properties when they are changed, and report correct source of the problem
- code style cleanups and improvements

* Thu Jan 19 2012 Antoine Martin <antoine@devloop.org.uk> 0.0.7.34-1
- security: restrict access to run-xpra script (chmod)
- security: cursor data sent to the client was too big (exposing server memory)
- fix thread leak - properly this time, SIGUSR1 now dumps all threads
- off-by-one keyboard mapping error could cause modifiers to be lost
- pure python/cython method for finding modifier mappings (faster and more reliable)
- retry socket read/write after temporary error EINTR
- avoid warnings when asked to refresh windows which are now hidden
- auto-refresh was using an incorrect window size
- logging formatting fixes (only shown with logging on)
- hide picture encoding menu when mmap in use (since it is then ignored)

* Fri Jan 13 2012 Antoine Martin <antoine@devloop.org.uk> 0.0.7.33-1
- readonly command line option
- correctly stop all network related threads on disconnection
- faster pixel data transfers for large areas
- fix auto-refresh jpeg quality
- fix potential exhaustion of mmap area
- fix potential race in packet compression setup code
- keyboard: better modifiers detection, synchronization of capslock and numlock
- keyboard: support all modifiers correctly with and without keyboard-sync option

* Wed Dec 28 2011 Antoine Martin <antoine@devloop.org.uk> 0.0.7.32-1
- bug fix: disconnection could leave the server (and X11 server) in a broken state due to threaded UI calls
- bug fix: don't remove window focus when just any connection is lost, only when the real client goes away
- bug fix: initial windows should get focus (partial fix)
- support key repeat latency workaround without needing raw keycodes (OS X and MS Windows)
- command line switch to enable client side key repeat: "--no-keyboard-sync" (for high latency/jitter links)
- session info dialog: shows realtime connection and server details
- menu entry in system tray to raise all managed windows
- key mappings: try harder to unpress all keys before setting the new keymap
- key mappings: try to reset modifier keys as well as regular keys
- key mappings: apply keymap using Cython code rather than execing xmodmap
- key mappings: fire change callbacks only once when all the work is done
- use dbus for tray notifications if available, prefered to pynotify
- show full version information in about dialog

* Mon Nov 28 2011 Antoine Martin <antoine@devloop.org.uk> 0.0.7.31-1
- threaded server for much lower latency
- fast memory mapped transfers for local connections
- adaptive damage batching, fixes window refresh
- xpra "detach" command
- fixed system tray for Ubuntu clients
- fixed maximized windows on Ubuntu clients

* Tue Nov 01 2011 Antoine Martin <antoine@devloop.org.uk> 0.0.7.30-1
- fix for update batching causing screen corruption
- fix AttributeError jpegquality: make PIL (aka python-imaging) truly optional
- fix for jitter compensation code being a little bit too trigger-happy

* Wed Oct 26 2011 Antoine Martin <antoine@devloop.org.uk> 0.0.7.29-2
- fix partial packets on boundary causing connection to drop (properly this time)

* Tue Oct 25 2011 Antoine Martin <antoine@devloop.org.uk> 0.0.7.29-1
- fix partial packets on boundary causing connection to drop
- improve disconnection diagnostic messages
- scale cursor down to the client's default size
- better handling of right click on system tray icon
- posix: detect when there is no DISPLAY and error out
- support ubuntu's appindicator (yet another system tray implementation)
- remove harmless warnings about missing properties on startup

* Tue Oct 18 2011 Antoine Martin <antoine@devloop.org.uk> 0.0.7.28-2
- fix password mode - oops

* Tue Oct 18 2011 Antoine Martin <antoine@devloop.org.uk> 0.0.7.28-1
- much more efficient and backwards compatible network code, prevents a CPU bottleneck on the client
- forwarding of system notifications, system bell and custom cursors
- system tray menu to make it easier to change settings and disconnect
- automatically resize Xdummy to match the client's screen size whenever it changes
- PNG image compression support
- JPEG and PNG compression are now optional, only available if the Python Imaging Library is installed
- scale window icons before sending if they are too big
- fixed keyboard mapping for OSX and MS Windows clients
- compensate for line jitter causing keys to repeat
- fixed cython warnings, unused variables, etc

* Thu Sep 22 2011 Antoine Martin <antoine@devloop.org.uk> 0.0.7.27-1
- compatibility fix for python 2.4 (remove "with" statement)
- slow down updates from windows that refresh continuously

* Tue Sep 20 2011 Antoine Martin <antoine@devloop.org.uk> 0.0.7.26-1
- minor changes to support the Android client (work in progress)
- allow keyboard shortcuts to be specified, default is meta+shift+F4 to quit (disconnects client)
- clear modifiers when applying new keymaps to prevent timeouts
- reduce context switching in the network read loop code
- try harder to close connections cleanly
- removed some unused code, fixed some old test code

* Wed Aug 31 2011 Antoine Martin <antoine@devloop.org.uk> 0.0.7.25-1
- Use xmodmap to grab the exact keymap, this should ensure all keys are mapped correctly
- Reset modifiers whenever we gain or lose focus, or when the keymap changes

* Mon Aug 15 2011 Antoine Martin <antoine@devloop.org.uk> 0.0.7.24-1
- Use raw keycodes whenever possible, should fix keymapping issues for all Unix-like clients
- Keyboard fixes for AltGr and special keys for non Unix-like clients

* Wed Jul 27 2011 Antoine Martin <antoine@devloop.org.uk> 0.0.7.23-2
- More keymap fixes..

* Wed Jul 20 2011 Antoine Martin <antoine@devloop.org.uk> 0.0.7.23-1
- Try to use setxkbmap before xkbcomp to setup the matching keyboard layout
- Handle keyval level (shifted keys) explicitly, should fix missing key mappings
- More generic option for setting window titles
- Exit if the server dies

* Thu Jun 02 2011 Antoine Martin <antoine@devloop.org.uk> 0.0.7.22-1
- minor fixes: jpeg, man page, etc

* Fri May 20 2011 Antoine Martin <antoine@devloop.org.uk> 0.0.7.21-1
- ability to bind to an existing display with --use-display
- --xvfb now specifies the full command used. The default is unchanged
- --auto-refresh-delay does automatic refresh of idle displays in a lossless fashion

* Wed May 04 2011 Antoine Martin <antoine@devloop.org.uk> 0.0.7.20-1
- more reliable fix for keyboard mapping issues

* Mon Apr 25 2011 Antoine Martin <antoine@devloop.org.uk> 0.0.7.19-1
- xrandr support when running against Xdummy, screen resizes on demand
- fixes for keyboard mapping issues: multiple keycodes for the same key

* Mon Apr 4 2011 Antoine Martin <antoine@devloop.org.uk> 0.0.7.18-2
- Fix for older distros (like CentOS) with old versions of pycairo

* Mon Mar 28 2011 Antoine Martin <antoine@devloop.org.uk> 0.0.7.18-1
- Fix jpeg compression on MS Windows
- Add ability to disable clipboard code
- Updated man page

* Wed Jan 19 2011 Antoine Martin <antoine@devloop.org.uk> 0.0.7.17-1
- Honour the pulseaudio flag on client

* Wed Aug 25 2010 Antoine Martin <antoine@devloop.org.uk> 0.0.7.16-1
- Merged upstream changes.

* Thu Jul 01 2010 Antoine Martin <antoine@devloop.org.uk> 0.0.7.15-1
- Add option to disable Pulseaudio forwarding as this can be a real network hog.
- Use logging rather than print statements.

* Tue May 04 2010 Antoine Martin <antoine@devloop.org.uk> 0.0.7.13-1
- Ignore minor version differences in the future (must bump to 0.0.8 to cause incompatibility error)

* Tue Apr 13 2010 Antoine Martin <antoine@devloop.org.uk> 0.0.7.12-1
- bump screen resolution

* Mon Jan 11 2010 Antoine Martin <antoine@devloop.org.uk> 0.0.7.11-1
- first rpm spec file

###
### eof
###
