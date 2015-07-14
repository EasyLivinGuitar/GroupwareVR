import avango
import avango.daemon
import avango.gua
import avango.script
import random
import setupEnvironment
import logManager
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

FRAMES_FOR_SPEED=4 #How many frames token to calculate speed and acceleration

THRESHHOLD=0.3

FRAMES_FOR_AUTODETECT=3 #How many frames you have to be under the speed threshold to detect

logmanager= logManager.logManager()

balloonSound = avango.sound.nodes.SoundSource()
graph = avango.gua.nodes.SceneGraph(Name="scenegraph") #Create Graph
loader = avango.gua.nodes.TriMeshLoader() #Create Loader
pencil_transform = avango.gua.nodes.TransformNode()
aim = avango.gua.nodes.TransformNode()
aim_transform = avango.gua.nodes.TransformNode()
base = avango.gua.nodes.TransformNode()
base_transform = avango.gua.nodes.TransformNode()

class trackingManager(avango.script.Script):
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
	lastTime=0
	time_2=0
	start_time=0
	end_time=0
	start_time2=0
	end_time2=0
	
	result_file= None
	created_file=False
	num_files=0

	startedTests=False
	endedTests=False
	flagPrinted=False

	current_index = 0
	counter = 0

	speed_time1=0
	speed_time2=0

	current_speed = 0
	peak_speed=0
	current_acceleration = 0
	peak_acceleration=0
	first_reversal_acceleration=0
	first_reversal_point=0
	reversal_points=[]
	frame_counter = 0
	frame_counter2 = 0

	low_speed_counter=0

	inside=False
	first=True


	# Logging
	userID=0
	group=0
	trial=0
	hits=0
	goal = False
	error=0
	last_error=0
	MT=0
	ID=0
	TP=0
	overshoots=0


	def __init__(self):
		self.super(trackingManager).__init__()
		AimMat = avango.gua.make_trans_mat(0.0, 0.0, 0)

	def __del__(self):
		if setupEnvironment.logResults():
			self.result_file.close()

	@field_has_changed(Button)
	def button_pressed(self):
		if(self.endedTests==False):
			if(self.Button.value):
				self.next()
			else:
				self.flagPrinted=False
		
	@field_has_changed(timer)
	def updateTimer(self):
		translation = self.TransMat.value.get_translate()
		if not setupEnvironment.space3D:
			self.TransMat.value = avango.gua.make_rot_mat(90, 1, 0, 0)*avango.gua.make_rot_mat(self.TransMat.value.get_rotate())
			tmp = translation.y
			translation.y = -translation.z-setupEnvironment.offsetTracking.get_translate().y
			translation.z = tmp

		if(self.startedTests and self.endedTests==False):
			self.setSpeed()
			self.setAcceleration()
			self.setError()
			self.setOvershoots()
			self.autoDetect()

		if setupEnvironment.logResults:	
			pass #save replay, todo

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
						self.logSetter()
						logmanager.log(self.result_file)
						self.resetValues()
						self.flagPrinted=True
					self.result_file.close()

	def logSetter(self):
		self.setError()
		self.last_error=self.error
		self.setID(self.current_index)
		self.setMT(self.lastTime, self.timer.value)
		self.setTP(self.current_index)
		logmanager.setUserID(self.userID)
		logmanager.setGroup(self.group)
		if setupEnvironment.space3D:
			if setupEnvironment.reduceDOFTranslate:
				logmanager.setCondition("pointing2D_air_locked_virtual")
				logmanager.setDOFVirtual(2, 0)
			else:
				logmanager.setCondition("pointing2D_air_free_virtual")
				logmanager.setDOFVirtual(3, 0)
			logmanager.setDOFReal(3, 0)
		else:
			if setupEnvironment.reduceDOFTranslate:
				logmanager.setCondition("pointing2D_table_locked_virtual")
				logmanager.setDOFVirtual(2, 0)
				logmanager.setDOFReal(2, 0)
		if(self.AimMat.value.get_translate().x>self.BaseMat.value.get_translate().x): #aim is right
			logmanager.setMovementDirection("r")
		else:
			logmanager.setMovementDirection("l")
		logmanager.setTargetDistance_t(D)
		logmanager.setTargetWidth_t(W[self.current_index])
		logmanager.setRotationAxis(0)
		logmanager.setTargetDistance_r(0)
		logmanager.setTargetWidth_r(0)
		logmanager.setID_combined(self.ID, 0)
		logmanager.setRepetition(N)
		logmanager.setTrial(self.trial)

		if setupEnvironment.useAutoDetect:
			logmanager.setHit("AUTO", self.MT, self.last_error, 0)
			logmanager.setClicks(0, 0)
		else:
			logmanager.setHit("BUTTON", self.MT, self.last_error, 0)
			logmanager.setClicks(self.trial, self.hits)

		logmanager.setSuccess(self.goal)
		logmanager.setPeakSpeed(self.peak_speed)
		logmanager.setMovementContinuity(self.peak_acceleration, self.first_reversal_acceleration)
		logmanager.setReversalPoints(self.first_reversal_point, len(self.reversal_points))

	def resetValues(self):
		self.overshoots=0
		self.peak_acceleration=0
		self.first_reversal_acceleration=0
		self.peak_speed=0
		self.first=True
		self.inside=False
		self.goal=False

	def autoDetect(self):
		if(math.fabs(self.current_speed) < THRESHHOLD and self.peak_speed>THRESHHOLD):
			if(self.low_speed_counter < FRAMES_FOR_AUTODETECT-1):
				self.low_speed_counter=self.low_speed_counter+1
			else:
				self.low_speed_counter=0
				if(self.first):
					self.first_reversal_point=self.TransMat.value.get_translate().x
					print(self.first_reversal_point)
					self.first_reversal_acceleration=self.current_acceleration
					self.first=False
				self.reversal_points.append(self.TransMat.value.get_translate().x)


	def next(self):
		if(self.endedTests==False):	
			if(self.startedTests==False):
				#start
				self.AimMat.value=avango.gua.make_trans_mat(D/2, 0, 0)
				self.BaseMat.value=avango.gua.make_trans_mat(-D/2, 0, 0)
				self.startedTests=True
				self.TransMat_old_x_translate = self.TransMat.value.get_translate().x
				self.lastTime=self.timer.value
				print("Tests started.\n")
			else:
				self.trial=self.trial+1
				if(self.counter==N-1):
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
					self.nextSettingStep()
					if(self.error <= self.AimMat_scale.value.get_scale().x/2):
						self.hit() 
					else:
						self.miss()

	def nextSettingStep(self):
		#switches aim and shadow aim
		temp = self.BaseMat.value
		self.AimMat_old = self.AimMat
		self.BaseMat.value = self.AimMat.value 
		self.AimMat.value = temp


		self.AimMat_scale.value = avango.gua.make_scale_mat(W[self.current_index])
		self.BaseMat_scale.value = avango.gua.make_scale_mat(W[self.current_index])			


	def hit(self):
		self.hits=self.hits+1
		self.goal=True
		setupEnvironment.playSound("balloon")
		setupEnvironment.setBackgroundColor(avango.gua.Color(0, 0.2, 0.05), 0.18)

	def miss(self):
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
		
	def setError(self):
		self.error = setupEnvironment.getDistance3D(self.TransMat.value, self.AimMat.value)

	def setID(self, index):
		self.ID = ID[index]

	def setMT(self, start, end):
		self.MT=end-start
		self.lastTime=self.timer.value

	def setTP(self, index):
		if(self.MT>0):
			self.TP=ID[index]/self.MT

	def setSpeed(self):
		if(self.frame_counter % 5 == 0):
			self.TransTranslation1=self.TransMat.value.get_translate()
			self.start_time=self.timer.value
		else: 
			if(self.frame_counter % 5 == FRAMES_FOR_SPEED-1):
				self.TransTranslation2=self.TransMat.value.get_translate()
				self.end_time=self.timer.value
				div=self.TransTranslation2-self.TransTranslation1
				length=math.sqrt(div.x**2 + div.y**2 + div.z**2)
				time=self.end_time-self.start_time
				self.current_speed=length/time

				if(self.current_speed<10**-3):
					self.current_speed=0

				if(self.current_speed>self.peak_speed):
					self.peak_speed=self.current_speed
			
		self.frame_counter=self.frame_counter+1

	def setAcceleration(self):
		if(self.frame_counter2 % 5 == 0):
			self.speed_time1=self.current_speed
			self.start_time2=self.timer.value
		else:
			if(self.frame_counter2 % 5 == FRAMES_FOR_SPEED-1):
				self.speed_time2=self.current_speed
				self.end_time2=self.timer.value
				div=self.speed_time2-self.speed_time1
				time=self.end_time2-self.start_time2
				self.current_acceleration=div/time

				if(self.current_acceleration>self.peak_acceleration):
					self.peak_acceleration=self.current_acceleration

		self.frame_counter2=self.frame_counter2+1

	def setOvershoots(self):
		if(self.error < self.AimMat_scale.value.get_scale().x/2):
			self.inside=True
		else:
			if(self.inside):
				self.overshoots=self.overshoots+1
				print("Overshoots: "+str(self.overshoots))
				self.inside=False


	def handle_key(self, key, scancode, action, mods):
		if action == 1:
			#32 is space 335 is num_enter
			if key==32 or key==335:
				self.Button.value=True
		else:
			self.Button.value=False
			self.flagPrinted=False

			
def start ():
	trackManager = trackingManager()
	trackManager.userID=input("USER_ID: ")
	trackManager.group=input("GROUP: ")

	setupEnvironment.getWindow().on_key_press(trackManager.handle_key)
	setupEnvironment.setup(graph)

	aim = loader.create_geometry_from_file("light_sphere", "data/objects/sphere_new.obj", avango.gua.LoaderFlags.NORMALIZE_SCALE)
	aim.Transform.value = avango.gua.make_scale_mat(W[0])
	aim.Material.value.set_uniform("Color", avango.gua.Vec4(1, 1, 0, 1))
	setupEnvironment.everyObject.Children.value.append(aim)

	base = loader.create_geometry_from_file("light_sphere", "data/objects/sphere_new.obj", avango.gua.LoaderFlags.NORMALIZE_SCALE)
	base.Transform.value = avango.gua.make_scale_mat(W[0])
	base.Material.value.set_uniform("Color", avango.gua.Vec4(0.5, 0.5, 0.5, 0.1))
	setupEnvironment.everyObject.Children.value.append(base)

	aim_transform=avango.gua.nodes.TransformNode(Children=[aim])
	base_transform=avango.gua.nodes.TransformNode(Children=[base])

	#loadMeshes
	trackManager.pcNode = setupEnvironment.PencilContainer().getNode()

	#listen to button
	button_sensor=avango.daemon.nodes.DeviceSensor(DeviceService=avango.daemon.DeviceService())
	button_sensor.Station.value="device-pointer"

	trackManager.Button.connect_from(button_sensor.Button0)

	#timer
	timer = avango.nodes.TimeSensor()
	trackManager.timer.connect_from(timer.Time)

	setupEnvironment.launch(globals())


if __name__ == '__main__':
  start()
