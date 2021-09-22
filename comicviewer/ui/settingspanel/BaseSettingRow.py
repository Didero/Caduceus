from abc import abstractmethod
from typing import TYPE_CHECKING, Any, Callable

from PySide6 import QtWidgets

from comicviewer.settings.SettingsEnum import SettingsEnum
from comicviewer.settings import SettingsStore
from comicviewer.ui import UiUtils
if TYPE_CHECKING:
	from comicviewer.ui.settingspanel.SettingsParentWidget import SettingsParentWidget

class BaseSettingRow(QtWidgets.QWidget):
	def __init__(self, parent, setting: SettingsEnum, layout: QtWidgets.QGridLayout, rowIndex: int, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.parent: SettingsParentWidget = parent
		self.setting: SettingsEnum = setting
		self.initialValue = None
		self.onChangeMethod: Callable or None = None
		# Create the UI
		layout.addWidget(QtWidgets.QLabel(setting.shortDescription), rowIndex, 0)
		self.settingWidget = self._createSettingWidget()
		layout.addWidget(self.settingWidget, rowIndex, 1)
		self.defaultButton = UiUtils.createButton("Default", lambda: self.setValue(self.setting.defaultValue), isDisabled=self.isDefaultValue())
		layout.addWidget(self.defaultButton, rowIndex, 2)
		layout.addWidget(QtWidgets.QLabel(setting.fullDescription), rowIndex, 3)
		self.updateInitialValue()

	@abstractmethod
	def _createSettingWidget(self) -> QtWidgets.QWidget:
		"""Create the actual widget where the user can change the setting"""
		pass

	@abstractmethod
	def getValue(self) -> Any:
		""":return: The currently user-set value of the setting"""
		pass

	@abstractmethod
	def setValue(self, newValue: Any):
		"""
		Set a new value as the initial value
		:param newValue: The new value to store
		"""
		pass

	def updateInitialValue(self):
		"""Retrieve the stored value for our setting, and store that as the initial value"""
		self.initialValue = SettingsStore.getSettingValue(self.setting)
		self.setValue(self.initialValue)

	def didValueChange(self) -> bool:
		""":return: True if the currently set value differs from the initial value, False if the user didn't change this setting"""
		return self.getValue() != self.initialValue

	def isDefaultValue(self) -> bool:
		""":return: True if this widget is at the default value for the setting, False otherwise"""
		return self.getValue() == self.setting.defaultValue

	def setOnChangeMethod(self, onChangeMethod: Callable):
		"""
		Store a method to be called when this setting widget gets changed by the user. The method will get passed this widget as the only argument
		:param onChangeMethod: The method that should
		"""
		self.onChangeMethod = onChangeMethod

	def onValueChanged(self, *args):
		self.defaultButton.setDisabled(self.isDefaultValue())
		if self.onChangeMethod is not None:
			self.onChangeMethod(self)
