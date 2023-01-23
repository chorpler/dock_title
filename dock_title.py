import os, plistlib, math, platform, sys, subprocess, shutil

class formatareText:
   INGROSAT = '\033[1m'
   SUBLINIAT = '\033[4m'
   PRESTABILIT = '\033[0m'

subprocess.run("clear")

if platform.system() != "Darwin":
    print(formatareText.INGROSAT + formatareText.SUBLINIAT + "Error:" + formatareText.PRESTABILIT + " This script is for macOS only! Exiting..." + formatareText.PRESTABILIT + "\n")
    exit()

_fisierDockPlist = os.path.expanduser("~/Library/Preferences/com.apple.dock.plist")
_fisierBackupDockPlist = os.path.expanduser("~/Library/Preferences/com.apple.dock.plist.backup")
if not os.path.isfile(_fisierDockPlist):
    print(formatareText.INGROSAT + formatareText.SUBLINIAT + "Error:" + formatareText.PRESTABILIT + " ~/Library/Preferences/com.apple.dock.plist" + " not found. Exiting..." + formatareText.PRESTABILIT + "\n")
    exit()

_plist = plistlib.load(open(_fisierDockPlist, "rb"))
_aplicatiiPersistente = _plist["persistent-apps"]
_celMaiLungNume = 0

_numarAplicatii = 0
for _aplicatie in _aplicatiiPersistente:
    _numeAplicatie = _aplicatie["tile-data"]["file-data"]["_CFURLString"].replace("%20", " ").split("/")[-2].replace(".app", "")
    _lungimeAplicatie = len(_numeAplicatie)
    _lungimeAplicatieOptima = int(_lungimeAplicatie + 5)
    if _lungimeAplicatieOptima > _celMaiLungNume:
        _celMaiLungNume = _lungimeAplicatieOptima
    _numarAplicatii += 1

_cateTaburiNeTrebuie = math.ceil(_celMaiLungNume / 8)
_taburiSpatiu = _cateTaburiNeTrebuie * "\t"

_numarOrdine = 1
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

_liniiDelimitareSus = "\n---[ App Name \u2191]" + u"\u001b[1000D" + _taburiSpatiu + "---[ App Title \u2191]\n"
_liniiDelimitareJos = "--- "
_meniuPredefinit = "'" + formatareText.INGROSAT + "a" + formatareText.PRESTABILIT + "' to " + formatareText.SUBLINIAT + "erase all Titles" + formatareText.PRESTABILIT + "\t'" + formatareText.INGROSAT + "r" + formatareText.PRESTABILIT + "' " + formatareText.SUBLINIAT + "to restore all Titles" + formatareText.PRESTABILIT + "\n'"  + formatareText.INGROSAT + "q" + formatareText.PRESTABILIT + "' to " + formatareText.SUBLINIAT + "quit" + formatareText.PRESTABILIT

print(f"{_liniiDelimitareSus}\n{_meniuPredefinit}\n{_liniiDelimitareJos}")

while True:
    _optiuneMeniu = input("Enter your choice: ")
    if _optiuneMeniu in ['a', 'r', 'q']:
        if _optiuneMeniu == "a":
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
        elif _optiuneMeniu == "r":
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
        elif _optiuneMeniu == "q":
            sys.exit()
    else:
        print("\033[F", end=" " * 35 + "\r", flush=True)