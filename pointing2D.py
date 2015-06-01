import avango
import avango.daemon
import avango.gua
import avango.script
import random
import setupEnvironment
import math
import os.path

from examples_common.GuaVE import GuaVE
from avango.script import field_has_changed


class PointerStuff(avango.script.Script):
	TransMat = avango.gua.SFMatrix4()
	HomeMat = avango.gua.SFMatrix4()
	isInside = False
	timer = avango.SFFloat()
	startTime = 0
	endTime = 0
	result_file= None
	created_file=False
	num_files=0


	def __init__(self):
		self.super(PointerStuff).__init__()

	def __del__(self):
		self.result_file.close()
		

	@field_has_changed(TransMat)
	def transMatHasChanged(self):
		self.logData()

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
		if distance < 0.5:
			self.inRange()
		else: 
			self.outRange()
		
		#self.result_file.write(str(distance))

	def logData(self):
		path="results/results_pointing_2D/"
		if self.created_file==False:
			self.num_files=len([f for f in os.listdir(path)
				if os.path.isfile(os.path.join(path, f))])
			self.created_file=True
		else:
			self.result_file=open(path+"pointing2D_trial"+str(self.num_files)+".txt", "a+")
			self.result_file.write(str(self.timer.value)+"\n"+str(self.TransMat.value)+"\n\n")
			self.result_file.close()

	@field_has_changed(timer)
	def updateTimer(self):
			self.isInside = False
			
			#self.HomeMat.value *= avango.gua.make_trans_mat(500,0,0) 
			getattr(self, "HomeRef").Material.value.set_uniform("Color", avango.gua.Vec4(1, 1,0, 0.1)) #Transparenz funktioniert nicht
			#bewege home an neue Stelle

	def inRange(self):
		if self.isInside==False:
		  self.startTime = self.timer.value #startTimer
		self.isInside = True
		getattr(self, "HomeRef").Material.value.set_uniform("Color", avango.gua.Vec4(0, 1,0, 0.1)) #Transparenz funktioniert nicht

	def outRange(self):
		if self.isInside==True:
		   self.endTime = self.timer.value #startTimer#onExit, stop timer
		self.isInside = False
		getattr(self, "HomeRef").Material.value.set_uniform("Color", avango.gua.Vec4(1, 0,0, 0.1)) #Transparenz funktioniert nicht

	def getRandomTranslation(self):
		rand_index_1=random.randint(0, 10)
		rand_div_1=5#random.randint(1, 5)

		rand_index_2=random.randint(0, 10)
		rand_div_2=5#random.randint(1, 5)

		return avango.gua.make_trans_mat(rand_index_1/rand_div_1, 0, rand_index_2/rand_div_2)

	def handle_key(self, key, scancode, action, mods):
		if action == 0:
			#32 is space 335 is num_enter
			if key==335:
				self.HomeMat.value=self.getRandomTranslation()
			

def start ():
	graph=avango.gua.nodes.SceneGraph(Name="scenegraph") #Create Graph
	loader = avango.gua.nodes.TriMeshLoader() #Create Loader

	#Meshes
	pencil=loader.create_geometry_from_file("tracked_object", "data/objects/tracked_object.obj", avango.gua.LoaderFlags.NORMALIZE_SCALE)
	pencil.Material.value.set_uniform("Color", avango.gua.Vec4(0.5, 1, 0, 0.2))
	#tracked_object.Transform=avango.gua.make_scale_mat(0.01)

	object_transform=avango.gua.nodes.TransformNode(Children=[pencil])

	home=loader.create_geometry_from_file("light_sphere", "data/objects/light_sphere.obj", avango.gua.LoaderFlags.NORMALIZE_SCALE)
	home.Transform.value = avango.gua.make_scale_mat(0.2)
	home.Material.value.set_uniform("Color", avango.gua.Vec4(0.5, 0,0, 0.1))

	pointerstuff = PointerStuff()
	setupEnvironment.getWindow().on_key_press(pointerstuff.handle_key)
	tracking = setupEnvironment.setup(graph)

	graph.Root.value.Children.value.extend([home])

	#tracked_object.Transform.connect_from(tracking.Matrix)

	pointer_device_sensor = avango.daemon.nodes.DeviceSensor(
		DeviceService = avango.daemon.DeviceService()
		)
	pointer_device_sensor.Station.value = "device-pointer"

	setattr(pointerstuff, "HomeRef", home)
	#pointerstuff.TransMat.connect_from(tracking.Matrix)
	object_transform.Transform.connect_from(pointerstuff.TransMat)
	pointerstuff.HomeMat.connect_from(home.Transform)
	home.Transform.connect_from(pointerstuff.HomeMat)

	timer = avango.nodes.TimeSensor()
	pointerstuff.timer.connect_from(timer.Time)
	#pointerstuff.HomeRef=home

	setupEnvironment.launch()

if __name__ == '__main__':
  start()