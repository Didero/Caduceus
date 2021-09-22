from typing import TYPE_CHECKING, Dict, Any

from PySide6 import QtWidgets

from comicviewer.settings.SettingsEnum import SettingsEnum
from comicviewer.settings import SettingsStore
from comicviewer.ui.settingspanel import SettingRowFactory
from comicviewer.ui import UiUtils
if TYPE_CHECKING:
	from comicviewer import MainController
	from comicviewer.ui.settingspanel.BaseSettingRow import BaseSettingRow

class SettingsParentWidget(QtWidgets.QWidget):
	def __init__(self, controller, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.controller: MainController = controller
		mainLayout = QtWidgets.QHBoxLayout()
		self.setLayout(mainLayout)
		self._shouldHandleSettingWidgetChange = True

		# Create the buttons before the settings widgets, because those widgets call our button update method, so we need the buttons to exist
		buttonLayout = QtWidgets.QHBoxLayout()
		self._saveButton = UiUtils.createButton("Save", self._saveSettings, buttonLayout, isDisabled=True)
		self._cancelButton = UiUtils.createButton("Cancel", self._undoChanges, buttonLayout, isDisabled=True)
		self._defaultsButton = UiUtils.createButton("Defaults", self._setToDefaults, buttonLayout, tooltipText="Reset settings to default values")

		gridLayout = QtWidgets.QGridLayout()
		self.initialValues: Dict[SettingsEnum, Any] = {}
		self.settingToWidget: Dict[SettingsEnum, BaseSettingRow] = {}
		rowIndex = 0
		for rowIndex, setting in enumerate(SettingsEnum):
			# Some settings shouldn't be displayed in this panel
			if setting.isHidden:
				continue
			self.settingToWidget[setting] = SettingRowFactory.getSettingRowClassForSetting(setting)(self, setting, gridLayout, rowIndex)
			self.initialValues[setting] = SettingsStore.getSettingValue(setting)
			self.settingToWidget[setting].setOnChangeMethod(self.onSettingWidgetChanged)
		gridLayout.addLayout(buttonLayout, rowIndex + 1, 0, 1, 2)
		mainLayout.addLayout(gridLayout)
		mainLayout.addStretch(1)

	def _saveSettings(self):
		settingsToSave = {}
		# Find all the changed settings we need to update
		for setting, widget in self.settingToWidget.items():
			if widget.didValueChange():
				settingsToSave[setting] = widget.getValue()
		if settingsToSave:
			SettingsStore.updateSettingValues(settingsToSave)
			# Update the initial values of all the saved settings
			for setting in settingsToSave:
				self.settingToWidget[setting].updateInitialValue()
			self.controller.onSettingsChanged(settingsToSave.keys())
			self._saveButton.setEnabled(False)
			self._cancelButton.setEnabled(False)

	def _undoChanges(self):
		self._shouldHandleSettingWidgetChange = False
		for setting, widget in self.settingToWidget.items():
			if widget.didValueChange():
				widget.setValue(widget.initialValue)
		self._shouldHandleSettingWidgetChange = True
		self.onSettingWidgetChanged()

	def _setToDefaults(self):
		self._shouldHandleSettingWidgetChange = False
		for setting, widget in self.settingToWidget.items():
			widget.setValue(setting.defaultValue)
		self._shouldHandleSettingWidgetChange = True
		self.onSettingWidgetChanged()

	def onSettingWidgetChanged(self, changedWidget=None):
		"""
		Called whenever the value of one of our setting widgets changed
		:param changedWidget: The widget that changed, or None if no particular widget was changed
		"""
		if not self._shouldHandleSettingWidgetChange:
			return
		# Update whether the Save/Cancel/Defaults button are enabled
		haveSettingsChanged = False
		hasNonDefaultSetting = False
		if changedWidget is not None:
			if changedWidget.didValueChange():
				haveSettingsChanged = True
			if not changedWidget.isDefaultValue():
				hasNonDefaultSetting = True
		if not haveSettingsChanged or not hasNonDefaultSetting:
			for widget in self.settingToWidget.values():
				if widget == changedWidget:
					continue
				if not haveSettingsChanged and widget.didValueChange():
					haveSettingsChanged = True
				if not hasNonDefaultSetting and not widget.isDefaultValue():
					hasNonDefaultSetting = True
				# If we know we need to enable both buttons, no need to keep checking
				if haveSettingsChanged and hasNonDefaultSetting:
					break
		self._saveButton.setEnabled(haveSettingsChanged)
		self._cancelButton.setEnabled(haveSettingsChanged)
		self._defaultsButton.setEnabled(hasNonDefaultSetting)
