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

class trackingManager(avango.script.Script):
	Button = avango.SFBool()

	PencilMat = avango.gua.SFMatrix4()

	AimMat_old = avango.gua.SFMatrix4()
	AimMat_scale = avango.gua.SFMatrix4()
	AimMat = avango.gua.SFMatrix4()

	timer = avango.SFFloat()
	time_1 = 0
	time_2 = 0

	result_file = None
	created_file = False
	num_files = 0

	startedTest = False
	endedTest = False
	evenTrial = False
	flagPrinted = False

	rot_error=0
	trans_error=0
	MT=0
	ID=0
	TP=0

	def __init__(self):
		self.super(trackingManager).__init__()

	@field_has_changed(Button)
	def button_pressed(self):
		if self.Button.value:
			if(self.evenTrial==False):
				self.time_1=self.timer.value
				self.evenTrial=True

				if(self.startedTest):
					self.setMT(self.time_2, self.time_1)
					self.setTP()
			else:
				self.time_2=self.timer.value
				self.evenTrial=False

				self.setMT(self.time_1, self.time_2)
				self.setTP()

			self.AimMat_old.value=self.AimMat.value
			self.nextSettingStep()

			self.setID()

			if self.startedTest==False:
				self.startedTest=True
				print("Test started.\n")
		else:
			self.flagPrinted=False
		
	@field_has_changed(timer)
	def updateTimer(self):
		if setupEnvironment.ignoreZ():
			translation = self.PencilMat.value.get_translate()
			translation.z = 0

			self.PencilMat.value = avango.gua.make_trans_mat(translation)*avango.gua.make_rot_mat(self.PencilMat.value.get_rotate())

		self.setError()
		self.logData()

	def logData(self):
		path="results/results_docking_2D/"
		if(self.startedTest and self.endedTest==False):
			if self.created_file==False: #create File 
				self.num_files=len([f for f in os.listdir(path)
					if os.path.isfile(os.path.join(path, f))])
				self.created_file=True
			else: #write permanent values
				self.result_file=open(path+"docking2D_trial"+str(self.num_files)+".txt", "a+")
				
				self.result_file.write(
					"TimeStamp: "+str(self.timer.value)+"\n"
					"Error: "+str(self.error)+"\n"
					"Pointerpos: \n"+str(self.PencilMat.value)+"\n"
					"Homepos: \n"+str(self.AimMat.value)+"\n\n")
				self.result_file.close()
			
				if self.Button.value: #write resulting values
					self.result_file=open(path+"docking2D_trial"+str(self.num_files)+".txt", "a+")
					if(self.flagPrinted==False):
						self.result_file.write(
							"MT: "+str(self.MT)+"\n"+
							"ID: "+str(self.ID)+"\n"+
							"TP: "+str(self.TP)+"\n"+
							"Total Error: "+str(self.error)+"\n"+
							"=========================\n\n")
						self.flagPrinted=True
					self.result_file.close()

	def nextSettingStep(self):
		print("Next")

	def getDistance2D(self, target1, target2):
		trans_x=target1.get_translate()[0]
		trans_y=target1.get_translate()[1]

		home_x=target2.get_translate()[0]
		home_y=target2.get_translate()[1]

		trans_home_x_square=(trans_x - home_x)*(trans_x - home_x)
		trans_home_y_square=(trans_y - home_y)*(trans_y - home_y)
		
		distance=math.sqrt(trans_home_x_square+trans_home_y_square)
		return distance

	def getDistance3D(self, target1, target2):
		trans_x=target1.get_translate()[0]
		trans_y=target1.get_translate()[1]
		trans_z=target1.get_translate()[2]

		home_x=target2.get_translate()[0]
		home_y=target2.get_translate()[1]
		home_z=target2.get_translate()[2]

		trans_home_x_square=(trans_x - home_x)*(trans_x - home_x)
		trans_home_y_square=(trans_y - home_y)*(trans_y - home_y)
		trans_home_z_square=(trans_z - home_z)*(trans_z - home_z)
		
		distance=math.sqrt(trans_home_x_square+trans_home_y_square+trans_home_z_square)
		return distance

	def setError(self):
		if setupEnvironment.space3D()==False:
			distance=self.getDistance2D(self.PencilMat.value, self.AimMat.value)
		else:
			distance=self.getDistance3D(self.PencilMat.value, self.AimMat.value)

		self.trans_error=distance
		pencil_rot=self.PencilMat.value.get_rotate().get_axis() 
			* self.PencilMat.value.get_rotate.get_angle()

		aim_rot=self.AimMat.value.get_rotate().get_axis()
			* self.AimMat.value.get_rotate.get_angle()

		delta=pencil_rot-aim_rot

		delta_x_square = error.x*error.x
		delta_y_square = error.y*error.y
		delta_z_square = error.z*error.z

		self.rot_error=math.sqrt(delta_x_square+delta_y_square+delta_z_square)



	def setID(self):
		target_size=self.AimMat_scale.value.get_scale().x*2
		
		if setupEnvironment.space3D()==False:
			distance=self.getDistance2D(self.AimMat.value, self.AimMat_old.value)
		else:
			distance=self.getDistance3D(self.AimMat.value, self.AimMat_old.value)

		self.ID=math.log10((distance/target_size)+1)/math.log10(2)

	def setMT(self, start, end):
		self.MT=end-start

	def setTP(self):
		self.TP=self.ID/self.MT

def start():
	graph = avango.gua.nodes.SceneGraph(Name="scenegraph") #Create Graph
	loader = avango.gua.nodes.TriMeshLoader() #Create Loader

	#Meshes
	pencil = loader.create_geometry_from_file("tracked_object", "data/objects/tracked_object.obj", avango.gua.LoaderFlags.NORMALIZE_SCALE)
	pencil.Transform.value=avango.gua.make_rot_mat(180, 1, 0, 0)*avango.gua.make_scale_mat(0.02)
	pencil.Material.value.set_uniform("Color", avango.gua.Vec4(0.5, 0.5, 0.5, 0.5))

	pencil_transform=avango.gua.nodes.TransformNode(Children=[pencil])

	aim = loader.create_geometry_from_file("light_sphere", "data/objects/light_sphere.obj", avango.gua.LoaderFlags.NORMALIZE_SCALE)
	aim.Transform.value = avango.gua.make_scale_mat(0.05)
	aim.Material.value.set_uniform("Color", avango.gua.Vec4(1, 0, 0, 1))

	aim_transform=avango.gua.nodes.TransformNode(Children=[aim])

	trackingmanager = trackingManager()

	#setup
	#setupEnvironment.getWindow().on_key_press(trackingmanager.handle_key)
	setupEnvironment.setup(graph)

	graph.Root.value.Children.value.extend([aim_transform, pencil_transform])

	pointer_device_sensor = avango.daemon.nodes.DeviceSensor(DeviceService = avango.daemon.DeviceService())
	pointer_device_sensor.TransmitterOffset.value = setupEnvironment.getOffsetTracking()

	pointer_device_sensor.Station.value = "LATUS-M1"


	button_sensor=avango.daemon.nodes.DeviceSensor(DeviceService=avango.daemon.DeviceService())
	button_sensor.Station.value="device-pointer"

	trackingmanager.Button.connect_from(button_sensor.Button0)
	
	#connect transmat with matrix from deamon
	trackingmanager.PencilMat.connect_from(pointer_device_sensor.Matrix)
	
	#connect object at the place of transmat
	pencil_transform.Transform.connect_from(trackingmanager.PencilMat)
	
	#connect home with home
	trackingmanager.AimMat.connect_from(aim_transform.Transform)
	trackingmanager.AimMat_scale.connect_from(aim.Transform)
	aim_transform.Transform.connect_from(trackingmanager.AimMat)

	timer = avango.nodes.TimeSensor()
	trackingmanager.timer.connect_from(timer.Time)

	setupEnvironment.launch()

if __name__ == '__main__':
  start()