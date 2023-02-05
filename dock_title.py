# This is a simple script that allows you to clear or restore the titles of the apps in the macOS Dock.
import os, plistlib, math, platform, sys, subprocess, shutil # Import the required modules

# Define the text formatting
class formatareText:
   INGROSAT = '\033[1m'
   SUBLINIAT = '\033[4m'
   PRESTABILIT = '\033[0m'

subprocess.run("clear") # Clear the terminal

# Check if the script is running on macOS. If not, exit.
if platform.system() != "Darwin":
    print(formatareText.INGROSAT + formatareText.SUBLINIAT + "Error:" + formatareText.PRESTABILIT + " This script is for macOS only! Exiting..." + formatareText.PRESTABILIT + "\n")
    exit()

# Define the Dock plist file path and the backup file path
_fisierDockPlist = os.path.expanduser("~/Library/Preferences/com.apple.dock.plist")
_fisierBackupDockPlist = os.path.expanduser("~/Library/Preferences/com.apple.dock.plist.backup")

# Check if the Dock plist file exists. If not, exit.
if not os.path.isfile(_fisierDockPlist):
    print(formatareText.INGROSAT + formatareText.SUBLINIAT + "Error:" + formatareText.PRESTABILIT + " ~/Library/Preferences/com.apple.dock.plist" + " not found. Exiting..." + formatareText.PRESTABILIT + "\n")
    exit()

# Open the Dock plist file and get the persistent-apps list
_plist = plistlib.load(open(_fisierDockPlist, "rb"))
_aplicatiiPersistente = _plist["persistent-apps"]

_celMaiLungNume = 0 # Set the longest app name length to 0
_numarAplicatii = 0 # Set the number of apps to 0

# Get the longest app name length
for _aplicatie in _aplicatiiPersistente:
    _numeAplicatie = _aplicatie["tile-data"]["file-data"]["_CFURLString"].replace("%20", " ").split("/")[-2].replace(".app", "")
    _lungimeAplicatie = len(_numeAplicatie)
    _lungimeAplicatieOptima = int(_lungimeAplicatie + 5)
    if _lungimeAplicatieOptima > _celMaiLungNume:
        _celMaiLungNume = _lungimeAplicatieOptima
    _numarAplicatii += 1

_cateTaburiNeTrebuie = math.ceil(_celMaiLungNume / 8) # Calculate the number of tabs needed
_taburiSpatiu = _cateTaburiNeTrebuie * "\t" # Create the tabs in a variable

_numarOrdine = 1 # Set the order number to 1

# Print the apps list and the file labels
for _aplicatie in _aplicatiiPersistente:
    _numeAplicatie = _aplicatie["tile-data"]["file-data"]["_CFURLString"].replace("%20", " ").split("/")[-2].replace(".app", "")
    if "file-label" in _aplicatie["tile-data"]:
        _etichetaFisier = "- " + _aplicatie["tile-data"]["file-label"]
    else:
        _etichetaFisier = "- "
    _lungimeNrOrdine = len(str(_numarOrdine))
    if _lungimeNrOrdine < 2:
        _punctSiSpatiu = ".  "
    else:
        _punctSiSpatiu = ". "
    print(str(_numarOrdine) + _punctSiSpatiu + formatareText.INGROSAT + _numeAplicatie + formatareText.PRESTABILIT + u"\u001b[1000D" + _taburiSpatiu + _etichetaFisier)
    _numarOrdine += 1

# Print the menu
_liniiDelimitareSus = "\n---[ App Name \u2191]" + u"\u001b[1000D" + _taburiSpatiu + "---[ App Title \u2191]\n"
_liniiDelimitareJos = "--- "
_meniuPredefinit = "'" + formatareText.INGROSAT + "a" + formatareText.PRESTABILIT + "' to " + formatareText.SUBLINIAT + "erase all Titles" + formatareText.PRESTABILIT + "\t'" + formatareText.INGROSAT + "r" + formatareText.PRESTABILIT + "' " + formatareText.SUBLINIAT + "to restore all Titles" + formatareText.PRESTABILIT + "\n'"  + formatareText.INGROSAT + "q" + formatareText.PRESTABILIT + "' to " + formatareText.SUBLINIAT + "quit" + formatareText.PRESTABILIT
print(f"{_liniiDelimitareSus}\n{_meniuPredefinit}\n{_liniiDelimitareJos}")

# Get the user's choice
while True:
    _optiuneMeniu = input("Enter your choice: ")
    if _optiuneMeniu in ['a', 'r', 'q']: # Check if the user's choice is valid
        if _optiuneMeniu == "a": # Erase all Titles
            print("\n> Erasing all Titles...")
            for _aplicatie in _aplicatiiPersistente:
                _aplicatie["tile-data"]["file-label"] = ""
            if os.path.isfile(_fisierBackupDockPlist):
                print("> Removing the old backup file...")
                os.remove(_fisierBackupDockPlist)
            print("> Backing up the Dock plist...")
            shutil.copyfile(_fisierDockPlist, _fisierBackupDockPlist)
            with open(_fisierDockPlist, 'wb') as fp:
                plistlib.dump(_plist, fp)
            print ("> Restarting the Dock...")
            subprocess.run(["killall", "Dock"])
            sys.exit()
        elif _optiuneMeniu == "r": # Restore all Titles
            print("\n> Restoring all Titles...")
            for _aplicatie in _aplicatiiPersistente:
                _aplicatie["tile-data"]["file-label"] = _aplicatie["tile-data"]["file-data"]["_CFURLString"].replace("%20", " ").split("/")[-2].replace(".app", "")
            if os.path.isfile(_fisierBackupDockPlist):
                print("> Removing the old backup file...")
                os.remove(_fisierBackupDockPlist)
            print("> Backing up the Dock plist...")
            shutil.copyfile(_fisierDockPlist, _fisierBackupDockPlist)
            with open(_fisierDockPlist, 'wb') as fp:
                plistlib.dump(_plist, fp)
            print ("> Restarting the Dock...")
            subprocess.run(["killall", "Dock"])
            sys.exit()
        elif _optiuneMeniu == "q": # Quit
            sys.exit()
    else:
        print("\033[F", end=" " * 35 + "\r", flush=True) # Clear the line