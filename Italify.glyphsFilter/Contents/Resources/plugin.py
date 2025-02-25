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

# TODO: Handle paths in cw direction

from __future__ import division, print_function, unicode_literals
import objc
from GlyphsApp import *
from GlyphsApp.plugins import *
from math import tan, pi, atan2, cos, sin
from Foundation import NSAffineTransform, NSMakePoint, NSMidX, NSMidY


class Italify(FilterWithDialog):
	dialog = objc.IBOutlet()
	resetAngleButton = objc.IBOutlet()
	select_tool = NSClassFromString("GSToolSelect").alloc().init()

	@objc.python_method
	def settings(self):
		self.menuName = Glyphs.localize({"en": "Italify"})
		self.actionButtonLabel = Glyphs.localize({
			"en": "Apply",
			"de": "Anwenden",
			"fr": "Appliquer",
			"es": "Aplicar",
			"pt": "Apliquer",
			"jp": "申し込む",
			"ko": "대다",
			"zh": "应用",
		})
		self.loadNib("IBdialog", __file__)

	@objc.python_method
	def start(self):
		Glyphs.defaults["com.eweracs.italify.angle"] = Glyphs.font.selectedLayers[0].master.italicAngle
		self.update()

	@objc.IBAction
	def setUpdate_(self, sender):
		self.update()

	@objc.IBAction
	def resetAngle_(self, sender):
		Glyphs.defaults["com.eweracs.italify.angle"] = Glyphs.font.selectedLayers[0].master.italicAngle
		self.update()

	@objc.python_method
	def filter(self, layer, inEditView, customParameters):
		if inEditView:
			angle = Glyphs.defaults["com.eweracs.italify.angle"] or 0
			ratio = Glyphs.defaults["com.eweracs.italify.ratio"] or 0
			distinguish_straight_and_curved = Glyphs.boolDefaults["com.eweracs.italify.distinguishStraightAndCurved"]
			add_extremes = Glyphs.boolDefaults["com.eweracs.italify.addExtremes"]
		else:
			angle = float(customParameters.get("angle", 0))
			ratio = float(customParameters.get("ratio", 0))
			distinguish_straight_and_curved = bool(customParameters.get("smart", False))
			add_extremes = bool(customParameters.get("extremes", False))

		rotation_angle = angle * ratio
		slant_angle = angle * (1 - ratio)
		bounds = layer.bounds
		center = NSMakePoint(NSMidX(bounds), NSMidY(bounds))

		for path in layer.paths:
			self.process_path(path, center, angle, rotation_angle, slant_angle, distinguish_straight_and_curved)

		for anchor in layer.anchors:
			self.slant_node(center, angle, anchor)

		if add_extremes:
			layer.addExtremePoints()

	@objc.python_method
	def process_path(self, path, center, angle, rotation_angle, slant_angle, distinguish_straight_and_curved):
		node_count = len(path.nodes)
		for i in range(node_count):
			node = path.nodes[i]
			prev_node = path.nodes[(i - 1) % node_count]
			next_node = path.nodes[(i + 1) % node_count]

			if distinguish_straight_and_curved:
				if node.type != "offcurve":
					if prev_node.type != "offcurve" and next_node.type != "offcurve":
						# Straight segment
						self.process_straight_segment(path, i, center, angle)
					else:
						# Curved segment
						self.process_curved_segment(node, prev_node, next_node, center, rotation_angle, slant_angle)
			else:
				self.rotate_node(center, rotation_angle, node)
				self.slant_node(center, slant_angle, node)

	@objc.python_method
	def process_straight_segment(self, path, index, center, angle):
		node = path.nodes[index]
		next_node = path.nodes[(index + 1) % len(path.nodes)]

		dx = next_node.x - node.x
		dy = next_node.y - node.y

		# Calculate the segment angle
		segment_angle = atan2(dy, dx)

		# Convert to degrees and normalize to 0-180 range
		angle_deg = (segment_angle * 180 / pi) % 180

		# Calculate shear and rotation factors
		# 0 degrees (horizontal) -> full shear, no rotation
		# 90 degrees (vertical) -> full rotation, no shear
		shear_factor = cos(segment_angle)
		rotation_factor = sin(segment_angle)

		# Apply transformations
		shear_angle = angle * shear_factor
		rotation_angle = angle * rotation_factor

		# Apply rotation first
		self.rotate_node(center, rotation_angle, node)
		self.rotate_node(center, rotation_angle, next_node)

		# Then apply shear
		self.slant_node(center, shear_angle, node)
		self.slant_node(center, shear_angle, next_node)

	@objc.python_method
	def process_curved_segment(self, node, prev_node, next_node, center, rotation_angle, slant_angle):
		self.rotate_node(center, rotation_angle, node)
		self.slant_node(center, slant_angle, node)

		if prev_node.type == "offcurve":
			self.rotate_node(center, rotation_angle, prev_node)
			self.slant_node(center, slant_angle, prev_node)

		if next_node.type == "offcurve":
			self.rotate_node(center, rotation_angle, next_node)
			self.slant_node(center, slant_angle, next_node)

	objc.python_method
	def slant_node(self, center, angle, node):
		transform = NSAffineTransform.new()
		transform.translateXBy_yBy_(center.x, center.y)
		slant = tan(angle * pi / 180.0)
		transform.shearXBy_(slant)
		transform.translateXBy_yBy_(-center.x, -center.y)
		node.position = transform.transformPoint_(node.position)

	@objc.python_method
	def rotate_node(self, center, angle, node):
		rotate = NSAffineTransform.new()
		rotate.translateXBy_yBy_(center.x, center.y)
		rotate.rotateByDegrees_(-angle)
		rotate.translateXBy_yBy_(-center.x, -center.y)
		node.position = rotate.transformPoint_(node.position)

	@objc.python_method
	def customParameterString(self):
		angle = Glyphs.defaults["com.eweracs.italify.angle"] or 0
		ratio = Glyphs.defaults["com.eweracs.italify.ratio"] or 0
		smart = int(Glyphs.boolDefaults["com.eweracs.italify.distinguishStraightAndCurved"])
		add_extremes = int(Glyphs.boolDefaults["com.eweracs.italify.addExtremes"])
		return f"Italify;angle:{angle};ratio:{ratio};smart:{smart};extremes:{add_extremes}"

	@objc.python_method
	def __file__(self):
		return __file__