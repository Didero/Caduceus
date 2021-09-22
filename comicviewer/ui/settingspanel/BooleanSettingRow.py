from PySide6 import QtWidgets

from comicviewer.ui.settingspanel.BaseSettingRow import BaseSettingRow

class BooleanSettingRow(BaseSettingRow):
	def _createSettingWidget(self) -> QtWidgets.QCheckBox:
		widget = QtWidgets.QCheckBox()
		widget.stateChanged.connect(self.onValueChanged)
		return widget

	def getValue(self) -> bool:
		return self.settingWidget.isChecked()

	def setValue(self, newValue: bool):
		self.settingWidget.setChecked(newValue)
