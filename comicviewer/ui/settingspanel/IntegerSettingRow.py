from PySide6 import QtWidgets

from comicviewer.ui.settingspanel.BaseSettingRow import BaseSettingRow


class IntegerSettingRow(BaseSettingRow):
	def _createSettingWidget(self) -> QtWidgets.QSpinBox:
		widget = QtWidgets.QSpinBox()
		widget.valueChanged.connect(self.onValueChanged)
		return widget

	def getValue(self) -> int:
		return self.settingWidget.value()

	def setValue(self, newValue: int):
		self.settingWidget.setValue(newValue)
