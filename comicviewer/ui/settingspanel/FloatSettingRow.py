from PySide6 import QtWidgets

from comicviewer.ui.settingspanel.BaseSettingRow import BaseSettingRow


class FloatSettingRow(BaseSettingRow):
	def _createSettingWidget(self) -> QtWidgets.QDoubleSpinBox:
		widget = QtWidgets.QDoubleSpinBox()
		widget.setSingleStep(0.05)
		widget.valueChanged.connect(self.onValueChanged)
		return widget

	def getValue(self) -> float:
		return self.settingWidget.value()

	def setValue(self, newValue: float):
		self.settingWidget.setValue(newValue)
