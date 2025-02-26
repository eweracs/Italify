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
from math import tan, pi, atan2, cos, sin, radians
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
		shear_angle = angle * (1 - ratio)
		bounds = layer.bounds
		centre = NSMakePoint(NSMidX(bounds), NSMidY(bounds))

		for path in layer.paths:
			self.process_path(path, centre, angle, distinguish_straight_and_curved, rotation_angle, shear_angle)

		for anchor in layer.anchors:
			anchor.position = self.shear_point(centre, angle, anchor.position)

		if add_extremes:
			layer.addExtremePoints()

		layer.roundCoordinates()

	@objc.python_method
	def process_path(self, path, centre, angle, distinguish_straight_and_curved, rotation_angle, shear_angle):
		if distinguish_straight_and_curved:
			self.smart_italify(path, centre, angle, rotation_angle, shear_angle)
			
		else:
			self.simple_italify(path, centre, rotation_angle, shear_angle)
				
	@objc.python_method
	def smart_italify(self, path, centre, angle, rotation_angle, shear_angle):
		# Get path segments
		transformed_segments = []
		path_segments = self.split_path_into_segments(path)
		for segment in path_segments:
			proxy_segment = [node.position for node in segment]
			# process each segment
			# process straight segment
			if len(segment) == 2:
				transformed_segment = self.process_straight_segment(proxy_segment, centre, angle)
				transformed_segments.append(transformed_segment)

			# process curved segment
			elif len(segment) == 4:
				transformed_segment = self.rotate_and_shear(proxy_segment, centre, rotation_angle, shear_angle)
				transformed_segments.append(transformed_segment)

		proxy_layer = GSLayer()
		path_list = []
		for transformed_segment in transformed_segments:
			if transformed_segment[0] == transformed_segment[1]:
				continue
			segment_path = self.make_path_from_segment(transformed_segment)
			proxy_layer.paths.append(segment_path)
			path_list.append(segment_path)

		for index in range(len(proxy_layer.paths) - 1):
			proxy_layer.connectPathsWithNode_andNode_extendPath_(
				list(proxy_layer.paths[0].nodes)[-1],
				proxy_layer.paths[1].nodes[0],
				True
			)
		proxy_layer.connectPathsWithNode_andNode_extendPath_(
			list((list(proxy_layer.paths)[-1]).nodes)[-1],
			list(proxy_layer.paths[0].nodes)[0],
			True
		)

		for shape in proxy_layer.shapes:
			path.parent.background.shapes.append(shape)

		# Add transformed segments to the background
		# self.visualise_segments(transformed_segments, path.parent)


	@objc.python_method
	def simple_italify(self, path, centre, rotation_angle, shear_angle):
		for node in path.nodes:
			node.position = self.rotate_point(centre, rotation_angle, node.position)
			node.position = self.shear_point(centre, shear_angle, node.position)

	@objc.python_method
	def make_path_from_segment(self, segment):
		new_path = GSPath()
		for index, point in enumerate(segment):
			node = GSNode(point)
			if len(segment) == 2:
				node.type = LINE
			if len(segment) == 4:
				if index == 0:
					node.type = LINE
				if index == 1 or index == 2:
					node.type = OFFCURVE
				if index == 3:
					node.type = CURVE
			new_path.addNode_(node)
		return new_path

	@objc.python_method
	def visualise_segments(self, segments, layer):
		for segment in segments:
			new_path = self.make_path_from_segment(segment)
			layer.background.paths.append(new_path)

	@objc.python_method
	def process_straight_segment(self, segment, centre, angle):
		point_1 = segment[0]
		point_2 = segment[1]

		dx = point_2.x - point_1.x
		dy = point_2.y - point_1.y

		# Calculate the segment angle
		segment_angle = atan2(dy, dx)

		# Convert to degrees and normalize to 0-180 range
		angle_deg = (segment_angle * 180 / pi) % 180

		# Calculate shear and rotation factors
		# 0 degrees (horizontal) -> full shear, no rotation
		# 90 degrees (vertical) -> full rotation, no shear
		shear_factor = cos(radians(angle_deg))
		rotation_factor = sin(radians(angle_deg))

		# Apply transformations
		shear_angle = angle * shear_factor
		rotation_angle = angle * rotation_factor

		transformed_segment = self.rotate_and_shear(segment, centre, rotation_angle, shear_angle)

		return transformed_segment

	@objc.python_method
	def rotate_and_shear(self, segment, centre, rotation_angle, shear_angle):
		transformed_segment = []
		for point in segment:
			rotated_point = self.rotate_point(centre, rotation_angle, point)
			sheared_point = self.shear_point(centre, shear_angle, rotated_point)
			transformed_segment.append(sheared_point)
		return transformed_segment

	@objc.python_method
	def split_path_into_segments(self, path):
		segments = []
		for node in path.nodes:
			if node.type != OFFCURVE:
				if node.nextNode.type != OFFCURVE:
					# if node.position == node.nextNode.position:
					# 	continue
					segment = [node, node.nextNode]
					segments.append(segment)
				if node.nextNode.type == OFFCURVE:
					segment = [node, node.nextNode, node.nextNode.nextNode, node.nextNode.nextNode.nextNode]
					segments.append(segment)
		return segments

	@objc.python_method
	def shear_point(self, centre, angle, point):
		transform = NSAffineTransform.new()
		shear = tan(radians(angle))
		transform.shearXBy_atCenter_(shear, centre.y)
		transformed_point = transform.transformPoint_(point)

		return transformed_point

	@objc.python_method
	def rotate_point(self, centre, angle, point):
		rotate = NSAffineTransform.new()
		rotate.translateXBy_yBy_(centre.x, centre.y)
		rotate.rotateByDegrees_(-angle)
		rotate.translateXBy_yBy_(-centre.x, -centre.y)
		transformed_point = rotate.transformPoint_(point)

		return transformed_point

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