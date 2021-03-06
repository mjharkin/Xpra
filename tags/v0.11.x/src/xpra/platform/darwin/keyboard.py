# This file is part of Xpra.
# Copyright (C) 2010 Nathaniel Smith <njs@pobox.com>
# Copyright (C) 2011-2013 Antoine Martin <antoine@devloop.org.uk>
# Xpra is released under the terms of the GNU GPL v2, or, at your option, any
# later version. See the file COPYING for details.


import gtk.gdk
from xpra.platform.keyboard_base import KeyboardBase, debug
from xpra.platform.darwin.osx_menu import getOSXMenuHelper


NUM_LOCK_KEYCODE = 71           #HARDCODED!
#a key and the keys we want to translate it into when swapping keys
#(a list so we can hopefully find a good match)
KEYS_TRANSLATION_OPTIONS = {
                    "Control_L"     : ["Alt_L", "Meta_L"],
                    "Control_R"     : ["Alt_R", "Meta_R"],
                    "Meta_L"        : ["Control_L", "Control_R"],
                    "Meta_R"        : ["Control_R", "Control_L"],
                    }

class Keyboard(KeyboardBase):
    """
        Switch Meta and Control
    """

    def __init__(self):
        self.swap_keys = True
        self.meta_modifier = None
        self.control_modifier = None
        self.num_lock_modifier = None
        self.num_lock_state = True
        self.num_lock_keycode = NUM_LOCK_KEYCODE
        self.key_translations = {}

    def set_modifier_mappings(self, mappings):
        KeyboardBase.set_modifier_mappings(self, mappings)
        self.meta_modifier = self.modifier_keys.get("Meta_L") or self.modifier_keys.get("Meta_R")
        self.control_modifier = self.modifier_keys.get("Control_L") or self.modifier_keys.get("Control_R")
        self.num_lock_modifier = self.modifier_keys.get("Num_Lock")
        debug("set_modifier_mappings(..) meta=%s, control=%s, numlock=%s", mappings, self.meta_modifier, self.control_modifier, self.num_lock_modifier)
        #find the keysyms and keycodes to use for each key we may translate:
        for orig_keysym in KEYS_TRANSLATION_OPTIONS.keys():
            new_def = self.find_translation(orig_keysym)
            if new_def is not None:
                self.key_translations[orig_keysym] = new_def
        debug("set_modifier_mappings(..) swap keys translations=%s", self.key_translations)

    def find_translation(self, orig_keysym):
        new_def = None
        #ie: keysyms : ["Meta_L", "Alt_L"]
        keysyms = KEYS_TRANSLATION_OPTIONS.get(orig_keysym)
        for keysym in keysyms:
            #ie: "Alt_L":
            keycodes_defs = self.modifier_keycodes.get(keysym)
            if not keycodes_defs:
                #keysym not found
                continue
            #ie: [(55, 'Alt_L'), (58, 'Alt_L'), 'Alt_L']
            for keycode_def in keycodes_defs:
                if type(keycode_def)==str:      #ie: 'Alt_L'
                    #no keycode found, but better than nothing:
                    new_def = 0, keycode_def    #ie: (0, 'Alt_L')
                    continue
                #look for a tuple of (keycode, keysym):
                if type(keycode_def) not in (list, tuple):
                    continue
                if type(keycode_def[0])!=int or type(keycode_def[1])!=str:
                    continue
                #found one, use that:
                return keycode_def           #(55, 'Alt_L')
        return new_def


    def mask_to_names(self, mask):
        names = KeyboardBase.mask_to_names(self, mask)
        if self.swap_keys and self.meta_modifier is not None and self.control_modifier is not None:
            meta_on = bool(mask & gtk.gdk.META_MASK)
            meta_set = self.meta_modifier in names
            control_set = self.control_modifier in names
            if meta_on and not control_set:
                debug("mask_to_names swapping meta for control: %s for %s", self.meta_modifier, self.control_modifier)
                names.append(self.control_modifier)
                if meta_set:
                    names.remove(self.meta_modifier)
            elif control_set and not meta_on:
                debug("mask_to_names swapping control for meta: %s for %s", self.control_modifier, self.meta_modifier)
                names.remove(self.control_modifier)
                if not meta_set:
                    names.append(self.meta_modifier)
        #deal with numlock:
        if self.num_lock_modifier is not None:
            if self.num_lock_state and self.num_lock_modifier not in names:
                names.append(self.num_lock_modifier)
            elif not self.num_lock_state and self.num_lock_modifier in names:
                names.remove(self.num_lock_modifier)
        debug("mask_to_names(%s)=%s", mask, names)
        return names

    def process_key_event(self, send_key_action_cb, wid, key_event):
        if self.swap_keys:
            trans = self.key_translations.get(key_event.keyname)
            if trans:
                debug("swap keys: translating key '%s' to %s", key_event, trans)
                key_event.keycode, key_event.keyname = trans
        if key_event.keycode==self.num_lock_keycode and not key_event.pressed:
            debug("toggling numlock")
            self.num_lock_state = not self.num_lock_state
            getOSXMenuHelper().update_numlock(self.num_lock_state)
        send_key_action_cb(wid, key_event)
