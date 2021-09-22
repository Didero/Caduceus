import json, logging, os
from enum import Enum
from typing import Any, Dict

from comicviewer.files import FileUtils
from comicviewer.settings.SettingsEnum import SettingsEnum


_currentValues: Dict[str, Any] = {}

_settingsFilePath = os.path.join(FileUtils.getStoragePath(), 'settings.json')

def getSettingValue(setting: SettingsEnum):
	if setting.name not in _currentValues:
		return setting.defaultValue
	if isinstance(setting.defaultValue, Enum) and not isinstance(_currentValues[setting.name], Enum):
		# First time this Enum setting is retrieved after being loaded from file, convert it from a string to the right Enum value
		enumClass = type(setting.defaultValue)
		currentEnumEntryName = _currentValues[setting.name]
		for name, enumEntry in enumClass.__members__.items():
			# Update the stored enum name entry to the actual enum entry
			if name == currentEnumEntryName:
				_currentValues[setting.name] = enumEntry
				break
		else:
			# If no matching name was found, revert to the default setting value
			logging.error(f"No matching enum entry found for value '{currentEnumEntryName}' for setting {setting}, reverting to default value")
			_currentValues.pop(setting.name, None)
			return setting.defaultValue
	return _currentValues[setting.name]

def setSettingValue(setting: SettingsEnum, value, shouldSaveSettings=True):
	# If the new value is the default value, no need to store it
	if value == setting.defaultValue:
		_currentValues.pop(setting.name, None)
	else:
		_currentValues[setting.name] = value
	if shouldSaveSettings:
		saveSettings()

def updateSettingValues(newSettingValues: Dict[SettingsEnum, Any]):
	for setting, value in newSettingValues.items():
		setSettingValue(setting, value, False)
	saveSettings()

def saveSettings():
	if not _currentValues:
		# If we don't have any values to save, delete the settings file
		if os.path.isfile(_settingsFilePath):
			os.remove(_settingsFilePath)
	else:
		# Create the settings folder if it doesn't exist yet
		if not os.path.isdir(FileUtils.getStoragePath()):
			os.makedirs(FileUtils.getStoragePath())
		# Convert values if necessary
		settingsToSave = {}
		for setting, value in _currentValues.items():
			if isinstance(value, Enum):
				settingsToSave[setting] = value.name
			else:
				settingsToSave[setting] = value
		try:
			with open(_settingsFilePath, 'w') as settingsFile:
				json.dump(settingsToSave, settingsFile)
		except Exception as e:
			logging.error(f"Saving the settings file to '{_settingsFilePath}' failed with exception {type(e)}: {e}")

def _loadSettings():
	global _currentValues
	_currentValues = {}
	if os.path.isfile(_settingsFilePath):
		try:
			with open(_settingsFilePath, 'r') as settingsFile:
				_currentValues = json.load(settingsFile)
		except Exception as e:
			logging.error(f"Loading the settings file failed with a '{type(e)}' exception: {e}")


_loadSettings()
