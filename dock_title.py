#!/usr/bin/env python3

# This is a simple script that allows you to Clear and Restore the titles of your MacOS dock's apps.
# It will not delete the Finder, Trash, or any other system apps titles.

import os
import sys
import subprocess
import platform
import pprint
import traceback
import re
import plistlib
from tabulate import tabulate, tabulate_formats

from collections import OrderedDict

from typing import Any, List, Dict, TypedDict, Optional, cast

RED = '\033[91m'
BOLD = '\033[1m'
ITALIC = '\033[3m'
UL = '\033[4m'
NOBOLD = '\033[22m'
NOITALIC = '\033[23m'
NOUL = '\033[24m'
NC = '\033[0m'

plist_file = "~/Library/Preferences/com.apple.dock.plist"
plist_file_backup = "~/Library/Preferences/com.apple.dock.plist.backup"

table_format = "fancy_outline"

try:
    import argparse
    from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
    import ntpath
    from typing import Any, AnyStr, Union, Type
    from collections.abc import Generator
    from termcolor import colored, cprint
    import colorama
    # from pypager.source import StringSource, FormattedTextSource
    # from pypager.pager import Pager
    # from prompt_toolkit import ANSI
except ImportError as e:
    print(f"{RED}{UL}ERROR:{NOUL} {str(e)}{NC}", file=sys.stderr)
    print(f"{RED}{UL}STACK TRACE:{NOUL} {traceback.format_exc()}{NC}", file=sys.stderr)
    print(f"{RED}One or more required Python packages are not installed, run the install script or 'pip install -r requirements.txt'{NC}", file=sys.stderr)
    sys.exit(1)

PROGRAM_TITLE = "DockTitle"
PROGRAM_NAME = PROGRAM_TITLE.lower()
VERSION = "2.1.0"
DEFAULT_INPUT = "/dev/stdin"
DEFAULT_SEPARATOR = " "
PADDING_LEFT = 0
PADDING_RIGHT = 2
DEFAULT_PRINT_OUTPUT = False
DEFAULT_BOLD = False
DEFAULT_PLAIN_TEXT = False
DEFAULT_QUOTE_EMPTY = False
DEFAULT_HIDE_TITLE = False
COLOR_TITLE_TEXT = "light_grey"
COLOR_TITLE_BG = "on_light_grey"
COLOR_COMMAND = "light_blue"
COLOR_ARG_REQUIRED = "light_yellow"
COLOR_ARG_OPTIONAL = "green"
COLOR_ARG_POSTL_REQ = {"color": "light_yellow", "attrs": ["bold"]}
COLOR_ARG_POSTL_OPT = {"color": "light_green", "attrs": ["bold"]}
COLOR_HELP = "blue"
COLOR_DYN_HELP = "blue"
COLOR_GROUP = "cyan"
# COLOR_DESCRIPTION = "light_magenta"
COLOR_PROGRAM_TITLE = "light_blue"
COLOR_DESCRIPTION = "yellow"


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


app_logo = r"""
   ___  ____  _______ __   __________________   ____
  / _ \/ __ \/ ___/ //_/  /_  __/  _/_  __/ /  / __/
 / // / /_/ / /__/ ,<      / / _/ /  / / / /__/ _/
/____/\____/\___/_/|_|    /_/ /___/ /_/ /____/___/

by Victor D. NEAMT
"""

#######################################################
# Log functions
#######################################################
# Define a list of colors to be used for the columns.
# Available text colors:
#     black, red, green, yellow, blue, magenta, cyan, white,
#     light_grey, dark_grey, light_red, light_green, light_yellow, light_blue,
#     light_magenta, light_cyan.
#
# Available text highlights:
#     on_black, on_red, on_green, on_yellow, on_blue, on_magenta, on_cyan, on_white,
#     on_light_grey, on_dark_grey, on_light_red, on_light_green, on_light_yellow,
#     on_light_blue, on_light_magenta, on_light_cyan.
#
# Available attributes:
#     bold, dark, underline, blink, reverse, concealed.
colorama.init()
# colors = ['red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white', 'grey', 'light_red', 'light_green']

debug = False
color_debug = "magenta"
color_error = "red"
color_warning = "yellow"
color_success = "green"
color_comment = "dark_grey"


def log(*args, **kwargs):
    print(" ".join(map(str, args)), **kwargs)


def logdbg(*args, **kwargs):
    global debug
    global color_debug
    label = "DEBUG"
    label_color = color_debug
    output_debug = debug
    if output_debug:
        print(colored(f"[{label}]", label_color), " ".join(map(str, args)), **kwargs, file=sys.stderr)


def logerr(*args, **kwargs):
    global color_error
    label = "ERROR"
    label_color = color_error
    print(colored(f"[{label}]", label_color), " ".join(map(str, args)), **kwargs, file=sys.stderr)


def logwarn(*args, **kwargs):
    global color_warning
    label = "WARNING"
    label_color = color_warning
    print(colored(f"[{label}]", label_color), " ".join(map(str, args)), **kwargs, file=sys.stderr)


Log = {
    "l": log,
    "e": logerr,
    "w": logwarn,
    "d": logdbg,
}


def exit_error(code: int):
    # Add custom error logging or messages here
    sys.exit(code)



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


def exit(code: int = 0):
    sys.exit(code)


# Check if the script is running on MacOS, and if not, exit.
if platform.system() != "Darwin":
    Log.e(f"This script is for MacOS only, exiting...")
    exit(1)

dock_plist = os.path.expanduser(plist_file)  # Define the path to the dock plist file
dock_plist_backup = os.path.expanduser(plist_file_backup)  # Define the path to the dock plist backup file

if not os.path.exists(dock_plist):  # Check if the dock plist file exists, and if not, exit.
    Log.e(f"Dock plist file '{dock_plist}' not found, exiting...")
    exit(1)

if not os.path.exists(dock_plist_backup):  # Check if the dock plist backup file exists, and if not, create it.
    subprocess.call(["cp", dock_plist, dock_plist_backup])
else:  # If the dock plist backup file exists, detele it and create anther backup.
    subprocess.call(["rm", dock_plist_backup])
    subprocess.call(["cp", dock_plist, dock_plist_backup])

dock_plist_opened = plistlib.load(open(dock_plist, "rb"))  # Open the dock plist file in read mode

if "persistent-apps" in dock_plist_opened:  # Check if there are any persistent apps in the dock, and if not, exit.
    persistent_apps = cast(PersistentApps, dock_plist_opened["persistent-apps"])
else:
    Log.e(f"No apps found in the dock, exiting...")
    exit(1)

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


def string_bad(value: Any) -> bool:
    return not string_good(value)


def strip_quotes(s: str) -> str:
    if string_bad(s):
        return None
    # unquoted = re.sub(r"['\"`]+", "", s)
    unquoted = s.strip("\"'` \t")
    if re.search(r"\s", unquoted):
        return f"\"{unquoted}\""
    else:
        return unquoted
    # if (s.startswith("'") and s.endswith("'")) or (s.startswith('"') and s.endswith('"')) or (s.startswith("`") and s.endswith("`")):
    #     return s[1:-1]
    # return s


def terminal_clear():
    # Print the following ANSI escape codes:
    # - chr(27) + "[2J" to clear screen
    # - chr(27) + "[H" to reset cursor position to top left
    # Specify end="" to avoid printing a newline
    print(f"\x1b[2J\x1b[H", end="")


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


def getAppList() -> PersistentAppsRecords:
    global app_map
    app_map = dict()
    if not list_good(all_apps):
        print(TextStyle.RED + "Error: no apps found in doc" + TextStyle.NC)
        exit(1)
    for i, app in enumerate(all_apps):
        app_map[i] = app
    # PRETTY.pprint(f"Adding app {app_number}")
    return app_map


def getAppNameList() -> list[str]:
    global all_apps
    app_names = list()
    for i, app in enumerate(all_apps):
        app_name = get_app_name(app)
        if string_good(app_name):
            app_names.append(app_name)
        else:
            app_names.append("UNKNOWN")
    return app_names

def writeChanges():  # Write the changes to the dock plist file and restart the dock
    print("> Writing changes to the dock plist file...")
    with open(dock_plist, 'wb') as fp:
        plistlib.dump(dock_plist_opened, fp)
    print("> Restarting the dock...\n")
    subprocess.run(["killall", "Dock"])


def printApps():
    global app_map
    app_map = getAppList()
    if not dict_good(app_map):
        # Check if there are any apps in the dock, and if not, exit.
        logerr(f"No apps found in the dock. Exiting...")
        exit(1)
    # print("{}{}{:>4} {} {:>41}{}\n".format(TextStyle.UNDERLINE, TextStyle.BOLD, "No.", "App Name", "App Title", TextStyle.reset))
    # table = [['col 1', 'col 2', 'col 3', 'col 4'], [1, 2222, 30, 500], [4, 55, 6777, 1]]
    # print(tabulate(table, headers='firstrow', tablefmt='fancy_grid'))
    table = [
        ['#', 'App Name', 'App Title']
    ]
    # print(f"{TextStyle.UNDERLINE}{TextStyle.BOLD}{'No.':>4} {'App Name'} {'App Title':>41}{TextStyle.NC}")
    for app_number, app in app_map.items():
        app_name = get_app_name(app)
        # app_name = app["tile-data"]["file-data"]["_CFURLString"].replace("%20", " ").split("/")[-2].replace(".app", "")
        if "file-label" in app["tile-data"]:
            app_title = app["tile-data"]["file-label"]
        else:
            app_title = ""
        # print("{:>3}. {} {:>40}".format(app_number+1, app_name, app_title))
        # print(f"{app_number+1:>3}. {app_name} {app_title:>40}")
        table.append([app_number+1, app_name, app_title])
        # app_number += 1
    print(tabulate(table, headers='firstrow', tablefmt=table_format, colalign=('right', 'right', 'left')))


def refreshScreen():
    # global app_map
    # app_map = getAppList()
    terminal_clear()
    printApps()
    print(f"{TextStyle.UNDERLINE}{TextStyle.BOLD}MENU{TextStyle.NC}: {TextStyle.BOLD}{'a':>6}{TextStyle.NC} {'(erase all)':>12} {TextStyle.BOLD}{'r':>6}{TextStyle.NC} {'(restore all)':>12}")
    print(f"      {TextStyle.BOLD}{'s':>6}{TextStyle.NC} {'(save all)':>12} {TextStyle.BOLD}{'q':>6}{TextStyle.NC} (quit)\n")
    # print("\n{}{}MENU{}:\n\n{}{:>6}{} to erase all titles\n{}{:>6}{} to restore all titles\n{}{:>6}{} to quit the app\n".format(
    # TextStyle.UNDERLINE, TextStyle.BOLD, TextStyle.reset, TextStyle.BOLD, "'a'", TextStyle.reset, TextStyle.BOLD, "'r'",
    # print(f"{TextStyle.UNDERLINE}{TextStyle.BOLD}MENU{TextStyle.NC}:\n\n{TextStyle.BOLD}{'a':>6}{TextStyle.NC} to erase all titles\n" \
    # "{TextStyle.BOLD}{'r':>6}{TextStyle.NC} to restore all titles\n{TextStyle.BOLD}{'q':>6}{TextStyle.NC} to quit the app\n")

#
#
# terminal_clear()
# print(app_logo)
# # print(chr(27) + "[2J" + app_logo)  # Clear the terminal screen and print the app logo
#
# printApps()  # Print the apps in the dock
# print("\n{}{}MENU{}:\n\n{}{:>6}{} to erase all titles\n{}{:>6}{} to restore all titles\n{}{:>6}{} to quit the app\n".format(
# TextStyle.UNDERLINE, TextStyle.BOLD, TextStyle.reset, TextStyle.BOLD, "'a'", TextStyle.reset, TextStyle.BOLD, "'r'",
# TextStyle.reset, TextStyle.BOLD, "'q'", TextStyle.reset))  # Print the menu


app_map = getAppList()
app_numbers = list(app_map.keys())
app_numbers = list(map(lambda x: str(x+1), app_numbers))

dirty = False

# print(f"App numbers: {' '.join(app_numbers)}")
# refreshScreen()


class UsageFormatter(argparse.HelpFormatter):
    def __init__(self,
                 prog,
                 indent_increment=2,
                 max_help_position=24,
                 width=None):
        self.SUPPRESS = '==SUPPRESS=='
        self.OPTIONAL = '?'
        self.ZERO_OR_MORE = '*'
        self.ONE_OR_MORE = '+'
        self.PARSER = 'A...'
        self.REMAINDER = '...'
        self._UNRECOGNIZED_ARGS_ATTR = '_unrecognized_args'
        super(UsageFormatter, self).__init__(prog, indent_increment, max_help_position, width)

    # use defined argument order to display usage
    def _format_usage(self, usage, actions, groups, prefix):
        if prefix is None:
            prefix = 'Usage:\n  '

        prefix = colored(prefix, COLOR_GROUP)
        cmd = colored(self._prog, COLOR_COMMAND)

        # if usage is specified, use that
        if usage is not None:
            usage = usage % dict(prog=cmd)
            # usage = cmd

        # if no optionals or positionals are available, usage is just prog
        elif usage is None and not actions:
            # usage = '%(prog)s' % dict(prog=self._prog)
            usage = f"{cmd}"
        elif usage is None:
            # prog = '%(prog)s' % dict(prog=self._prog)
            prog = cmd
            # build full usage string
            action_usage = self._format_actions_usage(actions, groups)  # NEW
            usage = ' '.join([s for s in [prog, action_usage] if s])
            # omit the long line wrapping code
        # prefix with 'usage:'
        # return '%s%s\n\n' % (prefix, usage)
        return f"{prefix}{usage}\n"

    def _format_actions_usage(self, actions, groups):
        # find group indices and identify actions in groups
        CR = COLOR_ARG_REQUIRED
        CO = COLOR_ARG_OPTIONAL
        AR1 = "("
        AR2 = ")"
        AO1 = "["
        AO2 = "]"
        R1 = CR + AR1
        R2 = AR2 + NC
        O1 = CO + AO1
        O2 = AO2 + NC
        group_actions = set()
        inserts = {}
        for group in groups:
            if not group._group_actions:
                raise ValueError(f'empty group {group}')

            try:
                start = actions.index(group._group_actions[0])
            except ValueError:
                continue
            else:
                end = start + len(group._group_actions)
                if actions[start:end] == group._group_actions:
                    for action in group._group_actions:
                        group_actions.add(action)
                    if not group.required:
                        if start in inserts:
                            inserts[start] += ' ['
                            # inserts[start] += ' ' + O1
                        else:
                            inserts[start] = '['
                            # inserts[start] = O1
                        if end in inserts:
                            inserts[end] += ']'
                            # inserts[end] += O2
                        else:
                            inserts[end] = ']'
                            # inserts[end] = O2
                    else:
                        if start in inserts:
                            inserts[start] += ' ('
                            # inserts[start] += ' ' + R1
                        else:
                            inserts[start] = '('
                            # inserts[start] = R1
                        if end in inserts:
                            inserts[end] += ')'
                            # inserts[end] += R2
                        else:
                            inserts[end] = ')'
                            # inserts[end] = R2
                    for i in range(start + 1, end):
                        inserts[i] = '|'

        # collect all actions format strings
        parts = []
        for i, action in enumerate(actions):

            # suppressed arguments are marked with None
            # remove | separators for suppressed arguments
            if action.help is self.SUPPRESS:
                parts.append(None)
                if inserts.get(i) == '|':
                    inserts.pop(i)
                elif inserts.get(i + 1) == '|':
                    inserts.pop(i + 1)

            # produce all arg strings
            elif not action.option_strings:
                default = self._get_default_metavar_for_positional(action)
                part = self._format_args(action, default)

                # if it's in a group, strip the outer []
                if action in group_actions:
                    # if part[0] == '[' and part[-1] == ']':
                    if part[0] == '[' and part[-1] == ']':
                        part = part[1:-1]
                    elif part.startswith(O1) and part.endswith(O2):
                        part = part.strip(O1).strip(O2)

                if not action.required:
                    # part = colored(part, COLOR_ARG_OPTIONAL)
                    part = colored(part, **COLOR_ARG_POSTL_OPT)
                else:
                    part = colored(part, **COLOR_ARG_POSTL_OPT)
                # add the action string to the list
                parts.append(part)

            # produce the first way to invoke the option in brackets
            else:
                option_string = action.option_strings[0]

                # if the Optional doesn't take a value, format is:
                #    -s or --long
                if action.nargs == 0:
                    part = action.format_usage()
                    # part = colored(part, COLOR_ARG_OPTIONAL)

                # if the Optional takes a value, format is:
                #    -s ARGS or --long ARGS
                else:
                    default = self._get_default_metavar_for_optional(action)
                    args_string = self._format_args(action, default)
                    part = '%s %s' % (option_string, args_string)

                # make it look optional if it's not required or in a group
                if not action.required and action not in group_actions:
                    # part = '[%s]' % part
                    # part = f"[{colored(part, COLOR_ARG_OPTIONAL)}]"
                    part = colored(f"[{part}]", COLOR_ARG_OPTIONAL)
                elif not action.required:
                    # Color it optional
                    part = colored(f"[{part}]", COLOR_ARG_OPTIONAL)
                elif action.required:
                    part = colored(f"({part})", COLOR_ARG_REQUIRED)

                # add the action string to the list
                parts.append(part)

        # insert things at the necessary indices
        for i in sorted(inserts, reverse=True):
            parts[i:i] = [inserts[i]]

        # join all the action items with spaces
        text = ' '.join([item for item in parts if item is not None])

        # clean up separators for mutually exclusive groups
        open = r'[\[(]'
        close = r'[\])]'
        text = re.sub(r'(%s) ' % open, r'\1', text)
        text = re.sub(r' (%s)' % close, r'\1', text)
        text = re.sub(r'%s *%s' % (open, close), r'', text)
        text = re.sub(r'\(([^|]*)\)', r'\1', text)
        text = text.strip()

        # return the text
        return text


def run_interactive():
    while True:  # Get the user's choice
        refreshScreen()
        input_prompt = f"{TextStyle.CYAN}Enter your choice:{TextStyle.NC} "
        if dirty:
            input_prompt = f"{TextStyle.CYAN}Enter your choice{TextStyle.NC} {TextStyle.YELLOW}(unsaved changes){TextStyle.NC}: "
        user_choice = input(input_prompt)
        input_char = user_choice.lower()[0] if string_good(user_choice) else 'n'  # No action by default
        if input_char in app_numbers:
            # Specific app number, toggle it
            app_index = int(user_choice) - 1
            single_app = app_map[app_index]
            dirty = True
            toggleAppLabel(single_app)
            # print()
            # writeChanges()
        elif input_char not in ['a', 'r', 's', 'q']:  # Check if the user's choice is valid, and if not, print clear the line and ask for another choice.
            print("\033[F", end=" " * 35 + "\r", flush=True)  # Clear the line if the user's choice is invalid
        elif input_char == "s":  # If the user's choice is s, save changes
            writeChanges()
            dirty = False
            exit(0)
        elif input_char == "a":  # If the user's choice is a, erase all the titles
            deleteTitles()
            dirty = True
            # writeChanges()
            # exit(0)
        elif input_char == "r":  # If the user's choice is r, restore all the titles
            restoreTitles()
            dirty = True
            # writeChanges()
            # exit(0)
        elif input_char == "q":  # If the user's choice is q, quit the app
            if dirty:
                confirm_exit = input(f"\n{TextStyle.YELLOW}> Changes made, do you want to save? (y/n/c[ancel]){TextStyle.NC} ")
                user_char = confirm_exit.lower()[0] if string_good(confirm_exit) else 'c'
                if user_char not in ['y', 'n', 'c']:
                    print("\033[F", end=" " * 35 + "\r", flush=True)  # Clear the line if the user's choice is invalid
                elif user_char == 'y':
                    print(f"\n{TextStyle.BOLD}> Saving changes ...{TextStyle.NC}\n")
                    writeChanges()
                    dirty = False
                    print(f"\n{TextStyle.BOLD}> Changes saved, quitting ...{TextStyle.NC}\n")
                    exit(0)
                elif user_char == 'n':
                    print(f"\n{TextStyle.YELLOW}> Quitting without saving ...{TextStyle.NC}\n")
                    exit(0)
                else:
                    # Cancel, return to menu
                    pass
            else:
                print("\n> Quitting ...\n")
                exit(0)


def format_help(self: ArgumentParser, groups: list[Any] = None):
    # self == parser

    if groups is None:
        groups = self._action_groups

    formatter = self._get_formatter()

    # description
    formatter.add_text(self.description)

    # Command usage (customized)
    # cmd = sys.argv[0]
    cmd = self.prog
    cmd_text = colored(cmd, COLOR_COMMAND)

    arg_text = ""
    usage_text = colored("Usage", COLOR_GROUP) + ":\n  "

    # Usage line
    formatter.add_usage(None, self._actions, self._mutually_exclusive_groups, prefix=usage_text)
    # formatter.add_usage(self.usage, self._actions, self._mutually_exclusive_groups, prefix=usage_text)
    # formatter.add_usage(, None, None)

    # positionals, optionals and user-defined groups
    for action_group in groups:
        formatter.start_section(action_group.title)
        formatter.add_text(action_group.description)
        formatter.add_arguments(action_group._group_actions)
        formatter.end_section()

    # epilog
    formatter.add_text(self.epilog)

    # determine help from format above
    return formatter.format_help()


def show_usage(argument_parser):
    if argument_parser is None or not isinstance(argument_parser, argparse.ArgumentParser):
        alert = f"show_usage: invalid parser provided, must provide valid ArgumentParser object"
        raise TypeError(alert)
    # argument_parser.print_help()
    # newparser = argparse.ArgumentParser(argument_parser)
    # newparser.formatter_class = UsageFormatter
    print("\n", end='')
    print(format_help(argument_parser))
    # print(format_help(newparser))
    print("\n", end='')


if __name__ == "__main__":
    '''
    DockTitle: show or change the popup label for persistent apps in the macOS Dock
    '''

    version_string = f"v{VERSION}"
    version_docstring = f"{PROGRAM_NAME} {version_string}"
    version_title = f"{PROGRAM_TITLE} {version_string}"

    program_title = ITALIC + colored(version_title, COLOR_PROGRAM_TITLE, attrs=["bold"]) + NOITALIC
    program_docstring = colored(f"Show or change the popup label for persistent apps in the macOS Dock", COLOR_DESCRIPTION, attrs=["bold"])
    program_docstring = f"{program_title}: {program_docstring}"
    parser = argparse.ArgumentParser(description=program_docstring, add_help=False, formatter_class=UsageFormatter)
    positional_args = parser.add_argument_group(colored("Arguments", COLOR_GROUP))
    action_args = parser.add_argument_group(colored("Options (actions)", COLOR_GROUP))
    output_args = parser.add_argument_group(colored("Options (output)", COLOR_GROUP))
    meta_args = parser.add_argument_group(colored("Options (miscellaneous)", COLOR_GROUP))
    # positional_args.add_argument('input_file', nargs='?', default=DEFAULT_INPUT, help=colored("Input file path. If not provided, will attempt to read data from stdin", COLOR_HELP))
    positional_args.add_argument('input_file', nargs='?', help=colored("Input file path. If not provided, will attempt to read data from standard input.", COLOR_HELP))
    # query_args.add_argument('-i', '--input', required=False, type=str, dest="input_file", default=None, help=colored("Input TSV/CSV file", COLOR_HELP))
    action_args.add_argument('-t', '--toggle', required=False, type=str, dest="arg_toggle", default=None, help=colored("Toggle: given a list of numbers, toggle the title of the apps at those positions", COLOR_HELP))
    action_args.add_argument('-r', '--remove', required=False, type=str, dest="arg_remove", default=None, help=colored("Remove: given a list of numbers, remove the title of the apps at those positions", COLOR_HELP))
    action_args.add_argument('-e', '--enable', required=False, type=str, dest="arg_enable", default=None, help=colored("Enable: given a list of numbers, enable the title of the apps at those positions", COLOR_HELP))
    action_args.add_argument('-l', '--list', required=False, dest="arg_list", action='store_true', default=False, help=colored("List: show list of current persistent apps in Dock", COLOR_HELP))
    meta_args.add_argument('-d', '--debug', required=False, dest="debug", action='store_true', help=colored("Show debug information and intermediate steps.", COLOR_HELP))
    meta_args.add_argument('-v', '--version', action='version', version=version_docstring, help=colored("Show program's version number and exit.", COLOR_HELP))
    meta_args.add_argument('-h', '--help', required=False, dest="show_help", action='store_true', help=colored("Show this help message and exit.", COLOR_HELP))

    inpArgs = parser.parse_args()
    show_help = inpArgs.show_help
    if len(sys.argv) < 2:
        # if not sys.stdin.isatty():
        #     # Input available on stdin, use that instead of filename
        #     reading_from_stdin = True
        # else:
            # No input available on stdin, show usage and exit
        show_usage(parser)
        exit_error(1)
    if show_help:
        show_usage(parser)
        exit_error(0)

    debug = inpArgs.debug
    arg_list = inpArgs.arg_list
    title_toggle = strip_quotes(inpArgs.arg_toggle) if string_good(inpArgs.arg_toggle) else None
    title_remove = strip_quotes(inpArgs.arg_remove) if string_good(inpArgs.arg_remove) else None
    title_enable = strip_quotes(inpArgs.arg_enable) if string_good(inpArgs.arg_enable) else None

    if arg_list:
        print(", ".join(getAppNameList()))
        exit_error(0)

    run_interactive()
