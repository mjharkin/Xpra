# This file is part of Xpra.
# Copyright (C) 2010 Nathaniel Smith <njs@pobox.com>
# Copyright (C) 2011-2013 Antoine Martin <antoine@devloop.org.uk>
# Xpra is released under the terms of the GNU GPL v2, or, at your option, any
# later version. See the file COPYING for details.

#default:
Keyboard = None

from xpra.platform import platform_import
platform_import(globals(), "keyboard", True,
                "Keyboard")

def main():
    import sys
    from xpra.util import print_nested_dict, csv
    from xpra.platform import program_context
    from xpra.log import Logger, enable_color
    with program_context("Keyboard-Tool", "Keyboard Tool"):
        log = Logger("keyboard")
        enable_color()
        if "-v" in sys.argv or "--verbose" in sys.argv:
            log.enable_debug()

        #naughty, but how else can I hook this up?
        import os
        if os.name=="posix":
            try:
                from xpra.x11.bindings import posix_display_source      #@UnusedImport
            except:
                pass    #maybe running on OSX? hope for the best..

        keyboard = Keyboard()
        mod_meanings, mod_managed, mod_pointermissing = keyboard.get_keymap_modifiers()
        print("Modifiers:")
        print_nested_dict(mod_meanings)
        print("")
        print("Server Managed                    : %s" % (csv(mod_managed) or "None"))
        print("Missing from pointer events       : %s" % (csv(mod_pointermissing) or "None"))
        print("")
        layout,layouts,variant,variants = keyboard.get_layout_spec()
        print("Layout:     '%s'" % (layout))
        print("Layouts:    %s" % (layouts, ))
        print("Variant:    '%s'" % (variant))
        print("Variants:   %s" % (variants, ))
        print("")
        print("Repeat:     %s" % csv(keyboard.get_keyboard_repeat()))

if __name__ == "__main__":
    main()
