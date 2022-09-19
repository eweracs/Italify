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
from math import tan, pi, atan2
from Foundation import NSAffineTransform


class Italify(FilterWithDialog):

	# The NSView object from the User Interface. Keep this here!
	dialog = objc.IBOutlet()

	# Text field in dialog
	angleTextBox = objc.IBOutlet()
	resetAngleButton = objc.IBOutlet()
	ratioSlider = objc.IBOutlet()
	addExtremesCheckBox = objc.IBOutlet()

	select_tool = NSClassFromString("GSToolSelect").alloc().init()

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

		for path in layer.paths:
			# process straight segments
			node_count = len(path.nodes)
			for index in range(node_count - 1, 0, -1):
				node = path.nodes[index]
				if node.type != "offcurve" and node.nextNode.type != "offcurve":
					self.transform_straight_segment(angle, layer, path, index)

			node_count = len(path.nodes)
			# process curved segments
			for index in range(node_count - 1, 0, -1):
				node = path.nodes[index]
				if node.type != "offcurve":
					if node.nextNode.type == "offcurve" and node.prevNode.type != "offcurve":
						layer.openCornerAtNode_offset_(node, 10)
						# transform on-curve node
						self.rotate_node(path.parent, rotation_angle, node)
						self.slant_node(path.parent, slant_angle, node)
						# transform attached off-curve node
						self.rotate_node(path.parent, rotation_angle, node.nextNode)
						self.slant_node(path.parent, slant_angle, node.nextNode)
						self.select_tool._makeCorner_firstNodeIndex_endNodeIndex_(path, index, index + 1)
					elif node.nextNode.type != "offcurve" and node.prevNode.type == "offcurve":
						layer.openCornerAtNode_offset_(node, 10)
						# transform on-curve node
						self.rotate_node(path.parent, rotation_angle, node)
						self.slant_node(path.parent, slant_angle, node)
						# transform attached off-curve node
						self.rotate_node(path.parent, rotation_angle, node.prevNode)
						self.slant_node(path.parent, slant_angle, node.prevNode)
						self.select_tool._makeCorner_firstNodeIndex_endNodeIndex_(path, index, index + 1)
					elif node.nextNode.type == "offcurve" and node.prevNode.type == "offcurve":
						# transform on-curve node
						self.rotate_node(path.parent, rotation_angle, node)
						self.slant_node(path.parent, slant_angle, node)
						# transform attached off-curve nodes
						self.rotate_node(path.parent, rotation_angle, node.prevNode)
						self.slant_node(path.parent, slant_angle, node.prevNode)
						self.rotate_node(path.parent, rotation_angle, node.nextNode)
						self.slant_node(path.parent, slant_angle, node.nextNode)

				# else:
				# 	self.rotate_node(path.parent, rotation_angle, node)
				# 	self.slant_node(path.parent, slant_angle, node)

		if add_extremes:
			layer.addNodesAtExtremes()
			layer.addExtremePointsForce_(True)

	@objc.python_method
	def get_slant_rotate_ratio_angle(self, node1, node2):
		return abs(abs(atan2(node1.position.y - node2.position.y, node1.position.x - node2.position.x) / pi * 2) - 1)

	@objc.python_method
	def slant_node(self, layer, angle, node):
		x_center = layer.bounds.origin.x + layer.bounds.size.width / 2
		y_center = layer.bounds.origin.y + layer.bounds.size.height / 2
		shift_matrix = [1, 0, 0, 1, -x_center, -y_center]
		layer.applyTransform(shift_matrix)

		transform = NSAffineTransform.new()
		slant = tan(angle * pi / 180.0)
		transform.shearXBy_(slant)

		node.position = transform.transformPoint_(node.position)

		shift_matrix = [1, 0, 0, 1, x_center, y_center]
		layer.applyTransform(shift_matrix)

	@objc.python_method
	def rotate_node(self, layer, angle, node):
		x_center = layer.bounds.origin.x + layer.bounds.size.width / 2
		y_center = layer.bounds.origin.y + layer.bounds.size.height / 2
		shift_matrix = [1, 0, 0, 1, -x_center, -y_center]
		layer.applyTransform(shift_matrix)

		rotate = NSAffineTransform.new()
		rotate.rotateByDegrees_(-angle)
		node.position = rotate.transformPoint_(node.position)

		shift_matrix = [1, 0, 0, 1, x_center, y_center]
		layer.applyTransform(shift_matrix)

	@objc.python_method
	def transform_straight_segment(self, angle, layer, path, index):
		layer.openCornerAtNode_offset_(self.return_node_for_index(path.nodes, index - 1), 10)
		layer.openCornerAtNode_offset_(self.return_node_for_index(path.nodes, index + 1), 10)

		rotation_angle = angle * (1 - self.get_slant_rotate_ratio_angle(self.return_node_for_index(path.nodes,
		                                                                                           index),
		                                                                self.return_node_for_index(path.nodes,
		                                                                                           index + 1)))
		slant_angle = angle * self.get_slant_rotate_ratio_angle(self.return_node_for_index(path.nodes, index),
		                                                        self.return_node_for_index(path.nodes, index + 1))

		self.rotate_node(layer, rotation_angle, self.return_node_for_index(path.nodes, index))
		self.rotate_node(layer, rotation_angle, self.return_node_for_index(path.nodes, index + 1))
		self.slant_node(layer, slant_angle, self.return_node_for_index(path.nodes, index))
		self.slant_node(layer, slant_angle, self.return_node_for_index(path.nodes, index + 1))

		self.select_tool._makeCorner_firstNodeIndex_endNodeIndex_(path,
		                                                          (index + 1) % len(path.nodes),
		                                                          (index + 2) % len(path.nodes))
		self.select_tool._makeCorner_firstNodeIndex_endNodeIndex_(path,
		                                                          (index - 1) % len(path.nodes),
		                                                          index % len(path.nodes))

	@objc.python_method
	def return_node_for_index(self, nodes, index):
		return nodes[index % len(nodes)]

	@objc.python_method
	def __file__(self):
		"""Please leave this method unchanged"""
		return __file__
