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
D=0.5 #in meter
ID=[3, 4, 5] #fitt's law
N=5 #number of tests per ID
W=[D/(2**ID[0]-1), D/(2**ID[1]-1), D/(2**ID[2]-1)] #in meter, Fitt's Law umgeformt nach W

FRAMES_FOR_SPEED=4 #How many frames token to calculate speed

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
	BaseMat_scale = avango.gua.SFMatrix4()

	TransMat_old_x_translate = 0
	point_of_turn = 0

	TransTranslation1=avango.gua.Vec3()
	TransTranslation2=avango.gua.Vec3()

	timer = avango.SFFloat()
	time_1=0
	time_2=0
	start_time=0
	end_time=0
	
	result_file= None
	created_file=False
	num_files=0

	startedTests=False
	endedTests=False
	flagPrinted=False

	error=0
	last_error=0
	MT=0
	ID=0
	TP=0

	current_index = 0
	counter = 0

	goal = False

	current_speed = 0
	frame_counter = 0


	def __init__(self):
		self.super(PointerManager).__init__()
		AimMat = avango.gua.make_trans_mat(0.0, 0.0, 0)

	def __del__(self):
		if setupEnvironment.logResults():
			self.result_file.close()

	@field_has_changed(Button)
	def button_pressed(self):
		if(self.endedTests==False):
			if(self.Button.value):
				self.last_error=self.error
				self.next()
			else:
				self.flagPrinted=False


	@field_has_changed(TransMat)
	def TransMatHasChanged(self):
		if setupEnvironment.useAutoDetect():
			if(setupEnvironment.useAutoDetect()==True and self.endedTests==False):
				if(self.AimMat.value.get_translate().x > self.BaseMat.value.get_translate().x): #Aim is right
					if(self.TransMat.value.get_translate().x < self.TransMat_old_x_translate):
						self.point_of_turn=self.TransMat.value.get_translate().x
						
						self.next()
				else: #Aim is left
					if(self.TransMat.value.get_translate().x > self.TransMat_old_x_translate): 
						self.point_of_turn=self.TransMat.value.get_translate().x

						self.next()

				self.TransMat_old_x_translate=self.TransMat.value.get_translate().x
		
	@field_has_changed(timer)
	def updateTimer(self):
		translation = self.TransMat.value.get_translate()
		if not setupEnvironment.space3D():
			self.TransMat.value = avango.gua.make_rot_mat(90, 1, 0, 0)*avango.gua.make_rot_mat(self.TransMat.value.get_rotate())
			tmp = translation.y
			translation.y = -translation.z-setupEnvironment.getOffsetTracking().get_translate().y
			translation.z = tmp

		if setupEnvironment.ignoreZ():
			translation.z = 0

		self.TransMat.value = avango.gua.make_trans_mat(translation)*avango.gua.make_rot_mat(self.TransMat.value.get_rotate())

		self.setSpeed()
		self.setError()
		if setupEnvironment.logResults():
			self.logData()

	def logData(self):
		path="results/results_pointing_2D/"
		if(self.startedTests and self.endedTests==False):
			if self.created_file==False: #create File 
				self.num_files=len([f for f in os.listdir(path)
					if os.path.isfile(os.path.join(path, f))])
				self.created_file=True
			else: #write permanent values
				self.result_file=open(path+"pointing2D_trial"+str(self.num_files)+".replay", "a+")
				
				self.result_file.write(
					"TimeStamp: "+str(self.timer.value)+"\n"+
					"Error: "+str(self.error)+"\n"+
					"Speed: "+str(self.current_speed)+"\n"
					"Pointerpos: \n"+str(self.TransMat.value)+"\n"
					"Aimpos: \n"+str(self.AimMat.value)+"\n\n")
				self.result_file.close()
			
				if self.Button.value: #write resulting values
					self.result_file=open(path+"pointing2D_trial"+str(self.num_files)+".log", "a+")
					if(self.flagPrinted==False):
						self.result_file.write(
							"HT: "+str(self.goal)+"\n"+
							"MT: "+str(self.MT)+"\n"+
							"ID: "+str(self.ID)+"\n"+
							"TP: "+str(self.TP)+"\n"+
							"W : "+str(W[self.current_index])+"\n"
							"Last Error: "+str(self.last_error)+"\n"+
							"=========================\n\n")
						self.flagPrinted=True
					self.result_file.close()

	def next(self):
		if(self.endedTests==False):	
			if(self.startedTests==False):
				self.setStartTranslation()
				self.time_1=self.timer.value
				self.startedTests=True
				self.TransMat_old_x_translate = self.TransMat.value.get_translate().x
				print("Tests started.\n")
			else:
				if(self.counter==N):
					self.counter=0
					self.current_index=self.current_index+1
				else:
					self.counter=self.counter+1

				if(self.current_index==len(W)):
					self.current_index=0
					self.endedTests = True
					setupEnvironment.setBackgroundColor(avango.gua.Color(0, 0.2, 1), 1)
					print("Tests finished")
				else:
					self.setID(self.current_index)
					self.nextSettingStep()
					self.setMT(self.time_1, self.timer.value)
					self.setID(self.current_index)
					self.setTP(self.current_index)
					if(self.error <= self.AimMat_scale.value.get_scale().x/2):
						self.hit() 
					else:
						self.miss()

	def hit(self):
		print("HIT")
		self.goal=True
		setupEnvironment.playSound("balloon")
		setupEnvironment.setBackgroundColor(avango.gua.Color(0, 0.2, 0.05), 0.18)

	def miss(self):
		print("MISS")
		self.goal=False
		setupEnvironment.playSound("miss")
		setupEnvironment.setBackgroundColor(avango.gua.Color(0.3, 0, 0), 0.18)


	def getRandomTranslation(self):
		settings=[
			avango.gua.make_trans_mat(-0.8, -0.8, 0),
			avango.gua.make_trans_mat(-0.4, 0.4, 0),
			avango.gua.make_trans_mat(0.2, -0.2, 0),
			avango.gua.make_trans_mat(0.2, 0.2, 0),
			avango.gua.make_trans_mat(0.4, -0.4, 0),
			avango.gua.make_trans_mat(0.8, 0.8, 0),
			avango.gua.make_trans_mat(0.25, -0.25, 0)
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

		self.AimMat_scale.value = avango.gua.make_scale_mat(W[self.current_index])
		self.BaseMat_scale.value = avango.gua.make_scale_mat(W[self.current_index])
		

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

	def setID(self, index):
		self.ID = ID[index]
		print("ID: "+ str(self.ID))

	def setMT(self, start, end):
		self.MT=end-start
		print("Time: " + str(self.MT))

	def setTP(self, index):
		if(self.MT>0):
			self.TP=ID[index]/self.MT

	def setSpeed(self):
		if(self.frame_counter == 0):
			self.TransTranslation1=self.TransMat.value.get_translate()
			self.start_time=self.timer.value
			self.frame_counter=self.frame_counter+1
		else: 
			if(self.frame_counter == FRAMES_FOR_SPEED):
				self.TransTranslation2=self.TransMat.value.get_translate()
				self.end_time=self.timer.value
				self.frame_counter=0
				div=self.TransTranslation2-self.TransTranslation1
				length=math.sqrt(div.x**2 + div.y**2 + div.z**2)
				time=self.end_time-self.start_time
				self.current_speed=length/time

				if(self.current_speed<10**-3):
					self.current_speed=0
			else:
				self.frame_counter=self.frame_counter+1



	def handle_key(self, key, scancode, action, mods):
		if action == 1:
			#32 is space 335 is num_enter
			if key==32 or key==335:
				self.Button.value=True
		else:
			self.Button.value=False
			self.flagPrinted=False

			
def start ():
    #setup
	pointerManager = PointerManager()
	
	#loadMeshes
	setupEnvironment.getWindow().on_key_press(pointerManager.handle_key)
	setupEnvironment.setup(graph)

	pencil = loader.create_geometry_from_file("tracked_object_pointing", "data/objects/thin_pointer_abstract.obj", avango.gua.LoaderFlags.DEFAULTS)
	pencil.Transform.value = avango.gua.make_scale_mat(1)
	pencil.Material.value.set_uniform("Color", avango.gua.Vec4(1.0, 1.0, 1.0, 1.0))
	#pencil.Material.value.set_uniform("Emissivity", 1.0)
	pencil.Material.value.EnableBackfaceCulling.value = False

	pencil_transform=avango.gua.nodes.TransformNode(Children=[pencil])

	aim = loader.create_geometry_from_file("light_sphere", "data/objects/light_sphere.obj", avango.gua.LoaderFlags.NORMALIZE_SCALE)
	aim.Transform.value = avango.gua.make_scale_mat(W[0])
	aim.Material.value.set_uniform("Color", avango.gua.Vec4(1, 1, 0, 1))
	#aim.Material.value.enableBackfaceCulling.value = False

	base = loader.create_geometry_from_file("light_sphere", "data/objects/light_sphere.obj", avango.gua.LoaderFlags.NORMALIZE_SCALE)
	base.Transform.value = avango.gua.make_scale_mat(W[0])
	base.Material.value.set_uniform("Color", avango.gua.Vec4(0.5, 0.5, 0.5, 0.1))

	aim_transform=avango.gua.nodes.TransformNode(Children=[aim])
	base_transform=avango.gua.nodes.TransformNode(Children=[base])


	everyObject = avango.gua.nodes.TransformNode(
		Children = [aim_transform, base_transform, pencil_transform], 
		Transform = setupEnvironment.getCenterPosition()
	)

	graph.Root.value.Children.value.append(everyObject)

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
	aim.Transform.connect_from(pointerManager.AimMat_scale)
	aim_transform.Transform.connect_from(pointerManager.AimMat)

	pointerManager.BaseMat.connect_from(base_transform.Transform)
	base_transform.Transform.connect_from(pointerManager.BaseMat)

	pointerManager.BaseMat_scale.connect_from(base.Transform)
	base.Transform.connect_from(pointerManager.BaseMat_scale)

	#setup timer
	timer = avango.nodes.TimeSensor()
	pointerManager.timer.connect_from(timer.Time)

	setupEnvironment.launch(globals())


if __name__ == '__main__':
  start()
