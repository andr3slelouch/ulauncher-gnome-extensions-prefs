import gi
gi.require_version('Gdk', '3.0')
import subprocess
import json
from gi.repository import Gio
from os.path import isdir, join, expanduser, isfile
from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent, ItemEnterEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.HideWindowAction import HideWindowAction
from ulauncher.api.shared.action.ExtensionCustomAction import ExtensionCustomAction

directories = {
    "system": "/usr/share/gnome-shell/extensions",
    "user": "{}/.local/share/gnome-shell/extensions".format(expanduser("~"))
}

def launch_extension_prefs(extension_name):
    return subprocess.Popen(["gnome-extensions","prefs",extension_name])

def list_extensions_with_prefs(only_enabled=True):
    """This function gets a list of extensions that has prefs file"""
    
    """
    Part 1 - Getting extensions
    gsettings get org.gnome.shell enabled-extensions or disabled-extensions
    """
    gnome_shell_extensions_schema = "org.gnome.shell"

    extensions_keys = {
        "enabled": "enabled-extensions",
        "disabled": "disabled-extensions"
    }
    
    gsettings = Gio.Settings.new(gnome_shell_extensions_schema)
    extensions_list = gsettings.get_value(extensions_keys["enabled"])
    if not (only_enabled):
        extensions_list.append(gsettings.get_value(extensions_keys["disabled"]))


    """
    Part 2 - Check if are system extensions or user extensions
    """

    
    system_extensions_list = []
    user_extensions_list = []


    for extension in extensions_list:
        if isdir(join(directories["user"], extension)):
            user_extensions_list.append(extension)
        elif isdir(join(directories["system"], extension)):
            system_extensions_list.append(extension)

    """
    Part 3 - Check if extension has prefs file
    """

    for extension in system_extensions_list:
        if not isfile(join(directories["system"], extension, "prefs.js")):
            system_extensions_list.remove(extension)
    for extension in user_extensions_list:
        if not isfile(join(directories["user"], extension, "prefs.js")):
            user_extensions_list.remove(extension)
    
    extensions_with_preferences_dict = {
        "user": user_extensions_list,
        "system": system_extensions_list
    }

    return extensions_with_preferences_dict

class GnomeExtensionItem:
    def __init__(self, directory_path, extension_type, previous_selection):
        self.directory_path = directory_path
        self.type = extension_type
        self.name = self.get_name()
        self.description = self.get_description()
        self.is_last = self.directory_path == previous_selection

    def get_name(self):
        with open(join(directories[self.type],self.directory_path,"metadata.json")) as json_file:
            data = json.load(json_file)
        return data["name"]
    
    def get_description(self):
        with open(join(directories[self.type],self.directory_path,"metadata.json")) as json_file:
            data = json.load(json_file)
        return data["description"]
    
    def to_extension_item(self):
        return ExtensionResultItem(icon='images/icon.png',
                                             name=self.name,
                                             description=self.description,
                                             selected_by_default=self.is_last,
                                             on_enter=ExtensionCustomAction(self.directory_path, keep_app_open=False))
    
    def is_matching(self, keyword):
        # Assumes UTF-8 input
        ascii_keyword = keyword
        return ascii_keyword in self.name.lower() or ascii_keyword in self.description.lower()
        
            

class GnomeExtensionsPrefs(Extension):

    def __init__(self):
        super(GnomeExtensionsPrefs, self).__init__()
        self.selection = None
        self.previous_selection = None
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())


class KeywordQueryEventListener(EventListener):

    def on_event(self, event, extension):
        query = event.get_argument()
        if query is None:
            # The extension has just been triggered, let's initialize the windows list.
            # (Or we delete all previously typed characters, but we can safely ignore that case)
            query = ''
            extension.items = [GnomeExtensionItem(extension, "user", extension) for extension in list_extensions_with_prefs()["user"]] + \
                [GnomeExtensionItem(extension, "system", extension) for extension in list_extensions_with_prefs()["system"]]
        matching_items = [extension_item.to_extension_item() for extension_item in extension.items if
                          extension_item.is_matching(query)]
        return RenderResultListAction(matching_items)

class ItemEnterEventListener(EventListener):
    def on_event(self, event, extension):
        extensions_list = list_extensions_with_prefs()["user"]+list_extensions_with_prefs["system"]
        for extension in extensions_list:
            print(extension, event.get_data())
            if extension == event.get_data():
                previous_selection = extension.selection
                extension.previous_selection = previous_selection
                extension.selection = extension
                launch_extension_prefs(extension)

        


if __name__ == '__main__':
    GnomeExtensionsPrefs().run()