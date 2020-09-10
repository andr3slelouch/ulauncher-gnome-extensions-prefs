import gi
from gi.repository import Gio
from os.path import isdir, join, expanduser, isfile
import subprocess
"""
gsettings get org.gnome.shell enabled-extensions
Part 1 - Getting enabled extensions
"""
gnome_shell_extensions_schema = "org.gnome.shell"
enabled_extensions_key = "enabled-extensions"
settings = Gio.Settings.new(gnome_shell_extensions_schema)
enabled_extensions_list = settings.get_value(enabled_extensions_key)
print(enabled_extensions_list)
enabled_extensions_dict = {}

"""
Part 2 - Check if are system extensions or user extensions
"""

system_extensions_dir = "/usr/share/gnome-shell/extensions"
user_extensions_dir = "{}/.local/share/gnome-shell/extensions".format(expanduser("~"))
system_extensions_list = []
user_extensions_list = []


for extension in enabled_extensions_list:
    if isdir(join(user_extensions_dir, extension)):
        user_extensions_list.append(extension)
    elif isdir(join(system_extensions_dir, extension)):
        system_extensions_list.append(extension)

"""
Part 3 - Check if extension has prefs file
"""

for extension in system_extensions_list:
    if not isfile(join(system_extensions_dir, extension, "prefs.js")):
        system_extensions_list.remove(extension)
for extension in user_extensions_list:
    if not isfile(join(user_extensions_dir, extension, "prefs.js")):
        user_extensions_list.remove(extension)

extensions_with_preferences_dict = {
        "user": user_extensions_list,
        "system": system_extensions_list
    }

for val in extensions_with_preferences_dict:
    print(val)

"""
Part 4 - Launch extensions with prefs
"""

#test = subprocess.Popen(["gnome-extensions","prefs",user_extensions_list[-1]])







