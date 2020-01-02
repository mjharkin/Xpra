#!/usr/bin/env python

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gtk, Gdk  #pylint: disable=wrong-import-position
from xpra.gtk_common.cursor_names import cursor_types  #pylint: disable=wrong-import-position

width = 400
height = 200
def main():
	window = Gtk.Window(type=Gtk.WindowType.TOPLEVEL)
	window.set_size_request(width, height)
	window.connect("delete_event", Gtk.main_quit)

	cursor_combo = Gtk.ComboBoxText()
	cursor_combo.append_text("")
	for name in sorted(cursor_types.keys()):
		cursor_combo.append_text(name)
	window.add(cursor_combo)

	def change_cursor(*_args):
		name = cursor_combo.get_active_text()
		print("new cursor: %s" % name)
		if name:
			gdk_cursor = cursor_types.get(name)
			cursor = Gdk.Cursor(gdk_cursor)
		else:
			cursor = None
		window.get_window().set_cursor(cursor)

	cursor_combo.connect("changed", change_cursor)
	window.show_all()
	Gtk.main()
	return 0


if __name__ == "__main__":
	main()