from typing import Type
from enum import Enum

from comicviewer.settings.SettingsEnum import SettingsEnum
from comicviewer.ui.settingspanel.BaseSettingRow import BaseSettingRow
from comicviewer.ui.settingspanel.BooleanSettingRow import BooleanSettingRow
from comicviewer.ui.settingspanel.IntegerSettingRow import IntegerSettingRow
from comicviewer.ui.settingspanel.FloatSettingRow import FloatSettingRow
from comicviewer.ui.settingspanel.EnumSettingRow import EnumSettingRow


def getSettingRowClassForSetting(setting: SettingsEnum) -> Type[BaseSettingRow]:
	if isinstance(setting.defaultValue, bool):
		return BooleanSettingRow
	elif isinstance(setting.defaultValue, int):
		return IntegerSettingRow
	elif isinstance(setting.defaultValue, float):
		return FloatSettingRow
	elif isinstance(setting.defaultValue, Enum):
		return EnumSettingRow
	else:
		raise NotImplementedError(f"Setting type {type(setting.defaultValue)} for setting {setting} is not supported")
