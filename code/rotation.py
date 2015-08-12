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

FRAMES_FOR_SPEED=4
FRAMES_FOR_AUTODETECT=3
THRESHHOLD=40

r = setupEnvironment.r
rotation2D=[avango.gua.make_rot_mat(20, 1, 0.8, 0),
			avango.gua.make_rot_mat(90, 0.1, 0.2, 0)]

rotation3D=[avango.gua.make_rot_mat(20, 1, 0.8, 0.3),
			avango.gua.make_rot_mat(90, 0.1, 0.2, 0.9)]

N=5 #number of tests per ID
ID=[4, 5, 6] #fitt's law

W=[]

for i in range(0, len(ID)):
	if setupEnvironment.randomTargets:
		D=[ setupEnvironment.getRotationError1D(rotation2D[0].get_rotate(), rotation2D[1].get_rotate()) ] #in degrees
		W=[D[0]/(2**ID[0]-1), D[0]/(2**ID[1]-1), D[0]/(2**ID[2]-1)] #in degrees, Fitt's Law umgeformt nach W
	else:
		D=100
		W.append(D/(2**ID[i]-1))

targetDiameter = [
	2*r*math.tan(W[0]/2*math.pi/180),
	2*r*math.tan(W[1]/2*math.pi/180),
	2*r*math.tan(W[2]/2*math.pi/180)
]#größe (Druchmesser) der Gegenkathete auf dem kreisumfang

# print(targetDiameter)

graph = avango.gua.nodes.SceneGraph(Name="scenegraph") #Create Graph
pencil_transform = avango.gua.nodes.TransformNode()

logmanager=logManager.logManager()

class trackingManager(avango.script.Script):
	Button = avango.SFBool()
	timer = avango.SFFloat()
	
	PencilRotation1=None
	PencilRotation2=None

	lastTime=0

	startedTests = False
	endedTests = False

	created_logfile = False
	created_replayfile = False
	flagPrinted = False

	index=0
	counter=0

	frame_counter=0
	frame_counter2=0
	start_time1=0
	start_time2=0
	end_time2=0
	end_time1=0

	current_speed=0
	current_acceleration=0
	peak_acceleration=0
	peak_speed=0
	speed_time1=0
	speed_time2=0
	first=False
	reversal_points=[]
	first_reversal_acceleration=0
	first_reversal_point=0
	low_speed_counter=0
	speededup=True
	local_peak_speed=0

	#Logging
	userID=0
	group=0
	trial=0
	succesful_clicks=0
	MT=0
	ID=0
	TP=0
	overshoots=0

	overshootInside=False
	goal=False

	def __init__(self):
		self.super(trackingManager).__init__()
		self.isInside = False;
		self.startTime = 0
		self.endTime = 0
		self.backAndForth = False
		self.backAndForthAgain = False;
		self.disks = setupEnvironment.DisksContainer()
		self.pcNode = None

	def __del__(self):
		if setupEnvironment.logResults:
			self.result_file.close()

	@field_has_changed(Button)
	def button_pressed(self):
		if self.Button.value==True:
			if(self.endedTests==False):
				self.startedTests=True
				self.select()
				if setupEnvironment.logResults:	
					self.logData()				

				self.nextSettingStep()
			else:
				print("Tests ended")
		else:
			self.flagPrinted = False


	@field_has_changed(timer)
	def updateTimer(self):
		#attach disks to pointer
		self.disks.setTranslate(
			avango.gua.make_trans_mat( self.pcNode.Transform.value.get_translate() )
		)
		if self.endedTests==False:
			self.setSpeed()
			self.setAcceleration()
			self.setOvershoots()
			self.autoDetect()

		if setupEnvironment.saveReplay:	
			self.logReplay()#save replay, todo

	def nextSettingStep(self):
		# print(self.index)
		if(self.counter%N == N-1):
			self.index=self.index+1

		if(self.index==len(W)):
			self.endedTests=True

		#print("P:"+str( pencilRot )+"")
		#print("T:"+str( self.disksMat.value.get_rotate_scale_corrected() )+"")
		if(self.index < len(W)):

			#move target			
			if setupEnvironment.randomTargets:#select from random targets?
				if setupEnvironment.taskDOFRotate==3:
					self.disks.setRotation(self.getRandomRotation3D())
				else:
					self.disks.setRotation(self.getRandomRotation2D())

			else:
				if self.backAndForth: #aim get right
					distance=0
					rotateAroundX=0;
					self.backAndForth=False
				else:
					distance=D
					rotateAroundX=0
					if self.backAndForthAgain:
						self.backAndForthAgain = False
						if setupEnvironment.taskDOFRotate==3:
							rotateAroundX = 1
						else:
							rotateAroundX = 0
					else:
						self.backAndForthAgain = True 
					self.backAndForth=True

				self.disks.setRotation(avango.gua.make_rot_mat(distance, rotateAroundX, 1, 0))
			
				self.disks.setDisksTransMats(targetDiameter[self.index])

			
			self.counter=self.counter+1

			self.setID(self.index)
		else: #trial over
			setupEnvironment.setBackgroundColor(avango.gua.Color(0,0,1), 1)

	def select(self):
		if self.getErrorRotate() < W[self.index]/2:
			# print("HIT:" + str(self.getErrorRotate())+"°")
			self.goal=True
			setupEnvironment.setBackgroundColor(avango.gua.Color(0, 0.2, 0.05), 0.18)
			if(setupEnvironment.useAutoDetect==False):
				self.succesful_clicks=self.succesful_clicks+1
		else:
			# print("MISS:" + str(self.getErrorRotate())+"°")
			self.goal=False
			setupEnvironment.setBackgroundColor(avango.gua.Color(0.3, 0, 0), 0.18)


	def getErrorRotate(self):
		return setupEnvironment.getRotationError1D(
			self.pcNode.Transform.value.get_rotate_scale_corrected(),
			self.disks.getRotate()
		)

	def autoDetect(self):
		if(math.fabs(self.current_speed) < THRESHHOLD and self.peak_speed>THRESHHOLD):
			if(self.low_speed_counter < FRAMES_FOR_AUTODETECT-1):
				self.low_speed_counter=self.low_speed_counter+1
			else:
				self.low_speed_counter=0
				if(self.first):
					self.first_reversal_point=self.pcNode.Transform.value.get_rotate().get_angle()
					# print(self.first_reversal_point)
					self.first_reversal_acceleration=self.current_acceleration
					self.first=False

				# print(self.local_peak_speed)
				if(self.local_peak_speed>THRESHHOLD):
					self.speededup=True
					self.local_peak_speed=0
				
				if(self.speededup):
					print("reversal")
					self.reversal_points.append(self.pcNode.Transform.value.get_rotate().get_angle())
					self.speededup=False


	def setSpeed(self):
		if(self.frame_counter % 5 == 0):
			self.PencilRotation1=self.pcNode.Transform.value.get_rotate()
			self.start_time=self.timer.value
		else: 
			if(self.frame_counter % 5 == FRAMES_FOR_SPEED-1):
				self.PencilRotation2=self.pcNode.Transform.value.get_rotate()
				div=setupEnvironment.getRotationError1D(self.PencilRotation1, self.PencilRotation2)

				time=self.timer.value - self.start_time
				self.current_speed=div/time

				if(self.current_speed<10**-3):
					self.current_speed=0

				if(self.current_speed>self.peak_speed):
					self.peak_speed=self.current_speed
				
				if(self.current_speed>self.local_peak_speed):
					self.local_peak_speed=self.current_speed
			
				# print(self.current_speed)
				# print(self.peak_speed)
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
		if(self.getErrorRotate() < W[self.index]/2):
			self.overshootInside = True
		else:
			if(self.overshootInside):
				self.overshoots=self.overshoots+1
				self.overshootInside=False


	def resetValues(self):
		self.overshoots=0
		self.peak_acceleration=0
		self.first_reversal_acceleration=0
		self.peak_speed=0
		self.first=True
		self.overshootInside=False
		self.goal=False
		self.reversal_points=[]

	def getRandomRotation3D(self):
		settings=[avango.gua.make_rot_mat(20, 1, 0.8, 0.3),
			avango.gua.make_rot_mat(90, 0.1, 0.2, 0.9)]

		index=random.randint(0, len(settings)-1)

		return settings[index]

	def getRandomRotation2D(self):
		settings=[avango.gua.make_rot_mat(20, 1, 0.8, 0),
			avango.gua.make_rot_mat(90, 0.1, 0.2, 0)]

		index=random.randint(0, len(settings)-1)

		return settings[index]
	
	def getPath(self):
		path="results/rotation_"+str(setupEnvironment.taskDOFRotate)+"DOF/"

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

		if(self.startedTests and self.endedTests== False):
			self.logSetter()
			logmanager.writeToFile(path+"rotation_trial"+str(self.num_logfiles)+".csv")
			self.resetValues()

	def logReplay(self):
		if setupEnvironment.taskDOFRotate==3:
			path="results/results_rotation_3D/"
		else:
			path="results/results_rotation_2D/"
		if(self.endedTests==False):
			if self.created_file==False: #create File 
				self.num_files=len([f for f in os.listdir(path)
					if os.path.isfile(os.path.join(path, f))])
				self.created_file=True
			else: #write permanent values
				self.result_file=open(path+"rotation2D_trial"+str(self.num_files)+".replay", "a+")
				
				# self.result_file.write(
				# 	"TimeStamp: "+str(self.timer.value)+"\n"+
				# 	"Error: "+str(self.getErrorRotate())+"\n"+
				# 	"Pointerpos: \n"+str(self.pcNode.Transform.value)+"\n"+
				# 	"Aimpos: \n"+str(self.disks.Transform.value)+"\n\n")
				self.result_file.close()	 

	def logSetter(self):
		self.setID(self.index)
		self.setMT(self.lastTime, self.timer.value)
		self.setTP(self.index)

		if self.getErrorRotate() < W[self.index]/2:
			self.goal= True
		else:
			self.goal= False

		if(setupEnvironment.useAutoDetect):
			hit_type ="Auto"
		else:
			hit_type ="Manual"
			#self.clicks = self.clicks+1
			if(self.goal):
				self.succesful_clicks= self.succesful_clicks+1

		logmanager.set("USER_ID", self.userID)
		logmanager.set("GROUP", self.group)
		if setupEnvironment.space3D:
			logmanager.set("DOF_REAL_ROTATE", 3)
		else:
			logmanager.set("DOF_REAL_ROTATE", 1)

		logmanager.set("DOF_VIRTUAL_ROTATE", setupEnvironment.virtualDOFRotate)

		if self.backAndForth:
			logmanager.set("MOVEMENT_DIRECTION","r")
		else:
			logmanager.set("MOVEMENT_DIRECTION","l")

		logmanager.set("ROTATION_AXIS","y")
		logmanager.set("TARGET_DISTANCE_ROTATE",D)
		logmanager.set("TARGET_WIDTH_ROTATE",W[self.index])
		logmanager.set("ID_COMBINED", self.ID)
		logmanager.set("REPETITION",N)
		logmanager.set("TRIAL", self.trial)
		if(setupEnvironment.useAutoDetect==False):
			logmanager.set("CLICKS", self.trial)
			logmanager.set("SUCCESSFUL_CLICKS", self.succesful_clicks)
		logmanager.set("SUCCESS",self.goal)
		logmanager.set("HIT_TYPE", hit_type)
		logmanager.set("MOVEMENT_TIME", self.MT)
		logmanager.set("ERROR_ROTATE", self.getErrorRotate())

		logmanager.set("OVERSHOOTS_ROTATE",self.overshoots)
		logmanager.set("PEAK_SPEED_ROTATE", self.peak_speed)
		if(self.peak_acceleration > 0):
			logmanager.set("MOVEMENT_CONTINUITY_ROTATE", self.first_reversal_acceleration/self.peak_acceleration)
		else:
			logmanager.set("MOVEMENT_CONTINUITY_ROTATE", "#DIV0")
		logmanager.set("FIRST_REVERSAL_POINT", self.first_reversal_point)
		logmanager.set("REVERSAL_POINTS", len(self.reversal_points))

		self.trial=self.trial+1

	def setID(self, index):
		if(index<len(ID)):
			self.ID = ID[index]
		# print("ID: "+ str(self.ID))

	def setMT(self, start, end):
		self.MT=end-start
		self.lastTime=self.timer.value
		# print("Time: " + str(self.MT))

	def setTP(self, index):
		if(self.MT>0 and self.index<len(ID)):
			self.TP=ID[index]/self.MT

	def handle_key(self, key, scancode, action, mods):
		if action == 1:
			#32 is space 335 is num_enter
			if key==32 or key==335:
				if(self.endedTests==False):
					#trackManager.nextSettingStep()
					self.Button.value=True
				else:
					print("Test ended")
		else:
			self.flagPrinted=False


def start():
	trackManager = trackingManager()
	trackManager.userID=input("USER_ID: ")
	trackManager.group=input("GROUP: ")

	setupEnvironment.getWindow().on_key_press(trackManager.handle_key)
	setupEnvironment.setup(graph)

	#loadMeshes
	trackManager.pcNode = setupEnvironment.PencilContainer().getNode()

	trackManager.disks.setupDisks(trackManager.pcNode)
	trackManager.disks.setDisksTransMats(targetDiameter[0])

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