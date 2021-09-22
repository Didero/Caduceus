import os, sys

from PySide6.QtCore import QStandardPaths


def getStoragePath() -> str:
	""":return: Where config and log files should be saved"""
	if isPortable:
		return getProgramPath()
	else:
		# '%appdata%/Roaming/Caduceus' in Windows, '~/.local/share/Caduceus' on Linux
		return QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)

def getProgramPath() -> str:
	# When run stand-alone, 'sys.path[0]' is a folder; when compiled with PyInstaller, it refers to a file. Handle both
	return sys.path[0] if os.path.isdir(sys.path[0]) else os.path.dirname(sys.path[0])


# Whether to store config files in the program's folder (portable) or in the OS's designated storage location (non-portable)
# Portable mode is enabled if a 'portable' commandline argument is passed (optionally prefixed by dashes), or if a 'portable' or 'portable.txt' file exists in the program folder
isPortable = (len(sys.argv) > 1 and sys.argv[1].lstrip('-').lower() == 'portable') or \
			os.path.isfile(os.path.join(getProgramPath(), 'portable')) or \
			os.path.isfile(os.path.join(getProgramPath(), 'portable.txt'))
