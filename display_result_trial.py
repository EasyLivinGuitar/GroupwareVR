import avango
import avango.daemon
import avango.gua
import avango.script
import random
import setupEnvironment
import math
import queue
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
	read=False
	queue=queue.Queue()
	step=None


	def __init__(self):
		#self.readData()
		self.super(PointerStuff).__init__()
		

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
		

	@field_has_changed(timer)
	def updateTimer(self):
		if self.read==False:
			self.readData()
			self.read=True

		self.play()

		getattr(self, "HomeRef").value=avango.gua.make_trans_mat(self.timer.value, 0.0, 0.0)
		if self.timer.value-self.startTime > 2 and self.isInside==True: #timer abbgelaufen:
			self.isInside = False
			
			#self.HomeMat.value *= avango.gua.make_trans_mat(500,0,0) 
			getattr(self, "HomeRef").Material.value.set_uniform("Color", avango.gua.Vec4(1, 1,0, 1)) #Transparenz funktioniert nicht
			#bewege home an neue Stelle

	def inRange(self):
		if self.isInside==False:
		  self.startTime = self.timer.value #startTimer
		self.isInside = True
		getattr(self, "HomeRef").Material.value.set_uniform("Color", avango.gua.Vec4(0, 1,0, 1)) #Transparenz funktioniert nicht

	def outRange(self):
		if self.isInside==True:
		   self.endTime = self.timer.value #startTimer#onExit, stop timer
		self.isInside = False
		getattr(self, "HomeRef").Material.value.set_uniform("Color", avango.gua.Vec4(1, 0,0, 1)) #Transparenz funktioniert nicht

	def readData(self):
		self.result_file=open("results/results_pointing_2D/pointing2D_trail7.txt")
		
		lines=self.result_file.readlines()

		for i in range(len(lines)):
			if(i%6==0):
				timeStamp=float(lines[i])
			if(i%6==1):
				mat_line_1=lines[i]
			if(i%6==2):
				mat_line_2=lines[i]
			if(i%6==3):
				mat_line_3=lines[i]
			if(i%6==4):
				mat_line_4=lines[i]
			if(i%6==5):
				string=mat_line_1.replace("(","")
				mat_1=string.split()
				
				mat_2=mat_line_2.split()
				
				mat_3=mat_line_3.split()

				string=mat_line_4.replace(")","")
				mat_4=string.split()

				matrix=avango.gua.Mat4()

				matrix.set_element(0, 0, float(mat_1[0]))
				matrix.set_element(0, 1, float(mat_1[1]))
				matrix.set_element(0, 2, float(mat_1[2]))
				matrix.set_element(0, 3, float(mat_1[3]))
				matrix.set_element(1, 0, float(mat_2[0]))
				matrix.set_element(1, 1, float(mat_2[1]))
				matrix.set_element(1, 2, float(mat_2[2]))
				matrix.set_element(1, 3, float(mat_2[3]))
				matrix.set_element(2, 0, float(mat_3[0]))
				matrix.set_element(2, 1, float(mat_3[1]))
				matrix.set_element(2, 2, float(mat_3[2]))
				matrix.set_element(2, 3, float(mat_3[3]))
				matrix.set_element(3, 0, float(mat_4[0]))
				matrix.set_element(3, 1, float(mat_4[1]))
				matrix.set_element(3, 2, float(mat_4[2]))
				matrix.set_element(3, 3, float(mat_4[3]))

				step=MatrixStep(timeStamp, matrix)
				self.queue.put(step)

	def play(self):
		if(self.step==None):
			self.step=self.queue.get()
		if(self.step.TimeStamp<=self.timer.value):
			self.TransMat.value=self.step.matrix
			self.step=None



class MatrixStep:
	TimeStamp=0.0
	matrix=avango.gua.SFMatrix4

	def __init__(self, stamp, mat):
		self.TimeStamp=stamp
		self.matrix=mat

			

def start ():
	graph=avango.gua.nodes.SceneGraph(Name="scenegraph") #Create Graph
	loader = avango.gua.nodes.TriMeshLoader() #Create Loader

	#Meshes
	tracked_object=loader.create_geometry_from_file("tracked_object", "data/objects/tracked_object.obj", avango.gua.LoaderFlags.NORMALIZE_SCALE)

	object_transform=avango.gua.nodes.TransformNode(Children=[tracked_object])

	home=loader.create_geometry_from_file("light_sphere", "data/objects/light_sphere.obj", avango.gua.LoaderFlags.NORMALIZE_SCALE)
	home.Transform.value = avango.gua.make_scale_mat(0.2)
	home.Material.value.set_uniform("Color", avango.gua.Vec4(1, 0,0, 1)) #Transparenz funktioniert nicht

	home_transform=avango.gua.nodes.TransformNode(Children=[home])

	#setupEnvironment.getWindow().on_key_press(handle_key)
	tracking = setupEnvironment.setup(graph)

	graph.Root.value.Children.value.extend([object_transform,home_transform])

	#tracked_object.Transform.connect_from(tracking.Matrix)

	pointer_device_sensor = avango.daemon.nodes.DeviceSensor(
		DeviceService = avango.daemon.DeviceService()
		)
	pointer_device_sensor.Station.value = "device-pointer"

	pointerstuff = PointerStuff()
	setattr(pointerstuff, "HomeRef", home)
	#pointerstuff.TransMat.connect_from(tracking.Matrix)
	object_transform.Transform.connect_from(pointerstuff.TransMat)
	#pointerstuff.HomeMat.connect_from(home_transform.Transform)
	home_transform.Transform.connect_from(pointerstuff.HomeMat)

	timer = avango.nodes.TimeSensor()
	pointerstuff.timer.connect_from(timer.Time)
	#pointerstuff.HomeRef=home

	setupEnvironment.launch()


if __name__ == '__main__':
  start()