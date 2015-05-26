import avango
import avango.daemon
import avango.gua
import avango.script
import random
import setupEnvironment
import math

from examples_common.GuaVE import GuaVE
from avango.script import field_has_changed

class trackingManager(avango.script.Script):
	TransMat = avango.gua.SFMatrix4()
	aimMat = avango.gua.SFMatrix4()
	isInside = False;
	timer = avango.SFFloat()
	startTime = 0
	endTime = 0


	def __init__(self):
		self.super(trackingManager).__init__()
		#self.aimRef=None

	@field_has_changed(TransMat)
	def transMatHasChanged(self):
		trans_x=self.TransMat.value.get_translate()[0]
		trans_y=self.TransMat.value.get_translate()[1]
		trans_z=self.TransMat.value.get_translate()[2]

		aim_x=self.aimMat.value.get_translate()[0]
		aim_y=self.aimMat.value.get_translate()[1]
		aim_z=self.aimMat.value.get_translate()[2]

		trans_aim_x_square=(trans_x - aim_x)*(trans_x - aim_x)
		trans_aim_y_square=(trans_y - aim_y)*(trans_y - aim_y)
		trans_aim_z_square=(trans_z - aim_z)*(trans_z - aim_z)
		
		distance=math.sqrt(trans_aim_x_square+trans_aim_y_square+trans_aim_z_square)
		if distance < 0.5:
			self.inRange()
		else: 
			self.outRange()
		#print(distance)

	@field_has_changed(timer)
	def updateTimer(self):
		if self.timer.value-self.startTime > 2 and self.isInside==True: #timer abbgelaufen:
			self.isInside = False
			
			#self.aimMat.value *= avango.gua.make_trans_mat(500,0,0) 
			#getattr(self, "aimRef").Material.value.set_uniform("Color", avango.gua.Vec4(1, 1,0, 0.5)) #Transparenz funktioniert nicht
			#bewege aim an neue Stelle

	def inRange(self):
		if self.isInside==False:
		  self.startTime = self.timer.value #startTimer
		self.isInside = True
		#getattr(self, "aimRef").Material.value.set_uniform("Color", avango.gua.Vec4(0, 1,0, 0.5)) #Transparenz funktioniert nicht

	def outRange(self):
		if self.isInside==True:
		   self.endTime = self.timer.value #startTimer#onExit, stop timer
		self.isInside = False
		#getattr(self, "aimRef").Material.value.set_uniform("Color", avango.gua.Vec4(1, 0,0, 0.5)) #Transparenz funktioniert nicht

def handle_key(key, scancode, action, mods):
	if action == 0:
		print(key)
		#32 is space 335 is num_enter
		if key is 335:
			print("check if achieved the goal")


def start ():
	graph=avango.gua.nodes.SceneGraph(Name="scenegraph") #Create Graph
	loader = avango.gua.nodes.TriMeshLoader() #Create Loader

	#Meshes
	tracked_object = loader.create_geometry_from_file("tracked_object", "data/objects/tracked_object.obj", avango.gua.LoaderFlags.NORMALIZE_SCALE)

	object_transform = avango.gua.nodes.TransformNode(Transform=avango.gua.make_trans_mat(0.0, 0.0, -10.0))

	aim = loader.create_geometry_from_file("tracked_object", "data/objects/tracked_object.obj", avango.gua.LoaderFlags.NORMALIZE_SCALE)
	aim.Transform.value = avango.gua.make_scale_mat(0.2)
	aim.Material.value.set_uniform("Color", avango.gua.Vec4(0.3, 0.3, 0.3, 0.5)) #Transparenz funktioniert nicht

	setupEnvironment.getWindow().on_key_press(handle_key)
	tracking = setupEnvironment.setup(graph)

	graph.Root.value.Children.value.extend([object_transform,aim])

	tracked_object.Transform.connect_from(tracking.Matrix)

	pointer_device_sensor = avango.daemon.nodes.DeviceSensor(
		DeviceService = avango.daemon.DeviceService()
		)
	pointer_device_sensor.Station.value = "device-pointer"

	trackManager = trackingManager()
	setattr(trackManager, "aimRef", aim)
	trackManager.TransMat.connect_from(tracking.Matrix)
	trackManager.aimMat.connect_from(aim.Transform)

	timer = avango.nodes.TimeSensor()
	trackManager.timer.connect_from(timer.Time)
	trackingManager.aimRef=aim

	setupEnvironment.launch()

if __name__ == '__main__':
  start()