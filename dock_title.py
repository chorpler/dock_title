#!/usr/bin/env python3

# This is a simple script that allows you to Clear and Restore the titles of your MacOS dock's apps.
# It will not delete the Finder, Trash, or any other system apps titles.

import os
import subprocess
import platform
import pprint
import plistlib

from collections import OrderedDict

from typing import Any, List, Dict, TypedDict, Optional, cast

plist_file = "~/Library/Preferences/com.apple.dock.plist"
plist_file_backup = "~/Library/Preferences/com.apple.dock.plist.backup"


class TextStyle:  # Define text styles
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    reset = '\033[0m'
    NC = reset


app_logo = """
   ___  ____  _______ __   __________________   ____
  / _ \/ __ \/ ___/ //_/  /_  __/  _/_  __/ /  / __/
 / // / /_/ / /__/ ,<      / / _/ /  / / / /__/ _/
/____/\____/\___/_/|_|    /_/ /___/ /_/ /____/___/

by Victor D. NEAMT
"""


# Define types for a persistent app record from the Dock plist file
PersistentAppFileData = TypedDict('PersistentAppFileData', {
    "_CFURLString": str,
    "_CFURLStringType": str,
})

PersistentAppTileData = TypedDict('PersistentAppTileData', {
    "book": str,
    "bundle-identifier": str,
    "dock-extra": bool,
    "file-data": PersistentAppFileData,
    "file-label": Optional[str],
    "file-mod-date": int,
    "file-type": int,
    "is-beta": bool,
    "parent-mod-date": int,
})

PersistentApp = TypedDict('PersistentApp', {
    "GUID": int,
    "tile-data": PersistentAppTileData,
    "tile-type": str,
})

PersistentApps = List[PersistentApp]
PersistentAppsRecords = Dict[int, PersistentApp]


# Set up global variables and formatters
PRETTY = pprint.PrettyPrinter(indent=2, width=200)
all_apps: PersistentApps = list()
persistent_apps: PersistentApps = list()
# app_map: List[(int, PersistentApp)] = list()
app_map: PersistentAppsRecords = dict()


# Check if the script is running on MacOS, and if not, exit.
if platform.system() != "Darwin":
    print(f"\n{TextStyle.RED}Error: this script is for MacOS only. Exiting...{TextStyle.NC}\n")
    exit()

dock_plist = os.path.expanduser(plist_file)  # Define the path to the dock plist file
dock_plist_backup = os.path.expanduser(plist_file_backup)  # Define the path to the dock plist backup file

if not os.path.exists(dock_plist):  # Check if the dock plist file exists, and if not, exit.
    print(f"\n{TextStyle.RED}Error: Dock plist file not found. Exiting...{TextStyle.NC}\n")
    exit()

if not os.path.exists(dock_plist_backup):  # Check if the dock plist backup file exists, and if not, create it.
    subprocess.call(["cp", dock_plist, dock_plist_backup])
else:  # If the dock plist backup file exists, detele it and create anther backup.
    subprocess.call(["rm", dock_plist_backup])
    subprocess.call(["cp", dock_plist, dock_plist_backup])

dock_plist_opened = plistlib.load(open(dock_plist, "rb"))  # Open the dock plist file in read mode

if "persistent-apps" in dock_plist_opened:  # Check if there are any persistent apps in the dock, and if not, exit.
    persistent_apps = cast(PersistentApps, dock_plist_opened["persistent-apps"])
else:
    print(f"\n{TextStyle.RED}Error: No apps found in the dock. Exiting...{TextStyle.NC}\n")
    exit()

if "recent-apps" in dock_plist_opened:  # Check if there are any recent apps in the dock, and if so, add them to the persistent apps list.
    all_apps = cast(PersistentApps, persistent_apps) + cast(PersistentApps, dock_plist_opened["recent-apps"])
else:  # If there are no recent apps in the dock, just use the persistent apps list.
    all_apps = cast(PersistentApps, persistent_apps)

if "persistent-others" in dock_plist_opened:  # Check if there are any persistent others in the dock, and if so, add them to the persistent apps list.
    all_apps = all_apps + cast(PersistentApps, dock_plist_opened["persistent-others"])


##################################################
# Utility functions for strings, lists, dicts
##################################################
def is_list(value: Any) -> bool:
    result = False
    if value is not None:
        if type(value) == list:
            result = True
    return result


def list_good(value: Any) -> bool:
    return is_list(value) and len(value) > 0


def is_dict(value: Any) -> bool:
    result = False
    if value is not None:
        if type(value) == dict or type(value) == OrderedDict:
            result = True
    return result


def dict_good(value: Any) -> bool:
    return is_dict(value) and len(value) > 0


def is_string(value: Any) -> bool:
    result = False
    if value is not None:
        if type(value) == str or type(value) == bytes:
            result = True
    return result


def string_good(value: Any) -> bool:
    return is_string(value) and len(value) > 0


##################################################
# App-specific functions
############################################
def isValid(app: PersistentApp) -> bool:
    if app is not None and app["GUID"] is not None and app['tile-data'] is not None:
        return True
    return False


def get_app_name(app: PersistentApp):
    if isValid(app):
        return app["tile-data"]["file-data"]["_CFURLString"].replace("%20", " ").split("/")[-2].replace(".app", "")


def get_app_label(app: PersistentApp) -> str:
    result = ""
    if isValid(app) and 'file-label' in app["tile-data"]:
        result = app["tile-data"]["file-label"]
    return result


def set_app_label(app: PersistentApp, label: str):
    new_label: str = ""
    if isValid(app):
        app_name = get_app_name(app)
        if string_good(label):
            print(f"\n> Setting label for {app_name} to '{label}' ...")
            new_label = label
        else:
            print(f"\n> Deleting label for app {app_name} ...")
        app["tile-data"]["file-label"] = new_label


def labelApp(app: PersistentApp, label: str = ""):
    if isValid(app):
        app_name = get_app_name(app)
        if label is not None and type(label) == str:
            app_name = label
        set_app_label(app, app_name)
    else:
        print(TextStyle.RED + f"ERROR: invalid app record provided" + TextStyle.NC)


def toggleAppLabel(app: PersistentApp) -> str:
    label_current = ""
    label_new = ""
    if isValid(app):
        app_name = get_app_name(app)
        app_label = get_app_label(app)
        label_current = app_label
        if string_good(app_label):
            label_new = ""
        else:
            label_new = app_name
        set_app_label(app, label_new)
        print(f"Toggling label for app {app_name}: '{label_current}' => '{label_new}'")
    else:
        print(f"{TextStyle.RED}ERROR: invalid app record provided{TextStyle.NC}")
    return label_new


def restoreAppLabel(app: PersistentApp):
    if isValid(app):
        app_name = get_app_name(app)
        set_app_label(app, app_name)
    else:
        print(TextStyle.RED + f"ERROR: invalid app record provided" + TextStyle.NC)


def labelAppWithGuid(app_guid: int, label: str):  # Erase title for the app with specified GUID
    app: PersistentApp
    for one_app in all_apps:
        if one_app["GUID"] == app_guid:
            app = one_app
            break
    if isValid(app):
        return labelApp(app, label)
    else:
        print(TextStyle.RED + f"ERROR: could not find app with GUID {app_guid}" + TextStyle.NC)


def labelAppNamed(app_name: str, label: str):  # Erase title for the app with specified name
    app: PersistentApp
    for one_app in all_apps:
        one_app_name = get_app_name(one_app)
        if one_app_name == app_name:
            app = one_app
            break
    if isValid(app):
        return labelApp(app, label)
    else:
        print(TextStyle.RED + f"ERROR: could not find app named {app_name}" + TextStyle.NC)


def deleteAppWithGuid(app_guid: int):
    return labelAppWithGuid(app_guid, "")


def deleteAppNamed(app_name: str):
    return labelAppNamed(app_name, "")


def deleteTitles():  # Erase all the titles of the apps in the dock
    print("\n> Erasing all titles...")
    for one_app in all_apps:
        labelApp(one_app, "")


def restoreTitles():  # Restore all the titles of the apps in the dock
    print("\n> Restoring all titles...")
    for one_app in all_apps:
        restoreAppLabel(one_app)
        # app["tile-data"]["file-label"] = app["tile-data"]["file-data"]["_CFURLString"].replace("%20", " ").split("/")[-2].replace(".app", "")


def writeChanges(): # Write the changes to the dock plist file and restart the dock
    print("> Writing changes to the dock plist file...")
    with open(dock_plist, 'wb') as fp:
        plistlib.dump(dock_plist_opened, fp)
    print("> Restarting the dock...\n")
    subprocess.run(["killall", "Dock"])

print(chr(27) + "[2J" + app_logo) # Clear the terminal screen and print the app logo
printApps() # Print the apps in the dock
print("\n{}{}MENU{}:\n\n{}{:>6}{} to erase all titles\n{}{:>6}{} to restore all titles\n{}{:>6}{} to quit the app\n".format(textStyle.underline, textStyle.BOLD, textStyle.reset, textStyle.BOLD, "'a'", textStyle.reset, textStyle.BOLD, "'r'", textStyle.reset, textStyle.BOLD, "'q'", textStyle.reset)) # Print the menu

while True: # Get the user's choice
    user_choice = input("Enter your choice: ")
    if not user_choice.lower() in ['a', 'r', 'q']: # Check if the user's choice is valid, and if not, print clear the line and ask for another choice.
        print("\033[F", end=" " * 35 + "\r", flush=True) # Clear the line if the user's choice is invalid
    elif user_choice.lower() == "a": # If the user's choice is a, erase all the titles
        deleteTitles()
        writeChanges()
        exit()
    elif user_choice.lower() == "r": # If the user's choice is r, restore all the titles 
        restoreTitles()
        writeChanges()
        exit()
    elif user_choice.lower() == "q": # If the user's choice is q, quit the app
        print("\n> Quitting the app...\n")
        exit()
           
