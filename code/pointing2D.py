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

#fitt's law parameter
D=0.9 #in meter
ID=2 #fitt's law
W=D/(2**ID-1) #in meter, Fitt's Law umgeformt nach W

balloonSound = avango.sound.nodes.SoundSource()
graph = avango.gua.nodes.SceneGraph(Name="scenegraph") #Create Graph
loader = avango.gua.nodes.TriMeshLoader() #Create Loader
pencil_transform = avango.gua.nodes.TransformNode()
aim = avango.gua.nodes.TransformNode()
aim_transform = avango.gua.nodes.TransformNode()
base = avango.gua.nodes.TransformNode()
base_transform = avango.gua.nodes.TransformNode()

class PointerManager(avango.script.Script):
	Button = avango.SFBool()
	TransMat = avango.gua.SFMatrix4()
	
	AimMat_scale = avango.gua.SFMatrix4()
	AimMat = avango.gua.SFMatrix4()

	BaseMat = avango.gua.SFMatrix4()

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
		AimMat = avango.gua.make_trans_mat(0.0, 0.0, setupEnvironment.getTargetDepth())

	def __del__(self):
		if setupEnvironment.logResults():
			self.result_file.close()

	@field_has_changed(Button)
	def button_pressed(self):
		if(setupEnvironment.onButtonPress()):
			if(self.Button.value):
				self.test()
			else:
				self.flagPrinted=False


	@field_has_changed(TransMat)
	def TransMatHasChanged(self):
		pass #print(self.TransMat.value)
		
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
					"Homepos: \n"+str(self.AimMat.value)+"\n\n")
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

	def test(self):
		if(self.startedTest==False):
			self.setStartTranslation()
			self.time_1=self.timer.value
			self.evenTrial=True
			self.startedTest=True
			print("Test started.\n")
		else:
			self.setID()
			self.nextSettingStep()
			if(self.evenTrial):
				self.time_2=self.timer.value
				self.evenTrial=False
				self.setMT(self.time_1, self.time_2)
			else:
				self.time_1=self.timer.value
				self.evenTrial=True
				self.setMT(self.time_2, self.time_1)
			self.setID()
			self.setTP()

			if(self.error<=self.AimMat_scale.value.get_scale().x/2):
				self.hit() 
			else:
				self.miss()

	def hit(self):
		print("Hell Yeah")
		setupEnvironment.setBackgroundColor(avango.gua.Color(0, 0.2, 0.05), 0.2)

	def miss(self):
		print("Oh fuck")
		setupEnvironment.setBackgroundColor(avango.gua.Color(0.3, 0, 0), 0.2)


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

	def setStartTranslation(self):
		self.AimMat.value=avango.gua.make_trans_mat(D/2, 0, 0)
		self.BaseMat.value=avango.gua.make_trans_mat(-D/2, 0, 0)

	def nextSettingStep(self):
		temp = self.BaseMat.value
		self.AimMat_old = self.AimMat
		self.BaseMat.value = self.AimMat.value
		self.AimMat.value = temp
		

	def getDistance2D(self, target1, target2):
		trans_x=target1.get_translate()[0]
		trans_y=target1.get_translate()[1]

		aim_x=target2.get_translate()[0]
		aim_y=target2.get_translate()[1]

		trans_aim_x_square=(trans_x - aim_x)*(trans_x - aim_x)
		trans_aim_y_square=(trans_y - aim_y)*(trans_y - aim_y)
		
		distance=math.sqrt(trans_aim_x_square+trans_aim_y_square)
		return distance

	def getDistance3D(self, target1, target2):
		trans_x=target1.get_translate()[0]
		trans_y=target1.get_translate()[1]
		trans_z=target1.get_translate()[2]

		aim_x=target2.get_translate()[0]
		aim_y=target2.get_translate()[1]
		aim_z=target2.get_translate()[2]

		trans_aim_x_square=(trans_x - aim_x)*(trans_x - aim_x)
		trans_aim_y_square=(trans_y - aim_y)*(trans_y - aim_y)
		trans_aim_z_square=(trans_z - aim_z)*(trans_z - aim_z)
		
		distance=math.sqrt(trans_aim_x_square+trans_aim_y_square+trans_aim_z_square)
		return distance

	def setError(self):
		if setupEnvironment.space3D()==False:
			self.error=self.getDistance2D(self.TransMat.value, self.AimMat.value)
		else:
			self.error=self.getDistance3D(self.TransMat.value, self.AimMat.value)

	def setID(self):
		# target_size=self.AimMat_scale.value.get_scale().x*2
		
		# if setupEnvironment.space3D()==False:
		# 	distance=self.getDistance2D(self.AimMat.value, self.AimMat_old.value)
		# else:
		# 	distance=self.getDistance3D(self.AimMat.value, self.AimMat_old.value)

		# self.ID=math.log10((distance/target_size)+1)/math.log10(2)
		self.ID = ID
		print("ID: "+ str(self.ID))

	def setMT(self, start, end):
		self.MT=end-start
		print("Time: " + str(self.MT))

	def setTP(self):
		self.TP=self.ID/self.MT

	def handle_key(self, key, scancode, action, mods):
		balloonSound.Play.value = True
		if action == 0:
			#32 is space 335 is num_enter
			if key==32:
				#balloonSound.Play.value = True
				#self.AimMat.value=self.getRandomTranslation()
				self.test()

			

def start ():
    #setup
	pointerManager = PointerManager()
	
	#loadMeshes
	setupEnvironment.getWindow().on_key_press(pointerManager.handle_key)
	setupEnvironment.setup(graph)

	pencil = loader.create_geometry_from_file("tracked_object_pointing", "data/objects/tracked_object_pointing.obj", avango.gua.LoaderFlags.NORMALIZE_SCALE)
	pencil.Transform.value=avango.gua.make_rot_mat(270, 1, 0, 0)*avango.gua.make_scale_mat(0.02)
	pencil.Material.value.set_uniform("Color", avango.gua.Vec4(0.5, 0.5, 0.5, 0.5))

	pencil_transform=avango.gua.nodes.TransformNode(Children=[pencil])

	aim = loader.create_geometry_from_file("light_sphere", "data/objects/light_sphere.obj", avango.gua.LoaderFlags.NORMALIZE_SCALE)
	aim.Transform.value = avango.gua.make_scale_mat(W)
	aim.Material.value.set_uniform("Color", avango.gua.Vec4(1, 0, 0, 1))

	base = loader.create_geometry_from_file("light_sphere", "data/objects/light_sphere.obj", avango.gua.LoaderFlags.NORMALIZE_SCALE)
	base.Transform.value = avango.gua.make_scale_mat(W)
	base.Material.value.set_uniform("Color", avango.gua.Vec4(0.8, 0, 0.2, 0.1))

	aim_transform=avango.gua.nodes.TransformNode(Children=[aim])
	base_transform=avango.gua.nodes.TransformNode(Children=[base])

	graph.Root.value.Children.value.extend([aim_transform, base_transform, pencil_transform])

	#sound
	# balloonSound = avango.sound.nodes.SoundSource()
	# balloonSound.URL.value = "data/sounds/balloon_pop.ogg"
	# balloonSound.Loop.value = True
	# balloonSound.Play.value = True
	# graph.Root.value.Children.value.extend([balloonSound])

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
	
	#connect aim with aim
	pointerManager.AimMat_scale.connect_from(aim.Transform)
	aim_transform.Transform.connect_from(pointerManager.AimMat)

	pointerManager.BaseMat.connect_from(base_transform.Transform)
	base_transform.Transform.connect_from(pointerManager.BaseMat)

	#setup timer
	timer = avango.nodes.TimeSensor()
	pointerManager.timer.connect_from(timer.Time)

	setupEnvironment.launch()


if __name__ == '__main__':
  start()
