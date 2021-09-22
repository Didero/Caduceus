import logging
from enum import Enum

from PySide6 import QtWidgets

from comicviewer.ui.settingspanel.BaseSettingRow import BaseSettingRow


class EnumSettingRow(BaseSettingRow):
	def _createSettingWidget(self) -> QtWidgets.QWidget:
		widget = QtWidgets.QComboBox()
		enumList = list(type(self.setting.defaultValue))
		widget.addItems([str(e) for e in enumList])
		widget.currentIndexChanged.connect(self.onValueChanged)
		return widget

	def getValue(self) -> Enum:
		# Since the combo box is filled with a list of enum members, getting the enum with the selected index is the selected enum
		return list(type(self.setting.defaultValue))[self.settingWidget.currentIndex()]

	def setValue(self, newValue: Enum):
		valueStr = str(newValue)
		index = self.settingWidget.findText(valueStr)
		if index == -1:
			logging.error(f"Unable to find default value entry '{newValue}' for setting {self.setting}")
		else:
			self.settingWidget.setCurrentIndex(index)
