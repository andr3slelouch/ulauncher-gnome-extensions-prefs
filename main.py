import gi
import subprocess
import json

gi.require_version("Gdk", "3.0")
from gi.repository import Gio
from os.path import isdir, join, expanduser, isfile
from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import (
    KeywordQueryEvent,
    ItemEnterEvent,
    PreferencesUpdateEvent,
    PreferencesEvent,
)
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.HideWindowAction import HideWindowAction
from ulauncher.api.shared.action.ExtensionCustomAction import ExtensionCustomAction

DISPLAY_MAX_RESULTS = 10

DIRECTORIES = {
    "system": "/usr/share/gnome-shell/extensions",
    "user": "{}/.local/share/gnome-shell/extensions".format(expanduser("~")),
}


def launch_extension_prefs(extension_name):
    return subprocess.Popen(["gnome-extensions", "prefs", extension_name])


def list_extensions_with_prefs(only_enabled=True):
    """This function gets a list of extensions that has prefs file"""

    """
    Part 1 - Getting extensions
    gsettings get org.gnome.shell enabled-extensions or disabled-extensions
    """
    gnome_shell_extensions_schema = "org.gnome.shell"

    extensions_keys = {
        "enabled": "enabled-extensions",
        "disabled": "disabled-extensions",
    }

    gsettings = Gio.Settings.new(gnome_shell_extensions_schema)
    extensions_list = list(gsettings.get_value(extensions_keys["enabled"]))
    if not (only_enabled):
        extensions_list += list(gsettings.get_value(extensions_keys["disabled"]))

    """
    Part 2 - Check if are system extensions or user extensions
    """

    system_extensions_list = []
    user_extensions_list = []

    for extension in extensions_list:
        if isdir(join(DIRECTORIES["user"], extension)):
            user_extensions_list.append(extension)
        elif isdir(join(DIRECTORIES["system"], extension)):
            system_extensions_list.append(extension)

    """
    Part 3 - Check if extension has prefs file
    """

    for extension in system_extensions_list:
        if not isfile(join(DIRECTORIES["system"], extension, "prefs.js")):
            system_extensions_list.remove(extension)
    for extension in user_extensions_list:
        if not isfile(join(DIRECTORIES["user"], extension, "prefs.js")):
            user_extensions_list.remove(extension)

    extensions_with_preferences_dict = {
        "user": user_extensions_list,
        "system": system_extensions_list,
    }

    return extensions_with_preferences_dict


class GnomeExtensionItem:
    def __init__(self, directory_path, extension_type, previous_selection):
        self.directory_path = directory_path
        self.type = extension_type
        self.name = self.get_name()
        self.is_last = self.directory_path == previous_selection

    def get_name(self):
        with open(
            join(DIRECTORIES[self.type], self.directory_path, "metadata.json")
        ) as json_file:
            data = json.load(json_file)
        return data["name"]

    def to_extension_item(self):
        return ExtensionResultItem(
            icon="images/icon.png",
            name=self.name,
            selected_by_default=self.is_last,
            on_enter=ExtensionCustomAction(self.directory_path, keep_app_open=False),
        )

    def is_matching(self, keyword):
        # Assumes UTF-8 input
        ascii_keyword = keyword
        return ascii_keyword in self.name.lower()


class GnomeExtensionsPrefs(Extension):
    def __init__(self):
        super(GnomeExtensionsPrefs, self).__init__()
        self.selection = None
        self.previous_selection = None
        self.only_enabled = None
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())
        self.subscribe(ItemEnterEvent, ItemEnterEventListener())
        self.subscribe(PreferencesEvent, PreferencesEventListener())
        self.subscribe(PreferencesUpdateEvent, PreferencesUpdateEventListener())


class KeywordQueryEventListener(EventListener):
    def on_event(self, event, extension):
        query = event.get_argument()
        if query is None:
            # The extension has just been triggered, let's initialize the windows list.
            # (Or we delete all previously typed characters, but we can safely ignore that case)
            query = ""
            extension.items = [
                GnomeExtensionItem(extension, "user", extension)
                for extension in list_extensions_with_prefs(extension.only_enabled)[
                    "user"
                ]
            ] + [
                GnomeExtensionItem(extension, "system", extension)
                for extension in list_extensions_with_prefs(extension.only_enabled)[
                    "system"
                ]
            ]
        matching_items = [
            extension_item.to_extension_item()
            for extension_item in extension.items
            if extension_item.is_matching(query)
        ]
        return RenderResultListAction(matching_items[:DISPLAY_MAX_RESULTS])


class ItemEnterEventListener(EventListener):
    def on_event(self, event, extension):
        extension_raw_name = event.get_data()
        launch_extension_prefs(extension_raw_name)


class PreferencesEventListener(EventListener):
    def on_event(self, event, extension):
        #   only_enabled value
        flag_dict = {"true": True, "false": False}
        extension.only_enabled = flag_dict[event.preferences["only_enabled"]]


class PreferencesUpdateEventListener(EventListener):
    def on_event(self, event, extension):
        #   only_enabled value
        if event.id == "only_enabled":
            flag_dict = {"true": True, "false": False}
            extension.only_enabled = flag_dict[event.new_value]


if __name__ == "__main__":
    GnomeExtensionsPrefs().run()