import avango
import avango.daemon
import avango.gua
import avango.script
import random
import setupEnvironment
import math

from examples_common.GuaVE import GuaVE
from avango.script import field_has_changed

class PointerStuff(avango.script.Script):
	TopButton = avango.SFBool()
	CenterButton = avango.SFBool()
	BottomButton = avango.SFBool()
	TransMat = avango.gua.SFMatrix4()
	HomeMat = avango.gua.SFMatrix4()
	isInside = False;
	timer = avango.SFFloat()
	startTime = 0
	endTime = 0


	def __init__(self):
		self.super(PointerStuff).__init__()
		self.top_button_last_time = False
		#self.HomeRef=None


	@field_has_changed(TopButton)
	def top_button_has_changed(self):
		pass

	@field_has_changed(TransMat)
	def transMatHasChanged(self):
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
		#print(distance)

	'''def evaluate(self):
		if self.TopButton.value:
			print("TopButton down")
			#self.cylinderRef.Material.value.set_uniform("Color", avango.gua.Vec4(random.random(), random.random(), random.random(), 1.0))
		if self.CenterButton.value:
			print("CenterButton down")
			#self.cylinderRef.Transform.value = avango.gua.make_trans_mat(0, 0, -0.1)*self.cylinderRef.Transform.value
			#self.cylinderRef.Transform.value = avango.gua.make_trans_mat(0, 0, -1)*avango.gua.make_scale_mat(0.01, 0.01, 10.0)
		if self.CenterButton.value==False:
			print("CenterButton up")
			#self.cylinderRef.Transform.value = avango.gua.make_trans_mat(0, 0, 0.1)*self.cylinderRef.Transform.value
			#self.cylinderRef.Transform.value = avango.gua.make_trans_mat(0, 0, -1)*avango.gua.make_scale_mat(0.01, 0.01, 10.0)
		if self.BottomButton.value:
			print("BottomButton down")'''

	@field_has_changed(timer)
	def updateTimer(self):
		if self.timer.value-self.startTime > 2 and self.isInside==True: #timer abbgelaufen:
			self.isInside = False
			#self.HomeMat.value *= avango.gua.make_trans_mat(500,0,0) 
			getattr(self, "HomeRef").Material.value.set_uniform("Color", avango.gua.Vec4(1, 1,0, 0.5)) #Transparenz funktioniert nicht
			#bewege home an neue Stelle

	def inRange(self):
		if self.isInside==False:
		  self.startTime = self.timer.value #startTimer
		self.isInside = True
		getattr(self, "HomeRef").Material.value.set_uniform("Color", avango.gua.Vec4(0, 1,0, 0.5)) #Transparenz funktioniert nicht

	def outRange(self):
		if self.isInside==True:
		   self.endTime = self.timer.value #startTimer#onExit, stop timer
		self.isInside = False
		getattr(self, "HomeRef").Material.value.set_uniform("Color", avango.gua.Vec4(1, 0,0, 0.5)) #Transparenz funktioniert nicht

	


def start ():
	graph=avango.gua.nodes.SceneGraph(Name="scenegraph") #Create Graph
	loader = avango.gua.nodes.TriMeshLoader() #Create Loader

	#Meshes
	tracked_object=loader.create_geometry_from_file("tracked_object", "data/objects/tracked_object.obj", avango.gua.LoaderFlags.NORMALIZE_SCALE)

	object_transform=avango.gua.nodes.TransformNode(Children=[tracked_object], Transform=avango.gua.make_trans_mat(0.0, 0.0, -10.0))

	home=loader.create_geometry_from_file("light_sphere", "data/objects/light_sphere.obj", avango.gua.LoaderFlags.NORMALIZE_SCALE)
	home.Transform.value = avango.gua.make_scale_mat(0.2)
	home.Material.value.set_uniform("Color", avango.gua.Vec4(1, 0,0, 0.5)) #Transparenz funktioniert nicht
	tracking = setupEnvironment.setup(graph)

	graph.Root.value.Children.value.extend([object_transform,home])

	tracked_object.Transform.connect_from(tracking.Matrix)

	pointer_device_sensor = avango.daemon.nodes.DeviceSensor(
		DeviceService = avango.daemon.DeviceService()
		)
	pointer_device_sensor.Station.value = "device-pointer"

	pointerstuff = PointerStuff()
	setattr(pointerstuff, "HomeRef", home)
	pointerstuff.TopButton.connect_from(pointer_device_sensor.Button0)
	pointerstuff.CenterButton.connect_from(pointer_device_sensor.Button1)
	pointerstuff.BottomButton.connect_from(pointer_device_sensor.Button2)
	pointerstuff.TransMat.connect_from(tracking.Matrix)
	pointerstuff.HomeMat.connect_from(home.Transform)

	timer = avango.nodes.TimeSensor()
	pointerstuff.timer.connect_from(timer.Time)
	#pointerstuff.HomeRef=home


	#light.Color.connect_from(pointerstuff.OutColor)
	setupEnvironment.launch()

if __name__ == '__main__':
  start()