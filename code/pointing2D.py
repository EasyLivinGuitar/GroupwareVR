import avango
import avango.daemon
import avango.gua
import avango.script
import random
import setupEnvironmentWall
import math
import os.path

from examples_common.GuaVE import GuaVE
from avango.script import field_has_changed


class PointerStuff(avango.script.Script):
	Button = avango.SFBool()
	TransMat = avango.gua.SFMatrix4()
	HomeMat = avango.gua.SFMatrix4()
	
	timer = avango.SFFloat()
	
	result_file= None
	created_file=False
	num_files=0

	startedTest=False
	flagPrinted=False

	error=0


	def __init__(self):
		self.super(PointerStuff).__init__()

	def __del__(self):
		self.result_file.close()

	@field_has_changed(Button)
	def button_pressed(self):
		if self.Button.value:
			if self.startedTest==False:
				self.startedTest=True
				self.HomeMat.value=self.getRandomTranslation()
			else:
				self.startedTest=False
				self.HomeMat.value=avango.gua.make_trans_mat(0, 0, 1)
		else:
			self.flagPrinted=False

	@field_has_changed(TransMat)
	def transMatHasChanged(self):
		self.error=self.getDistance()

		
	@field_has_changed(timer)
	def updateTimer(self):
		if setupEnvironmentWall.ignoreZ():
			translation = self.TransMat.value.get_translate()
			translation.z = 0

			self.TransMat.value = avango.gua.make_trans_mat(translation)*avango.gua.make_rot_mat(self.TransMat.value.get_rotate())

		self.logData()

	def logData(self):
		path="results/results_pointing_2D/"
		# if(self.startedTest):
		if self.created_file==False:
			self.num_files=len([f for f in os.listdir(path)
				if os.path.isfile(os.path.join(path, f))])
			self.created_file=True
		else:
			self.result_file=open(path+"pointing2D_trial"+str(self.num_files)+".txt", "a+")
			
			if(self.Button.value and self.flagPrinted==False):
				self.result_file.write("==========\n\n")
				self.flagPrinted=True
			
			self.result_file.write(
				"TimeStamp: "+str(self.timer.value)+"\n"
				"Error: "+str(self.error)+"\n"
				"Pointerpos: \n"+str(self.TransMat.value)+"\n"
				"Homepos: \n"+str(self.HomeMat.value)+"\n\n")
			self.result_file.close()
		if(self.startedTest==False):
			if self.Button.value:
				self.result_file=open(path+"pointing2D_trial"+str(self.num_files)+".txt", "a+")
				if(self.flagPrinted==False):
					self.result_file.write("----------\n\n")
					self.flagPrinted=True
				self.result_file.close()



	def getRandomTranslation(self):
		settings=[
			avango.gua.make_trans_mat(-0.8, -0.8, 1),
			avango.gua.make_trans_mat(-0.4, 0.4, 1),
			avango.gua.make_trans_mat(0.2, -0.2, 1),
			avango.gua.make_trans_mat(0.2, 0.2, 1),
			avango.gua.make_trans_mat(0.4, -0.4, 1),
			avango.gua.make_trans_mat(0.8, 0.8, 1)
		]

		index=random.randint(0, len(settings)-1)
		
		return settings[index]

	def getDistance(self):
		trans_x=self.TransMat.value.get_translate()[0]
		trans_y=self.TransMat.value.get_translate()[1]
		trans_z=self.TransMat.value.get_translate()[2]

		home_x=self.HomeMat.value.get_translate()[0]
		home_y=self.HomeMat.value.get_translate()[1]
		home_z=self.HomeMat.value.get_translate()[2]

		trans_home_x_square=(trans_x - home_x)*(trans_x - home_x)
		trans_home_y_square=(trans_y - home_y)*(trans_y - home_y)
		trans_home_z_square=(trans_z - home_z)*(trans_z - home_z)
		
		distance=math.sqrt(trans_home_x_square+trans_home_y_square+trans_home_z_square)
		return distance


	def handle_key(self, key, scancode, action, mods):
		if action == 0:
			#32 is space 335 is num_enter
			if key==335:
				self.HomeMat.value=self.getRandomTranslation()
			

def start ():
	graph = avango.gua.nodes.SceneGraph(Name="scenegraph") #Create Graph
	loader = avango.gua.nodes.TriMeshLoader() #Create Loader

	#Meshes
	pencil = loader.create_geometry_from_file("tracked_object", "data/objects/tracked_object.obj", avango.gua.LoaderFlags.NORMALIZE_SCALE)
	pencil.Transform.value=avango.gua.make_rot_mat(180, 1, 0, 0)*avango.gua.make_scale_mat(0.02)
	pencil.Material.value.set_uniform("Color", avango.gua.Vec4(0.5, 1, 0, 0.2))

	pencil_transform=avango.gua.nodes.TransformNode(Children=[pencil])

	home = loader.create_geometry_from_file("light_sphere", "data/objects/light_sphere.obj", avango.gua.LoaderFlags.NORMALIZE_SCALE)
	home.Transform.value = avango.gua.make_scale_mat(0.15)
	home.Material.value.set_uniform("Color", avango.gua.Vec4(1, 1,0, 1))

	home_transform=avango.gua.nodes.TransformNode(Children=[home])

	pointerstuff = PointerStuff()
	#setup
	setupEnvironmentWall.getWindow().on_key_press(pointerstuff.handle_key)
	setupEnvironmentWall.setup(graph)

	graph.Root.value.Children.value.extend([home_transform, pencil_transform])

	pointer_device_sensor = avango.daemon.nodes.DeviceSensor(DeviceService = avango.daemon.DeviceService())
	pointer_device_sensor.TransmitterOffset.value = setupEnvironmentWall.getOffsetTracking()
	pointer_device_sensor.Station.value = "pointer-1"

	button_sensor=avango.daemon.nodes.DeviceSensor(DeviceService=avango.daemon.DeviceService())
	button_sensor.Station.value="device-pointer"

	pointerstuff.Button.connect_from(button_sensor.Button0)
	
	#connect transmat with matrix from deamon
	pointerstuff.TransMat.connect_from(pointer_device_sensor.Matrix)
	
	#connect object at the place of transmat
	pencil_transform.Transform.connect_from(pointerstuff.TransMat)
	
	#connect home with home
	pointerstuff.HomeMat.connect_from(home_transform.Transform)
	home_transform.Transform.connect_from(pointerstuff.HomeMat)

	timer = avango.nodes.TimeSensor()
	pointerstuff.timer.connect_from(timer.Time)

	setupEnvironmentWall.launch()

if __name__ == '__main__':
  start()
