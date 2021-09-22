import os, time

import PyInstaller.__main__

if __name__ == '__main__':
	startTime = time.perf_counter()
	basepath = os.path.dirname(__file__)
	programName = 'Caduceus'
	# TODO: Make these settings configurable
	debugMode = False

	pyInstallerArguments = [
		'main.py',
		'--name=' + programName,
		#'--onefile',  # Disabled because a single exe is slower to start than an unpacked build
		'--clean',  # Always start with a new cache
		'--noconfirm',  # Clean the 'dist' folder
		'--noconsole',  # Don't show a console window when running the exe
		'--add-data=lib' + os.pathsep + 'lib',
	]
	if not debugMode:
		# UPX compresses the resulting file(s). Slower compile but much smaller result
		upxFolder = "D:/Programs/UPX"
		if os.path.isdir(upxFolder) and os.path.isfile(os.path.join(upxFolder, 'UPX.exe')):
			pyInstallerArguments.append('--upx-dir=D:/Programs/UPX')
		else:
			print("UPX exe not found, not using UPX compression")
		# Don't show the console
		pyInstallerArguments.append('--noconsole')
	iconPath = os.path.join(basepath, 'icon.ico')
	if os.path.isfile(iconPath):
		pyInstallerArguments.append('--icon=' + iconPath)
	PyInstaller.__main__.run(pyInstallerArguments)
	print(f"Build took {time.perf_counter() - startTime} seconds")
