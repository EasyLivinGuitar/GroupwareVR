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
	HomeMat_scale = avango.gua.SFMatrix4()
	isInside = False
	
	timer = avango.SFFloat()
	
	result_file = None

	read = False
	queue = queue.Queue()
	step = None


	def __init__(self):
		self.super(PointerStuff).__init__()
		self.HomeRef=None
		

	@field_has_changed(TransMat)
	def transMatHasChanged(self):
		distance=self.getDistance()

		if distance < self.HomeMat_scale.value.get_scale().x/2:
			self.inRange()
		else: 
			self.outRange()
		

	@field_has_changed(timer)
	def updateTimer(self):
		if self.read==False:
			self.readData()
			self.read=True

		self.play()

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

	def inRange(self):
		self.isInside = True
		self.HomeRef.Material.value.set_uniform("Color", avango.gua.Vec4(0, 1,0, 1)) #Transparenz funktioniert nicht

	def outRange(self):
		self.isInside = False
		self.HomeRef.Material.value.set_uniform("Color", avango.gua.Vec4(1, 0,0, 1)) #Transparenz funktioniert nicht

	def readData(self):
		path=input("Path to file for replay: ")

		self.result_file=open(path)
		gotValues=False
		
		lines=self.result_file.readlines()

		for i in range(len(lines)):
			check=lines[i].split()
			
			if(check):
				if(check[0]=="TimeStamp:"):
					timeStamp=float(check[1])
				if(check[0]=="Error:"):
					error=float(check[1])
				if(check[0]=="Pointerpos:"):
					pointer_mat=self.getMatrix(lines, i+1)
				if(check[0]=="Homepos:"):
					home_mat=self.getMatrix(lines, i+1)
					gotValues=True

				if(gotValues):
					step=MatrixStep(timeStamp, error, pointer_mat, home_mat)
					self.queue.put(step)
					gotValues=False


	def play(self):
		if(self.step==None):
			self.step=self.queue.get()
		if(self.step.TimeStamp<=self.timer.value):
			self.HomeMat.value=self.step.HomeMat
			self.TransMat.value=self.step.PointerMat
			self.step=None

	def getMatrix(self, lines, index):
		mat_line_1=lines[index].replace("(","")
		mat_line_2=lines[index+1]
		mat_line_3=lines[index+2]
		mat_line_4=lines[index+3].replace(")","")

		mat_1=mat_line_1.split()
		mat_2=mat_line_2.split()
		mat_3=mat_line_3.split()
		mat_4=mat_line_4.split()

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

		return matrix



class MatrixStep:
	TimeStamp=0.0
	Error=0.0
	PointerMat=avango.gua.SFMatrix4
	HomeMat=avango.gua.SFMatrix4

	def __init__(self, stamp, error, p_mat, h_mat):
		self.TimeStamp=stamp
		self.Error=error
		self.PointerMat=p_mat
		self.HomeMat=h_mat

			

def start ():
	graph=avango.gua.nodes.SceneGraph(Name="scenegraph") #Create Graph
	loader = avango.gua.nodes.TriMeshLoader() #Create Loader

	#Meshes
	pencil = loader.create_geometry_from_file("tracked_object", "data/objects/tracked_object.obj", avango.gua.LoaderFlags.NORMALIZE_SCALE)
	pencil.Transform.value=avango.gua.make_rot_mat(180, 1, 0, 0)*avango.gua.make_scale_mat(0.02)
	pencil.Material.value.set_uniform("Color", avango.gua.Vec4(0.5, 1, 0, 0.2))

	pencil_transform=avango.gua.nodes.TransformNode(Children=[pencil])

	home=loader.create_geometry_from_file("light_sphere", "data/objects/light_sphere.obj", avango.gua.LoaderFlags.NORMALIZE_SCALE)
	home.Transform.value = avango.gua.make_scale_mat(0.15)
	home.Material.value.set_uniform("Color", avango.gua.Vec4(1, 0,0, 1)) #Transparenz funktioniert nicht

	home_transform=avango.gua.nodes.TransformNode(Children=[home])

	tracking = setupEnvironment.setup(graph)

	graph.Root.value.Children.value.extend([pencil_transform, home_transform])


	pointer_device_sensor = avango.daemon.nodes.DeviceSensor(
		DeviceService = avango.daemon.DeviceService()
		)
	pointer_device_sensor.Station.value = "device-pointer"

	pointerstuff = PointerStuff()
	pointerstuff.HomeRef=home
	
	pointerstuff.HomeMat_scale.connect_from(home.Transform)
	pencil_transform.Transform.connect_from(pointerstuff.TransMat)
	home_transform.Transform.connect_from(pointerstuff.HomeMat)

	timer = avango.nodes.TimeSensor()
	pointerstuff.timer.connect_from(timer.Time)

	setupEnvironment.launch(globals())


if __name__ == '__main__':
  start()

  #results/results_pointing_2D/pointing2D_trial0.txt