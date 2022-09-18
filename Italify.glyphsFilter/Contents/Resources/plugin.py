# encoding: utf-8

###########################################################################################################
#
#
#	Filter with dialog Plugin
#
#	Read the docs:
#	https://github.com/schriftgestalt/GlyphsSDK/tree/master/Python%20Templates/Filter%20with%20Dialog
#
#	For help on the use of Interface Builder:
#	https://github.com/schriftgestalt/GlyphsSDK/tree/master/Python%20Templates
#
#
###########################################################################################################

from __future__ import division, print_function, unicode_literals
import objc
from GlyphsApp import *
from GlyphsApp.plugins import *
from math import sin, cos, tan, radians, pi


class Italify(FilterWithDialog):

	# The NSView object from the User Interface. Keep this here!
	dialog = objc.IBOutlet()

	# Text field in dialog
	angleTextBox = objc.IBOutlet()
	resetAngleButton = objc.IBOutlet()
	ratioSlider = objc.IBOutlet()
	addExtremesCheckBox = objc.IBOutlet()

	@objc.python_method
	def settings(self):
		self.menuName = Glyphs.localize({
			"en": "Italify",
		})

		# Word on Run Button (default: Apply)
		self.actionButtonLabel = Glyphs.localize({
			"en": "Apply",
			"de": "Anwenden",
			"fr": "Appliquer",
			"es": "Aplicar",
			"pt": "Aplique",
			"jp": "申し込む",
			"ko": "대다",
			"zh": "应用",
		})

		# Load dialog from .nib (without .extension)
		self.loadNib("IBdialog", __file__)

	# On dialog show
	@objc.python_method
	def start(self):
		Glyphs.defaults["com.eweracs.italify.angle"] = Glyphs.font.selectedLayers[0].master.italicAngle
		self.set_states()
		self.update()

	@objc.IBAction
	def setAngle_(self, sender):
		Glyphs.defaults["com.eweracs.italify.angle"] = float(sender.floatValue())
		self.update()

	@objc.IBAction
	def resetAngle_(self, sender):
		Glyphs.defaults["com.eweracs.italify.angle"] = Glyphs.font.selectedLayers[0].master.italicAngle
		self.angleTextBox.setStringValue_(Glyphs.defaults["com.eweracs.italify.angle"] or 0)
		self.update()

	@objc.IBAction
	def setRatio_(self, sender):
		Glyphs.defaults["com.eweracs.italify.ratio"] = float(sender.floatValue())
		self.update()

	@objc.IBAction
	def setAddExtremes_(self, sender):
		Glyphs.defaults["com.eweracs.italify.addExtremes"] = bool(sender.state())
		self.update()

	@objc.python_method
	def set_states(self):
		self.angleTextBox.setStringValue_(Glyphs.defaults["com.eweracs.italify.angle"] or 0)
		self.ratioSlider.setFloatValue_(Glyphs.defaults["com.eweracs.italify.ratio"] or 0)
		self.addExtremesCheckBox.setState_(Glyphs.defaults["com.eweracs.italify.addExtremes"] or False)

	# Actual filter
	@objc.python_method
	def filter(self, layer, inEditView, customParameters):
		angle = Glyphs.defaults["com.eweracs.italify.angle"] or 0
		ratio = Glyphs.defaults["com.eweracs.italify.ratio"] or 0
		add_extremes = Glyphs.defaults["com.eweracs.italify.addExtremes"] or False

		rotation_angle = angle * ratio
		slant_angle = angle * (1 - ratio)

		if not inEditView:
			return False

		self.rotate_layer(rotation_angle, layer)
		self.slant_layer(slant_angle, layer)

		if add_extremes:
			layer.addNodesAtExtremes()
			layer.addExtremePointsForce_(True)

	@objc.python_method
	def rotate_layer(self, angle, layer):
		x_center = layer.bounds.origin.x + layer.bounds.size.width / 2
		y_center = layer.bounds.origin.y + layer.bounds.size.height / 2
		shift_matrix = [1, 0, 0, 1, -x_center, -y_center]
		layer.applyTransform(shift_matrix)

		angle_radians = radians(angle)
		rotation_matrix = [cos(angle_radians), -sin(angle_radians), sin(angle_radians),
		                   cos(angle_radians), 0, 0]
		layer.applyTransform(rotation_matrix)

		shift_matrix = [1, 0, 0, 1, x_center, y_center]
		layer.applyTransform(shift_matrix)

	@objc.python_method
	def slant_layer(self, angle, layer):
		x_center = layer.bounds.origin.x + layer.bounds.size.width / 2
		y_center = layer.bounds.origin.y + layer.bounds.size.height / 2
		shift_matrix = [1, 0, 0, 1, -x_center, -y_center]
		layer.applyTransform(shift_matrix)

		transform = NSAffineTransform.new()
		slant = tan(angle * pi / 180.0)
		transform.shearXBy_(slant)

		for path in layer.paths:
			for node in path.nodes:
				node.position = transform.transformPoint_(node.position)
		for anchor in layer.anchors:
			anchor.position = transform.transformPoint_(anchor.position)

		shift_matrix = [1, 0, 0, 1, x_center, y_center]
		layer.applyTransform(shift_matrix)

	@objc.python_method
	def __file__(self):
		"""Please leave this method unchanged"""
		return __file__
