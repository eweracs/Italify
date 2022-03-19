# encoding: utf-8

from __future__ import division, print_function, unicode_literals
import objc
from GlyphsApp import *
from GlyphsApp.plugins import *
from vanilla import *
from math import *

class Italify(PalettePlugin):

	@objc.python_method
	def settings(self):
		self.name = "Italify"

		self.default_angle = Glyphs.font.selectedFontMaster.italicAngle / 2
		self.preferredAngles = {}

		width = 150
		height = 114
		self.paletteView = Window((width, height))
		self.paletteView.group = Group((0, 0, width, height))
		self.paletteView.group.rotateTitle = TextBox((10, 10, -10, -10), "Rotate", sizeStyle='small')
		self.paletteView.group.rotateEntry = EditText((-80, 5, -34, 22), text=str(self.default_angle),
		                                              callback=self.enter_angles)
		self.paletteView.group.rotateReset = SquareButton((-30, 6, -10, 20), u"↺", sizeStyle="small",
		                                                  callback=self.reset_value)
		self.paletteView.group.slantTitle = TextBox((10, 36, -10, -10), "Slant", sizeStyle='small')
		self.paletteView.group.slantEntry = EditText((-80, 31, -34, 22), text=str(self.default_angle),
		                                             callback=self.enter_angles)
		self.paletteView.group.slantReset = SquareButton((-30, 32, -10, 20), u"↺", sizeStyle="small",
		                                                  callback=self.reset_value)

		self.paletteView.group.addExtremes = CheckBox((14, 58, -10, 18), "Add extremes", sizeStyle="small")

		self.paletteView.group.italifyButton = Button((10, 84, -10, -10), "Italify", callback=self.italify)

		self.dialog = self.paletteView.group.getNSView()

	@objc.python_method
	def start(self):
		# Adding a callback for the "GSUpdateInterface" event
		Glyphs.addCallback(self.update, UPDATEINTERFACE)

	@objc.python_method	
	def __del__(self):
		Glyphs.removeCallback(self.update)

	@objc.python_method
	def enter_angles(self, sender):
		if not sender.get().isnumeric() or len(sender.get()) < 1:
			return
		self.preferredAngles[Glyphs.font.selectedFontMaster.id] = [
			float(self.paletteView.group.rotateEntry.get()),
			float(self.paletteView.group.slantEntry.get())
		]
		print(self.preferredAngles)

	@objc.python_method
	def reset_value(self, sender):
		if sender == self.paletteView.group.rotateReset:
			self.paletteView.group.rotateEntry.set(str(self.default_angle))
		if sender == self.paletteView.group.slantReset:
			self.paletteView.group.slantEntry.set(str(self.default_angle))
		self.preferredAngles[Glyphs.font.selectedFontMaster.id] = [
			float(self.paletteView.group.rotateEntry.get()),
			float(self.paletteView.group.slantEntry.get())
		]

	@objc.python_method
	def get_angle(self, node1, node2):
		nodes_radians = atan2(node1.y - node2.y, node1.x - node2.x)
		return degrees(nodes_radians)

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
	def remove_italic_extremes(self, layer):
		delete_nodes = [[] for path in layer.paths]
		for i, path in enumerate(layer.paths):
			for node in path.nodes:
				prev_dist = hypot(node.x - node.prevNode.x, node.y - node.prevNode.y)
				next_dist = hypot(node.x - node.nextNode.x, node.y - node.nextNode.y)
				if prev_dist < next_dist:
					angle = self.get_angle(node, node.nextNode)
				elif next_dist < prev_dist:
					angle = self.get_angle(node, node.prevNode)
				if node.type == "curve" and node.smooth and node.prevNode.type == node.nextNode.type == "offcurve" and \
						abs(angle) - 1 <= italic_angle <= abs(angle) + 1:
					delete_nodes[i].append(node)
		for i, path in enumerate(layer.paths):
			for delete in delete_nodes[i]:
				path.removeNodeCheckKeepShape_normalizeHandles_(delete, True)

	@objc.python_method
	def italify(self, sender):
		for layer in Glyphs.font.selectedLayers:
			backup_layer = layer.copy()

			self.rotate_layer(self.preferredAngles[Glyphs.font.selectedFontMaster.id][0], layer)
			self.slant_layer(self.preferredAngles[Glyphs.font.selectedFontMaster.id][1], layer)

			if self.paletteView.group.addExtremes.get():
				layer.addNodesAtExtremes()

			self.slant_layer(self.preferredAngles[Glyphs.font.selectedFontMaster.id][1], backup_layer)
			layer.anchors = backup_layer.anchors

	@objc.python_method
	def update(self, sender):
		self.default_angle = Glyphs.font.selectedFontMaster.italicAngle / 2

		if Glyphs.font.selectedFontMaster.id not in self.preferredAngles:
			self.preferredAngles[Glyphs.font.selectedFontMaster.id] = [
			float(self.paletteView.group.rotateEntry.get() or self.default_angle),
			float(self.paletteView.group.slantEntry.get() or self.default_angle)
			]

		self.paletteView.group.rotateEntry.set(self.preferredAngles[Glyphs.font.selectedFontMaster.id][0])
		self.paletteView.group.slantEntry.set(self.preferredAngles[Glyphs.font.selectedFontMaster.id][1])

	@objc.python_method
	def __file__(self):
		"""Please leave this method unchanged"""
		return __file__
