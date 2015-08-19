import avango
import avango.daemon
import avango.gua
import avango.script
import random
import setupEnvironment
import logManager
import math
import os.path

from examples_common.GuaVE import GuaVE
from avango.script import field_has_changed

DISABLEROTATION = False

setup_environment = setupEnvironment.setupEnvironment()
r = setup_environment.r #circle radius

#fitt's law parameter
D_rot=45 #in degrees
D_trans= 0.3 #in meter
ID=[3, 5, 6] #fitt's law
N=15 #number of tests per ID
W_rot=[]
W_trans=[]
targetDiameter =[]
for i in range(0, len(ID)):
	W_rot.append(D_rot/(2**(ID[i]/2)-1)) #in degrees, Fitt's Law umgeformt nach W

	#halbiere ID wenn es noch einen Rotations-Anteil gibt
	if DISABLEROTATION == True:
		divisor = 1
	else:
		divisor = 2
		targetDiameter.append(2*r*math.tan(W_rot[i]/2*math.pi/180))#größe (Druchmesser) der Gegenkathete auf dem kreisumfang
	W_trans.append(D_trans/(2**(ID[i]/divisor)-1)) #in degrees, Fitt's Law umgeformt nach W


THRESHHOLD_TRANSLATE = 0.3
FRAMES_FOR_AUTODETECT_TRANSLATE = 3

FRAMES_FOR_AUTODETECT_ROTATE = 3
THRESHHOLD_ROTATE = 40
FRAMES_FOR_SPEED = 4 #How many frames taken to calculate speed and acceleration

if DISABLEROTATION:
	taskString = "pointing"
else:
	taskString = "docking"

graph = avango.gua.nodes.SceneGraph(Name ="scenegraph") #Create Graph
loader = avango.gua.nodes.TriMeshLoader() #Create Loader
pencil_transform = avango.gua.nodes.TransformNode()

logmanager =logManager.logManager()

class trackingManager(avango.script.Script):
	Button = avango.SFBool()
	timer = avango.SFFloat()
	
	time2= 0

	startedTests = False
	endedTests = False

	created_logfile = False
	created_replayfile = False

	current_index= 0
	counter = 0

	#Logging
	userID = 0
	group = 0
	trial = 1
	clicks = 0

	MT = 0
	ID = 0
	TP = 0
	overshoots_r = 0
	overshoots_t = 0
	overshootInside_translate = False;
	overshootInside_rotate = False;

	frame_counter_speed = 0
	frame_counter_acceleration = 0

	low_speed_counter = 0

	goal = False

	peak_speed_t = 0
	peak_speed_r = 0

	current_speed_translate = 0
	current_speed_rotate = 0
	current_acceleration_translate = 0
	current_acceleration_rotate = 0
	peak_acceleration_t = 0
	peak_acceleration_r = 0
	first_reversal_acceleration_t = 0
	first_reversal_acceleration_rotate = 0
	first_reversal_point_t = 0
	first_reversal_point_r = 0
	first_translate = True
	first_rotate = True
	reversal_points_t = []
	reversal_points_r = []

	succesful_clicks= 0

	frame_counter = 0
	frame_counter2 = 0

	low_speed_counter_translate = 0
	low_speed_counter_rotate = 0

	local_peak_speed_r = 0
	speededup = False

	inside = False

	# Logging
	userID = 0
	group = 0
	trial = 0
	hits = 0
	goal = False
	error = 0
	last_error = 0
	MT= 0
	ID= 0
	TP= 0

	PContainer = None

	def __init__(self):
		self.super(trackingManager).__init__()
		self.isInside = False;
		self.startTime = 0
		self.taskNum = 0
		self.disks = setupEnvironment.DisksContainer(setup_environment)
		self.aim = None
		self.aimShadow = None
		self.index = 0
		self.pcNode = None

	def __del__(self):
		if setup_environment.logResults:
			pass # self.result_file.close()

	@field_has_changed(Button)
	def button_pressed(self):
		if self.Button.value == True:
			if(self.endedTests== False):
				self.select()
				if setup_environment.logResults:	
					self.logData()

				self.nextSettingStep()
			else:
				print("Tests ended")
		else:
			self.flagPrinted = False
		

	@field_has_changed(timer)
	def updateTimer(self):
		if not self.endedTests:
			highlightR = False

			#position disks
			if not DISABLEROTATION:
				if setup_environment.getDistance3D(self.pcNode.Transform.value, self.aim.Transform.value) <= W_trans[self.index] :
					#attach disks to pointer
					self.disks.setTranslate( avango.gua.make_trans_mat(self.pcNode.Transform.value.get_translate()) )
				else:
					#attach disks to aim
					self.disks.setTranslate( avango.gua.make_trans_mat(self.aim.Transform.value.get_translate()) )

				#highlight rotation if near target
				if setup_environment.showWhenInTarget:	
					#highlight rotation if near target
					if setup_environment.getDistance3D(self.pcNode.Transform.value, self.aim.Transform.value) <= W_trans[self.index] and self.getErrorRotate() < W_rot[self.index]/2:
						highlightT = True
						self.disks.highlightRed()
					else:
						self.disks.setColor()
			
			#highlight translation
			highlightT = False
			if setup_environment.showWhenInTarget:
				if self.getErrorTranslate() < W_trans[self.index]/2:
					self.aim.Material.value.set_uniform("Color", avango.gua.Vec4(1, 0.8, 0, 0.8))
					highlightT = True
				else:
					self.aim.Material.value.set_uniform("Color", avango.gua.Vec4(1, 1, 0, 0.8))

			# if highlightT or highlightR:
			# 	setup_environment.setBackgroundColor(avango.gua.Color(0.5, 0.5, 0.0))
			# if (highlightT and highlightR) or (DISABLEROTATION and hightlightT):
			# 	setup_environment.setBackgroundColor(avango.gua.Color(1, 1, 0.0))
			
			self.aim.Material.EnableBackfaceCulling = False
			self.aim.Material.EnableBackFaceCulling = False
			self.aim.Material.BackfaceCulling = False

		#set logging vars
		if self.startedTests and self.endedTests== False:
			self.setSpeedTranslate()
			self.setSpeedRotate()
			self.frame_counter_speed= self.frame_counter_speed+1
			self.setAccelerationTranslate()
			self.setAccelerationRotate()
			self.frame_counter_acceleration = self.frame_counter_acceleration+1
			self.checkTranslateOvershoots()
			self.checkRotateOvershoots()
			self.checkReversalTranslate()
			self.checkReversalRotate()

		if setup_environment.saveReplay:	
			self.logReplay()

		setup_environment.cam.Transform.connect_from(setup_environment.head_device_sensor.Matrix)

	def select(self):
		if(self.index < len(ID)):
			#auswerten
			if self.getErrorRotate() < W_rot[self.index]/2 and self.getErrorTranslate() < W_trans[self.index]/2:
				#hit
				self.goal= True
				setup_environment.setBackgroundColor(avango.gua.Color(0, 0.2, 0.05), 0.18)
				if DISABLEROTATION:
					setup_environment.playSound("balloon")
				else:
					setup_environment.playSound("hit_rotate")
			else:
				#miss
				self.goal= False
				setup_environment.setBackgroundColor(avango.gua.Color(0.3, 0, 0), 0.18)
				setup_environment.playSound("miss")

	def nextSettingStep(self):
		if(self.counter%N == N-1):
			setup_environment.playSound("levelUp")
			self.index = self.index+1

		if(self.startedTests == False):
			self.lastTime = self.timer.value
			self.startedTests = True
		else:
			self.counter = self.counter+1
		


		if(self.index==len(ID)):
			self.endedTests = True

		#print("P:"+str( pencilRot )+"")
		#print("T:"+str( self.disksMat.value.get_rotate_scale_corrected() )+"")
		if(self.index < len(ID)):
			#move target			
			if setup_environment.randomTargets:
				if not DISABLEROTATION:
					if setup_environment.taskDOFRotate ==3:
						rotation = self.getRandomRotation3D()
						self.disks.setRotation(rotation)
					else:
						rotation = self.getRandomRotation2D()
						self.disks.setRotation(rotation)
			else:

				#switches aim and shadow aim
				temp = self.aimShadow.Transform.value
				self.aimShadow.Transform.value = self.aim.Transform.value 
				self.aim.Transform.value = temp

				self.aim.Transform.value = avango.gua.make_trans_mat(self.aim.Transform.value.get_translate())* avango.gua.make_scale_mat(W_trans[self.index])
				self.aimShadow.Transform.value = avango.gua.make_trans_mat(self.aimShadow.Transform.value.get_translate())* avango.gua.make_scale_mat(W_trans[self.index])	
				
				if not DISABLEROTATION:
					if self.taskNum==0 or self.taskNum==2:
						distance = D_rot
						if setup_environment.taskDOFRotate == 3:
							rotateAroundX = 1
						else:
							rotateAroundX = 0
					else:
						distance = D_rot
						rotateAroundX = 0
						if self.taskNum==3:
							distance = 0

					self.disks.setRotation( avango.gua.make_rot_mat(distance, rotateAroundX, 1, 0) )
					self.taskNum = (self.taskNum+1) % 4

					self.disks.setDisksTransMats(targetDiameter[self.index])
					

			self.setID(self.index)
		else: #trial over
			setup_environment.setBackgroundColor(avango.gua.Color(0,0,1), 1)
		
	def getErrorRotate(self):
		if not DISABLEROTATION:
			return setup_environment.getRotationError1D(
				self.pcNode.Transform.value.get_rotate_scale_corrected(),
				self.disks.getRotate()
			)
		return 0

	def getErrorTranslate(self):
		return setup_environment.getDistance3D(self.pcNode.Transform.value, self.aim.Transform.value)

	def getPath(self):
		path="results/"+taskString+"_"+str(setup_environment.taskDOFRotate)+"DOF/"

		#create dir if not existent
		if not os.path.exists(path):
			os.makedirs(path)

		return path

	def logData(self):
		path = self.getPath()
		
		#fint out which file number
		if self.created_logfile == False: #create File 
			self.num_logfiles = len([f for f in os.listdir(path)
				if os.path.isfile(os.path.join(path, f))])
			self.created_logfile = True

		if(self.startedTests and self.endedTests == False):
			self.logSetter()
			logmanager.writeToFile(path+taskString+"_trial"+str(self.num_logfiles)+".csv")
			self.resetValues()

	def logReplay(self):
		path = self.getPath()

		if(self.endedTests== False):
			if self.created_replayfile == False: #create File 
				self.num_files = len([f for f in os.listdir(path)
					if os.path.isfile(os.path.join(path, f))])
				self.created_replayfile = True
			else: #write permanent values
				self.result_file = open(path+taskString+"_trial"+str(self.num_logfiles)+".replay", "a+")
				
				self.result_file.write(
					"TimeStamp: "+str(self.timer.value)+"\n"+
					"ErrorRotate: "+str(self.getErrorRotate())+"\n"+
					"Pointerpos: \n"+str(self.pcNode.Transform.value)+"\n"+
					"Aimpos: \n"+str(self.aim.Transform.value)+"\n\n")
				self.result_file.close()

	def checkTranslateOvershoots(self):
		if(self.getErrorTranslate() < self.aim.Transform.value.get_scale().x/2):
			self.overshootInside_translate = True
		else:
			if(self.overshootInside_translate):#
				self.overshoots_t = self.overshoots_t+1
				self.overshootInside_translate = False

	def checkRotateOvershoots(self):
		if(self.getErrorRotate() < W_rot[self.index]/2):
			self.overshootInside_rotate = True
		else:
			if(self.overshootInside_rotate):
				self.overshoots_r = self.overshoots_r+1
				self.overshootInside_rotate = False

	def logSetter(self):
		if self.getErrorRotate() < W_rot[self.index]/2 and self.getErrorTranslate() < W_trans[self.index]/2:
			self.goal= True
		else:
			self.goal= False

		if(setup_environment.useAutoDetect):
			hit_type ="Auto"
		else:
			hit_type ="Manual"
			self.clicks = self.clicks+1
			if(self.goal):
				self.succesful_clicks= self.succesful_clicks+1

		self.setMT(self.lastTime, self.timer.value)
		logmanager.set("USER ID", self.userID)
		logmanager.set("USER GROUP", self.group)

		if(setup_environment.space3D):
			logmanager.set("DOF real T", 3)
			logmanager.set("DOF real R", 3)
		else:
			logmanager.set("DOF real T", 2)
			logmanager.set("DOF real R", 1)
		logmanager.set("DOF virtual T", setup_environment.getDOFTranslate())



		logmanager.set("movement direction", self.aim.Transform.value.get_translate()-self.aimShadow.Transform.value.get_translate())

		logmanager.set("target distance T", D_trans)
		logmanager.set("target width T", W_trans[self.index])
		logmanager.set("target distance R", D_rot)
		logmanager.set("target width R", W_rot[self.index])
		logmanager.set("ID combined", self.ID)
		if DISABLEROTATION:
			logmanager.set("ID T", self.ID)
			logmanager.set("ID R", 0)
		else:
			logmanager.set("ID T", self.ID/2)
			logmanager.set("ID R ", self.ID/2)
		logmanager.set("REPETITION", N)
		logmanager.set("TRIAL", self.trial)
		logmanager.set("BUTTON CLICKS", self.clicks)
		logmanager.set("SUCCESSFUL CLICKS", self.succesful_clicks)
		if self.goal:
			logmanager.set("Hit", 1)
		else:
			logmanager.set("Hit", 0)
		logmanager.set("OVERSHOOTS R", self.overshoots_r)
		logmanager.set("OVERSHOOTS T", self.overshoots_t)
		logmanager.set("PEAK ACCELERATION T", self.peak_acceleration_t)
		logmanager.set("PEAK ACCELERATION R", self.peak_acceleration_r)
		if (self.peak_acceleration_r > 0):
			logmanager.set("MOVEMENT CONTINUITY R", self.first_reversal_acceleration_rotate / self.peak_acceleration_r)
		else:
			logmanager.set("MOVEMENT CONTINUITY R", "#DIV0")
		if (self.peak_acceleration_t > 0):
			logmanager.set("MOVEMENT CONTINUITY T", self.first_reversal_acceleration_t / self.peak_acceleration_t)
		else:
			logmanager.set("MOVEMENT CONTINUITY T", "#DIV0")
		logmanager.set("PEAK SPEED R", self.peak_speed_r)
		logmanager.set("PEAK SPEED T", self.peak_speed_t)
		logmanager.set("HIT TYPE", hit_type)
		logmanager.set("MT", self.MT)
		logmanager.set("ERROR R", self.getErrorRotate())
		logmanager.set("ERROR T", self.getErrorTranslate())
		logmanager.set("FIRST REVERSAL R", self.first_reversal_point_r)
		logmanager.set("FIRST REVERSAL T", self.first_reversal_point_t)
		logmanager.set("REVERSAL POINTS R", len(self.reversal_points_r))
		logmanager.set("REVERSAL POINTS T", len(self.reversal_points_t))

		self.trial = self.trial + 1

	def setSpeedRotate(self):
		if(self.frame_counter_speed % 5 == 0):
			self.PencilRotation1= self.pcNode.Transform.value.get_rotate()
			self.start_time = self.timer.value
		else: 
			if(self.frame_counter_speed % 5 == FRAMES_FOR_SPEED-1):
				self.PencilRotation2 = self.pcNode.Transform.value.get_rotate()
				self.end_time = self.timer.value
				div = setup_environment.getRotationError1D(self.PencilRotation1, self.PencilRotation2)
				time = self.end_time-self.start_time
				self.current_speed_rotate = div / time

				if(self.current_speed_rotate < 10**-3):
					self.current_speed_rotate = 0

				if(self.current_speed_rotate > self.peak_speed_r):
					self.peak_speed_r = self.current_speed_rotate

				if(self.current_speed_rotate > self.local_peak_speed_r):
					self.local_peak_speed_r = self.current_speed_rotate

	def setSpeedTranslate(self):
		if(self.frame_counter_speed % 5 == 0):
			self.TransTranslation1 = self.pcNode.Transform.value.get_translate()
			self.start_time = self.timer.value
		else: 
			if(self.frame_counter_speed % 5 == FRAMES_FOR_SPEED-1):
				self.TransTranslation2 = self.pcNode.Transform.value.get_translate()
				self.end_time = self.timer.value
				div = self.TransTranslation2-self.TransTranslation1
				length = math.sqrt(div.x**2 + div.y**2 + div.z**2)
				time = self.end_time-self.start_time
				self.current_speed_translate = length/time

				if(self.current_speed_translate < 10**-3):#noise filter
					self.current_speed_translate = 0

				if(self.current_speed_translate > self.peak_speed_t):
					self.peak_speed_t = self.current_speed_translate
		
	def setAccelerationTranslate(self):
		if(self.frame_counter_acceleration % 5 == 0):
			self.speed_at_start_translate = self.current_speed_translate
			self.start_time_translate = self.timer.value
		else:
			if(self.frame_counter_acceleration % 5 == FRAMES_FOR_SPEED-1):
				
				div = self.current_speed_translate - self.speed_at_start_translate
				time = self.timer.value - self.start_time_translate
				
				self.current_acceleration_translate = div/time

				if(self.current_acceleration_translate > self.peak_acceleration_t):
					self.peak_acceleration_t = self.current_acceleration_translate

	def setAccelerationRotate(self):
		if(self.frame_counter_acceleration % 5 == 0):
			self.speed_at_start_rotate = self.current_speed_rotate
			self.start_time_rotate = self.timer.value
		else:
			if(self.frame_counter_acceleration % 5 == FRAMES_FOR_SPEED-1):
				div = self.current_speed_rotate - self.speed_at_start_rotate
				time = self.timer.value - self.start_time_rotate
				self.current_acceleration_rotate = div/time
				
				#noise filter
				if(math.fabs(self.current_acceleration_rotate) < 1):
					self.current_acceleration_rotate = 0

				if(self.current_acceleration_rotate > self.peak_acceleration_r):
					self.peak_acceleration_r = self.current_acceleration_rotate

	def checkReversalTranslate(self):
		if(math.fabs(self.current_speed_translate) < THRESHHOLD_TRANSLATE and self.peak_speed_t>THRESHHOLD_TRANSLATE):
			if(self.low_speed_counter_translate < FRAMES_FOR_AUTODETECT_TRANSLATE-1):
				self.low_speed_counter_translate = self.low_speed_counter_translate+1
			else:
				self.low_speed_counter_translate = 0
				if(self.first_translate):
					self.first_reversal_point_t = self.pcNode.Transform.value.get_translate().x
					self.first_reversal_acceleration_t = self.current_acceleration_translate
					self.first_translate = False
				self.reversal_points_t.append(self.pcNode.Transform.value.get_translate().x)

	def checkReversalRotate(self):
		if(math.fabs(self.current_speed_rotate) < THRESHHOLD_ROTATE and self.peak_speed_r > THRESHHOLD_ROTATE):
			if(self.low_speed_counter_rotate < FRAMES_FOR_AUTODETECT_ROTATE-1):
				self.low_speed_counter_rotate = self.low_speed_counter_rotate+1
			else:
				self.low_speed_counter_rotate = 0
				if(self.first_rotate):
					self.first_reversal_point_r = self.pcNode.Transform.value.get_rotate().get_angle()
					self.first_reversal_acceleration_rotate = self.current_acceleration_rotate
					self.reversal_points_r.append(self.first_reversal_point_r)
					self.first_rotate = False

				if(self.local_peak_speed_r > THRESHHOLD_ROTATE):
					self.speededup= True
					self.local_peak_speed_r = 0
				
				if(self.speededup):
					self.reversal_points_r.append(self.pcNode.Transform.value.get_rotate().get_angle())
					self.speededup= False

	def resetValues(self):
		self.overshoots_t = 0
		self.overshoots_r = 0
		self.peak_speed_t = 0
		self.peak_acceleration_t = 0
		self.peak_speed_r = 0
		self.peak_acceleration_r = 0
		self.reversal_points_t = []
		self.reversal_points_r = []
		self.first_translate = True
		self.first_rotate = True

	def setID(self, index):
		if(index<len(ID)):
			self.ID = ID[index]

	def setMT(self, start, end):
		self.MT=end-start
		self.lastTime = self.timer.value

	def setTP(self, index):
		if(self.MT>0 and self.current_index<len(ID)):
			self.TP=ID[index]/self.MT

	def handle_key(self, key, scancode, action, mods):
		if action == 1:
			#32 is space 335 is num_enter
			if key==32 or key==335:
				if(self.endedTests== False):
					self.Button.value = True
				else:
					print("Test ended")


def start():
	trackManager = trackingManager()
	trackManager.userID = input("USER ID: ")
	trackManager.group = input("GROUP: ")

	setup_environment.getWindow().on_key_press(trackManager.handle_key)
	setup_environment.setup(graph)

	trackManager.aim = loader.create_geometry_from_file("pointer_object_abstract", "data/objects/modified_sphere.obj", avango.gua.LoaderFlags.NORMALIZE_SCALE)
	trackManager.aim.Transform.value = avango.gua.make_trans_mat(-D_trans/2, 0, 0)*avango.gua.make_scale_mat(W_trans[0])
	trackManager.aim.Material.value.set_uniform("Color", avango.gua.Vec4(0, 1, 0, 0.8))
	trackManager.aim.Material.value.EnableBackfaceCulling.value = False
	setup_environment.everyObject.Children.value.append(trackManager.aim)

	trackManager.aimShadow = loader.create_geometry_from_file("pointer_object_abstract", "data/objects/modified_sphere.obj", avango.gua.LoaderFlags.NORMALIZE_SCALE)
	trackManager.aimShadow.Transform.value = avango.gua.make_trans_mat(D_trans/2, 0, 0)*avango.gua.make_scale_mat(W_trans[0])
	trackManager.aimShadow.Material.value.set_uniform("Color", avango.gua.Vec4(0.5, 0.5, 0.5, 0.1))
	trackManager.aimShadow.Material.value.EnableBackfaceCulling.value = False
	setup_environment.everyObject.Children.value.append(trackManager.aimShadow)

	#loadMeshes
	PContainer = setupEnvironment.PencilContainer().create(setup_environment)
	trackManager.pcNode = PContainer.getNode()
	trackManager.PContainer = PContainer

	if (not DISABLEROTATION):
		trackManager.disks.setupDisks(trackManager.pcNode)
		trackManager.disks.setDisksTransMats(targetDiameter[0])

	#listen to button
	button_sensor = avango.daemon.nodes.DeviceSensor(DeviceService = avango.daemon.DeviceService())
	button_sensor.Station.value ="device-pointer"
	trackManager.Button.connect_from(button_sensor.Button0)

	#timer
	timer = avango.nodes.TimeSensor()
	trackManager.timer.connect_from(timer.Time)

	setup_environment.launch(globals())


if __name__ == '__main__':
  start()