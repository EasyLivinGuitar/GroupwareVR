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
	pencilTransMat = avango.gua.SFMatrix4()
	aimMat = avango.gua.SFMatrix4()
	timer = avango.SFFloat()


	def __init__(self):
		self.super(trackingManager).__init__()
		self.isInside = False;
		self.startTime = 0
		self.endTime = 0
		self.aimRef = None
		#self.aimRef=None

	@field_has_changed(pencilTransMat)
	def pencilTransMatHasChanged(self):
		#calculate error
		currentRot = self.pencilTransMat.value.get_rotate().get_axis()*self.pencilTransMat.value.get_rotate().get_angle()

		aimRot = self.aimMat.value.get_rotate().get_axis()*self.pencilTransMat.value.get_rotate().get_angle()

		error = currentRot - aimRot
		error_x_square = (currentRot[0] - aimRot[0])*(currentRot[0] - aimRot[0])
		error_y_square = (currentRot[1] - aimRot[1])*(currentRot[1] - aimRot[1])
		error_z_square = (currentRot[2] - aimRot[2])*(currentRot[2] - aimRot[2])
		
		distance=math.sqrt(error_x_square+error_y_square+error_z_square)
		if distance < 0.5:
			self.inRange()
		else: 
			self.outRange()
		#print(distance)

	@field_has_changed(timer)
	def updateTimer(self):
		#erase translation in the matrix and keep rotation
		rotation = self.pencilTransMat.value.get_rotate()
		self.pencilTransMat.value = avango.gua.Mat4()
		self.pencilTransMat.value = avango.gua.make_rot_mat(rotation)

		if self.timer.value-self.startTime > 2 and self.isInside==True: #timer abbgelaufen:
			self.isInside = False
			
			#self.aimMat.value *= avango.gua.make_trans_mat(500,0,0) 
			#getattr(self, "aimRef").Material.value.set_uniform("Color", avango.gua.Vec4(1, 1,0, 0.5)) #Transparenz funktioniert nicht
			#bewege aim an neue Stelle

	def inRange(self):
		if self.isInside==False:
		  self.startTime = self.timer.value #startTimer
		self.isInside = True
		self.aimRef.Material.value.set_uniform("Color", avango.gua.Vec4(0, 1,0, 0.5)) #Transparenz funktioniert nicht

	def outRange(self):
		if self.isInside==True:
		   self.endTime = self.timer.value #startTimer#onExit, stop timer
		self.isInside = False
		self.aimRef.Material.value.set_uniform("Color", avango.gua.Vec4(1, 0,0, 0.5)) #Transparenz funktioniert nicht

def handle_key(key, scancode, action, mods):
	if action == 0:
		print(key)
		#32 is space 335 is num_enter
		if key == 335:
			print("check if achieved the goal")


def start ():
	graph=avango.gua.nodes.SceneGraph(Name="scenegraph") #Create Graph
	loader = avango.gua.nodes.TriMeshLoader() #Create Loader

	#Meshes
	pencil = loader.create_geometry_from_file("tracked_object", "data/objects/tracked_object.obj", avango.gua.LoaderFlags.NORMALIZE_SCALE)
	pencil.Material.value.set_uniform("Color", avango.gua.Vec4(0.3, 0.3, 0.3, 0.5))
	object_transform = avango.gua.nodes.TransformNode(Children=[pencil], Transform=avango.gua.make_trans_mat(0.0, 0.0, -15.0))

	aim = loader.create_geometry_from_file("tracked_object", "data/objects/tracked_object.obj", avango.gua.LoaderFlags.NORMALIZE_SCALE)
	aim.Transform.value = avango.gua.make_trans_mat(0,0,-10)*avango.gua.make_scale_mat(0.2)
	aim.Material.value.set_uniform("Color", avango.gua.Vec4(0.3, 0.3, 0.3, 0.5))

	setupEnvironment.getWindow().on_key_press(handle_key)
	tracking = setupEnvironment.setup(graph)

	#add nodes to root
	graph.Root.value.Children.value.extend([object_transform, aim])

	pencil.Transform.connect_from(tracking.Matrix)

	pointer_device_sensor = avango.daemon.nodes.DeviceSensor(
		DeviceService = avango.daemon.DeviceService()
		)
	pointer_device_sensor.Station.value = "device-pointer"

	trackManager = trackingManager()
	trackManager.aimRef = aim
	trackManager.pencilTransMat.connect_from(tracking.Matrix)
	trackManager.aimMat.connect_from(aim.Transform)

	timer = avango.nodes.TimeSensor()
	trackManager.timer.connect_from(timer.Time)
	trackingManager.aimRef=aim

	setupEnvironment.launch()

if __name__ == '__main__':
  start()