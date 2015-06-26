import avango
import avango.daemon
import avango.gua
import avango.script
import random
import setupEnvironment
import math
import os.path
import avango.sound
import avango.sound.openal

from examples_common.GuaVE import GuaVE
from avango.script import field_has_changed

balloonSound = avango.sound.nodes.SoundSource()
graph = avango.gua.nodes.SceneGraph(Name="scenegraph") #Create Graph
loader = avango.gua.nodes.TriMeshLoader() #Create Loader
pencil_transform = avango.gua.nodes.TransformNode()
home = avango.gua.nodes.TransformNode();
home_transform = avango.gua.nodes.TransformNode();

class PointerManager(avango.script.Script):
	Button = avango.SFBool()
	TransMat = avango.gua.SFMatrix4()
	
	HomeMat_scale = avango.gua.SFMatrix4()
	HomeMat = avango.gua.SFMatrix4()
	HomeMat_old = avango.gua.SFMatrix4()

	timer = avango.SFFloat()
	time_1=0
	time_2=0
	
	result_file= None
	created_file=False
	num_files=0

	startedTest=False
	endedTest=False
	evenTrial=False
	flagPrinted=False

	error=0
	MT=0
	ID=0
	TP=0

	axis=["h", "h+45", "v", "v+45"]
	current_axis=None
	current_translations=[]
	axisDone=True

	def __init__(self):
		self.super(PointerManager).__init__()
		HomeMat = avango.gua.make_trans_mat(0.0, 0.0, setupEnvironment.getTargetDepth())

	def __del__(self):
		if setupEnvironment.logResults():
			self.result_file.close()

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

			self.HomeMat_old.value=self.HomeMat.value
			self.nextSettingStep()

			self.setID()

			if self.startedTest==False:
				self.startedTest=True
				print("Test started.\n")
		else:
			self.flagPrinted=False
		balloonSound.Play.value = True

	@field_has_changed(TransMat)
	def TransMatHasChanged(self):
		pass#print(self.TransMat.value);
		
	@field_has_changed(timer)
	def updateTimer(self):
		if setupEnvironment.ignoreZ():
			translation = self.TransMat.value.get_translate()
			translation.z = 0

			self.TransMat.value = avango.gua.make_trans_mat(translation)*avango.gua.make_rot_mat(self.TransMat.value.get_rotate())

		self.setError()
		if setupEnvironment.logResults():
			self.logData()

	def logData(self):
		path="results/results_pointing_2D/"
		if(self.startedTest and self.endedTest==False):
			if self.created_file==False: #create File 
				self.num_files=len([f for f in os.listdir(path)
					if os.path.isfile(os.path.join(path, f))])
				self.created_file=True
			else: #write permanent values
				self.result_file=open(path+"pointing2D_trial"+str(self.num_files)+".txt", "a+")
				
				self.result_file.write(
					"TimeStamp: "+str(self.timer.value)+"\n"
					"Error: "+str(self.error)+"\n"
					"Pointerpos: \n"+str(self.TransMat.value)+"\n"
					"Homepos: \n"+str(self.HomeMat.value)+"\n\n")
				self.result_file.close()
			
				if self.Button.value: #write resulting values
					self.result_file=open(path+"pointing2D_trial"+str(self.num_files)+".txt", "a+")
					if(self.flagPrinted==False):
						self.result_file.write(
							"MT: "+str(self.MT)+"\n"+
							"ID: "+str(self.ID)+"\n"+
							"TP: "+str(self.TP)+"\n"+
							"Total Error: "+str(self.error)+"\n"+
							"=========================\n\n")
						self.flagPrinted=True
					self.result_file.close()



	def getRandomTranslation(self):
		settings=[
			avango.gua.make_trans_mat(-0.8, -0.8, setupEnvironment.getTargetDepth()),
			avango.gua.make_trans_mat(-0.4, 0.4, setupEnvironment.getTargetDepth()),
			avango.gua.make_trans_mat(0.2, -0.2, setupEnvironment.getTargetDepth()),
			avango.gua.make_trans_mat(0.2, 0.2, setupEnvironment.getTargetDepth()),
			avango.gua.make_trans_mat(0.4, -0.4, setupEnvironment.getTargetDepth()),
			avango.gua.make_trans_mat(0.8, 0.8, setupEnvironment.getTargetDepth()),
			avango.gua.make_trans_mat(0.25, -0.25, setupEnvironment.getTargetDepth())
		]

		index=random.randint(0, len(settings)-1)
		
		return settings[index]

	def nextSettingStep(self):
		if(len(self.axis)>0 or len(self.current_translations)>0):
			if(self.axisDone):
				index=random.randint(0, len(self.axis)-1)
				self.current_axis=self.axis[index]
				del(self.axis[index])
				self.current_translations=self.getTranslations(self.current_axis)
				self.axisDone=False
	
			if(len(self.current_translations)==0):
				self.axisDone=True
				self.nextSettingStep()
			else:
				self.HomeMat.value=self.current_translations[0]
				del(self.current_translations[0])
		else:
			self.endedTest=True
			print("Test ended.\n")


	def getTranslations(self, axis):
		if(axis=="h"):
			translations=[
			avango.gua.make_trans_mat(0.25, 0, setupEnvironment.getTargetDepth()),
			avango.gua.make_trans_mat(-0.25, 0, setupEnvironment.getTargetDepth()),
			avango.gua.make_trans_mat(-0.125, 0, setupEnvironment.getTargetDepth()),
			avango.gua.make_trans_mat(0.125, 0, setupEnvironment.getTargetDepth()),
			avango.gua.make_trans_mat(0, 0, setupEnvironment.getTargetDepth())]
		if(axis=="h+45"):
			translations=[
			avango.gua.make_trans_mat(0.25, 0.25, setupEnvironment.getTargetDepth()),
			avango.gua.make_trans_mat(-0.25, -0.25, setupEnvironment.getTargetDepth()),
			avango.gua.make_trans_mat(-0.125, -0.125, setupEnvironment.getTargetDepth()),
			avango.gua.make_trans_mat(0.125, 0.125, setupEnvironment.getTargetDepth()),
			avango.gua.make_trans_mat(0, 0, setupEnvironment.getTargetDepth())]
		if(axis=="v"):
			translations=[
			avango.gua.make_trans_mat(0, 0.25, setupEnvironment.getTargetDepth()),
			avango.gua.make_trans_mat(0, -0.25, setupEnvironment.getTargetDepth()),
			avango.gua.make_trans_mat(0, -0.125, setupEnvironment.getTargetDepth()),
			avango.gua.make_trans_mat(0, 0.125, setupEnvironment.getTargetDepth()),
			avango.gua.make_trans_mat(0, 0, setupEnvironment.getTargetDepth())]
		if(axis=="v+45"):
			translations=[
			avango.gua.make_trans_mat(-0.25, 0.25, setupEnvironment.getTargetDepth()),
			avango.gua.make_trans_mat(0.25, -0.25, setupEnvironment.getTargetDepth()),
			avango.gua.make_trans_mat(0.125, -0.125, setupEnvironment.getTargetDepth()),
			avango.gua.make_trans_mat(-0.125, 0.125, setupEnvironment.getTargetDepth()),
			avango.gua.make_trans_mat(0, 0, setupEnvironment.getTargetDepth())]
		return translations
		

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
			self.error=self.getDistance2D(self.TransMat.value, self.HomeMat.value)
		else:
			self.error=self.getDistance3D(self.TransMat.value, self.HomeMat.value)

	def setID(self):
		target_size=self.HomeMat_scale.value.get_scale().x*2
		
		if setupEnvironment.space3D()==False:
			distance=self.getDistance2D(self.HomeMat.value, self.HomeMat_old.value)
		else:
			distance=self.getDistance3D(self.HomeMat.value, self.HomeMat_old.value)

		self.ID=math.log10((distance/target_size)+1)/math.log10(2)

	def setMT(self, start, end):
		self.MT=end-start

	def setTP(self):
		self.TP=self.ID/self.MT

	def handle_key(self, key, scancode, action, mods):
		balloonSound.Play.value = True
		if action == 0:
			#32 is space 335 is num_enter
			if key==335:
				balloonSound.Play.value = True
				self.HomeMat.value=self.getRandomTranslation()

			

def start ():
    #setup
	pointerManager = PointerManager()
	
	setupEnvironment.getWindow().on_key_press(pointerManager.handle_key)
	setupEnvironment.setup(graph)

	loadMeshes()
	setupSound()

	#connections
	pointer_device_sensor = avango.daemon.nodes.DeviceSensor(DeviceService = avango.daemon.DeviceService())
	pointer_device_sensor.TransmitterOffset.value = setupEnvironment.getOffsetTracking()

	pointer_device_sensor.Station.value = "pointer"


	button_sensor=avango.daemon.nodes.DeviceSensor(DeviceService=avango.daemon.DeviceService())
	button_sensor.Station.value="device-pointer"

	pointerManager.Button.connect_from(button_sensor.Button0)
	
	#connect transmat with matrix from deamon
	pointerManager.TransMat.connect_from(pointer_device_sensor.Matrix)
	
	#connect object at the place of transmat
	pencil_transform.Transform.connect_from(pointerManager.TransMat)
	
	#connect home with home
	pointerManager.HomeMat_scale.connect_from(home.Transform)
	#commented because redundant?
	home_transform.Transform.connect_from(pointerManager.HomeMat)

	#setup timer
	timer = avango.nodes.TimeSensor()
	pointerManager.timer.connect_from(timer.Time)

	setupEnvironment.launch()

def loadMeshes():
	pencil = loader.create_geometry_from_file("tracked_object", "data/objects/tracked_object.obj", avango.gua.LoaderFlags.NORMALIZE_SCALE)
	pencil.Transform.value=avango.gua.make_rot_mat(180, 1, 0, 0)*avango.gua.make_scale_mat(0.02)
	pencil.Material.value.set_uniform("Color", avango.gua.Vec4(0.5, 0.5, 0.5, 0.5))

	pencil_transform=avango.gua.nodes.TransformNode(Children=[pencil])

	home = loader.create_geometry_from_file("light_sphere", "data/objects/light_sphere.obj", avango.gua.LoaderFlags.NORMALIZE_SCALE)
	home.Transform.value = avango.gua.make_scale_mat(0.05)
	home.Material.value.set_uniform("Color", avango.gua.Vec4(1, 0, 0, 1))

	home_transform=avango.gua.nodes.TransformNode(Children=[home])

	graph.Root.value.Children.value.extend([home_transform, pencil_transform])

def setupSound():
	balloonSound = avango.sound.nodes.SoundSource()
	graph.Root.value.Children.value.extend([balloonSound])
	balloonSound.URL.value = "data/sounds/balloon_pop.ogg"
	balloonSound.Loop.value = False
	balloonSound.Play.value = True

if __name__ == '__main__':
  start()
