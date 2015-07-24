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

THREEDIMENSIONTASK=False

DISABLEROTATION=True


r=setupEnvironment.r #circle radius

#fitt's law parameter
D_rot=45 #in degrees
D_trans=0.2 #in meter
ID=[4, 5, 6] #fitt's law
N=5 #number of tests per ID
W_rot=[]
W_trans=[]
targetDiameter=[]
for i in range(0, len(ID)):
	W_rot.append(D_rot/(2**(ID[i]/2)-1)) #in degrees, Fitt's Law umgeformt nach W
	W_trans.append(D_trans/(2**(ID[i]/2)-1)) #in degrees, Fitt's Law umgeformt nach W
	targetDiameter.append(2*r*math.tan(W_rot[i]/2*math.pi/180))#größe (Druchmesser) der Gegenkathete auf dem kreisumfang

FRAMES_FOR_SPEED=4 #How many frames token to calculate speed and acceleration


graph = avango.gua.nodes.SceneGraph(Name="scenegraph") #Create Graph
loader = avango.gua.nodes.TriMeshLoader() #Create Loader
pencil_transform = avango.gua.nodes.TransformNode()

logmanager=logManager.logManager()

class trackingManager(avango.script.Script):
	Button = avango.SFBool()
	timer = avango.SFFloat()
	
	time2=0

	startedTests = False
	endedTests = False

	created_file =  False
	flagPrinted = False

	current_index=0
	counter=0

	#Logging
	userID=0
	group=0
	trial=0
	clicks=0

	MT=0
	ID=0
	TP=0
	overshootsRotate=0
	overshootsTranslate=0
	overshootInside_translate = False;
	overshootInside_rotate = False;

	frame_counter_speed = 0
	frame_counter_acceleration = 0

	low_speed_counter = 0

	goal=False

	peak_speed_translate = 0
	peak_speed_rotate = 0

	current_speed_translate = 0
	current_speed_rotate = 0
	current_acceleration_translate = 0
	current_acceleration_rotate = 0
	peak_acceleration_translate=0
	peak_acceleration_rotate=0
	first_reversal_acceleration_translate=0
	first_reversal_acceleration_rotate=0
	first_reversal_point_translate=0
	first_reversal_point_rotate=0
	reversal_points=[]

	succesful_clicks=0

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
		self.isInside = False;
		self.startTime = 0
		self.backAndForth = False
		self.backAndForthAgain = False;
		self.disks = setupEnvironment.DisksContainer()
		self.aim = None
		self.aimShadow = None
		self.index = 0
		self.pcNode = None

	def __del__(self):
		if setupEnvironment.logResults:
			pass # self.result_file.close()

	@field_has_changed(Button)
	def button_pressed(self):
		if self.Button.value==True:
			if(self.endedTests==False):
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
		if (not DISABLEROTATION):
			if (not self.endedTests and setupEnvironment.getDistance3D(self.pcNode.Transform.value, self.aim.Transform.value) <= W_trans[self.index]) :
				#attach disks to pointer
				self.disks.setTranslate( avango.gua.make_trans_mat(self.pcNode.Transform.value.get_translate()) )
			else:
				#attach disks to aim
				self.disks.setTranslate( avango.gua.make_trans_mat(self.aim.Transform.value.get_translate()) )

		if(self.startedTests and self.endedTests==False):
			self.setSpeedTranslate()
			self.setSpeedRotate()
			self.frame_counter_speed=self.frame_counter_speed+1
			self.setAccelerationTranslate()
			self.setAccelerationRotate()
			self.frame_counter_acceleration = self.frame_counter_acceleration+1
			#self.setError()
			self.checkTranslateOvershoots()
			self.checkRotateovershoots()
			#self.autoDetect()

		if setupEnvironment.logResults:	
			self.logReplay()

	def select(self):
		if(self.index < len(W_rot)):
			#auswerten
			if self.getErrorRotate() < W_rot[self.index]/2 and self.getErrorTranslate() < W_trans[self.index]/2:
				print("HIT: Rot: " + str(self.getErrorRotate())+"° "+ "Trans: "+ str(self.getErrorTranslate()))
				self.goal=True
				setupEnvironment.setBackgroundColor(avango.gua.Color(0, 0.2, 0.05), 0.18)
			else:
				print("MISS: Rot: " + str(self.getErrorRotate())+"° "+ "Trans: "+ str(self.getErrorTranslate()))
				self.goal=False
				setupEnvironment.setBackgroundColor(avango.gua.Color(0.3, 0, 0), 0.18)


	def nextSettingStep(self):
		if(self.startedTests==False):
			self.lastTime=self.timer.value
		self.startedTests=True
		print(self.index)
		if(self.counter%N == N-1):
			self.index=self.index+1

		if(self.index==len(W_rot)):
			self.endedTests=True

		#print("P:"+str( pencilRot )+"")
		#print("T:"+str( self.disksMat.value.get_rotate_scale_corrected() )+"")
		if(self.index < len(W_rot)):
			#move target			
			if setupEnvironment.randomTargets:
				if (not DISABLEROTATION):
					if THREEDIMENSIONTASK:
						rotation=self.getRandomRotation3D()
						self.disks.setRotation(rotation)
					else:
						rotation=self.getRandomRotation2D()
						self.disks.setRotation(rotation)
			else:

				#switches aim and shadow aim
				temp = self.aimShadow.Transform.value
				self.aimShadow.Transform.value = self.aim.Transform.value 
				self.aim.Transform.value = temp

				self.aim.Transform.value = avango.gua.make_trans_mat(self.aim.Transform.value.get_translate())* avango.gua.make_scale_mat(W_trans[self.index])
				self.aimShadow.Transform.value = avango.gua.make_trans_mat(self.aimShadow.Transform.value.get_translate())* avango.gua.make_scale_mat(W_trans[self.index])	
				
				if (not DISABLEROTATION):
					if self.backAndForth: #aim get right
						distance = 0
						rotateAroundX = 0
						self.backAndForth=False
					else:
						distance = D_rot
						self.backAndForth=True
						rotateAroundX=0
						if not self.backAndForthAgain:
							self.backAndForthAgain=True
							if THREEDIMENSIONTASK:
								rotateAroundX=1
							else:
								rotateAroundX=0

					self.disks.setRotation( avango.gua.make_rot_mat(distance, rotateAroundX, 1, 0) )
				
					self.disks.setDisksTransMats(targetDiameter[self.index])

			
			self.counter=self.counter+1

			self.setID(self.index)
		else: #trial over
			setupEnvironment.setBackgroundColor(avango.gua.Color(0,0,1), 1)
		
	def getErrorRotate(self):
		if (not DISABLEROTATION):
			return setupEnvironment.getRotationError1D(
				self.pcNode.Transform.value.get_rotate_scale_corrected(),
				self.disks.getRotate()
			)
		return 0

	def getErrorTranslate(self):
		return setupEnvironment.getDistance3D(self.pcNode.Transform.value, self.aim.Transform.value)

	def logData(self):
		if THREEDIMENSIONTASK==False:
			path="results/results_docking_2D/"
		else:
			path="results/results_docking_3D/"

		if not os.path.exists(path):
			os.makedirs(path)

		if(self.startedTests and self.endedTests==False):
			self.result_file=open(path+"docking_trial"+str(self.num_files)+".log", "a+")
			if(self.flagPrinted==False):
				self.logSetter()
				logmanager.log(self.result_file)
				self.resetValues()
				self.flagPrinted=True
			self.result_file.close()

	def logReplay(self):
		if THREEDIMENSIONTASK==False:
			path="results/results_docking_2D/"
		else:
			path="results/results_docking_3D/"

		if not os.path.exists(path):
			os.makedirs(path)

		if(self.endedTests==False):
			if self.created_file==False: #create File 
				self.num_files=len([f for f in os.listdir(path)
					if os.path.isfile(os.path.join(path, f))])
				self.created_file=True
			else: #write permanent values
				self.result_file=open(path+"docking_trial"+str(self.num_files)+".replay", "a+")
				
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
			if(self.overshootInside_translate):
				self.overshoots = self.overshootsTranslate+1
				self.overshootInside_translate = False

	def checkRotateovershoots(self):
		if(self.getErrorRotate() < W_rot[self.index]/2):
			self.overshootInside_rotate = True
		else:
			if(self.overshootInside_rotate):
				self.overshootsTranslate = self.overshootsRotate+1
				self.overshootInside_rotate = False


	def logSetter(self):
		if self.getErrorRotate() < W_rot[self.index]/2 and self.getErrorTranslate() < W_trans[self.index]/2:
			self.goal=True
		else:
			self.goal=False

		if(setupEnvironment.useAutoDetect):
			hit_type="Auto"
		else:
			hit_type="Manual"
			self.clicks=self.clicks+1
			if(self.goal):
				self.succesful_clicks=self.succesful_clicks+1

		self.setMT(self.lastTime, self.timer.value)
		logmanager.setUserID(self.userID)
		logmanager.setGroup(self.group)

		if(setupEnvironment.space3D):
			# if(setupEnvironment.reduceDOFTranslate and setupEnvironment.reduceDOFRotate):
			# 	logmanager.setCondition("docking2D_air_locked_virtual")
			# else:
			# 	logmanager.setCondition("docking2D_air_free_virtual")
			logmanager.setDOFReal(3, 3)
		else:
			logmanager.setCondition("docking2D_table_locked_virtual")
			logmanager.setDOFReal(2, 1)
		logmanager.setDOFVirtual(setupEnvironment.getDOFTranslate(), setupEnvironment.virtualDOFRotate)	

		if self.backAndForth:
			logmanager.setMovementDirection("r")
		else:
			logmanager.setMovementDirection("l")

		logmanager.setTargetDistance_t(D_trans)
		logmanager.setTargetWidth_t(W_trans[self.index])
		logmanager.setTargetDistance_r(D_rot)
		logmanager.setTargetWidth_r(W_rot[self.index])
		logmanager.setID_combined(self.ID/2, self.ID/2)
		logmanager.setRepetition(N)
		logmanager.setTrial(self.trial)
		logmanager.setClicks(self.clicks, self.succesful_clicks)
		logmanager.setSuccess(self.goal)
		logmanager.setOvershootCountRotate( self.overshootsRotate )
		logmanager.setOvershootCoutTranslate( self.overshootsTranslate )
		logmanager.setHit(hit_type, self.MT, self.getErrorTranslate(), self.getErrorRotate())
		logmanager.setPeakSpeedTranslate(self.peak_speed_translate)
		logmanager.setPeakSpeedRotate(self.peak_speed_rotate)
		logmanager.setTranslateContinuity(self.peak_acceleration_translate, self.first_reversal_acceleration_translate)
		logmanager.setRotateContinuity(self.peak_acceleration_rotate, self.first_reversal_acceleration_rotate)

		self.trial = self.trial+1

	def setSpeedRotate(self):
		if(self.frame_counter_speed % 5 == 0):
			# self.PencilRotation1=setupEnvironment.get_euler_angles(self.pencilTransMat.value.get_rotate())
			self.PencilRotation1=self.pcNode.Transform.value.get_rotate()
			self.start_time=self.timer.value
		else: 
			if(self.frame_counter_speed % 5 == FRAMES_FOR_SPEED-1):
				# self.PencilRotation2=setupEnvironment.get_euler_angles(self.pencilTransMat.value.get_rotate())
				self.PencilRotation2=self.pcNode.Transform.value.get_rotate()
				self.end_time=self.timer.value
				# div=math.fabs(self.PencilRotation2[0]-self.PencilRotation1[0])+math.fabs(self.PencilRotation2[1]-self.PencilRotation1[1])+ math.fabs(self.PencilRotation2[2]-self.PencilRotation1[2])
				div=setupEnvironment.getRotationError1D(self.PencilRotation1, self.PencilRotation2)
				time=self.end_time-self.start_time
				self.current_speed_rotate = div / time

				if(self.current_speed_rotate < 10**-3):
					self.current_speed=0

				if(self.current_speed_rotate > self.peak_speed_rotate):
					self.peak_speed_rotate =self.current_speed
			
				# print(self.current_speed)
				# print(self.peak_speed)

	def setSpeedTranslate(self):
		if(self.frame_counter_speed % 5 == 0):
			self.TransTranslation1 = self.pcNode.Transform.value.get_translate()
			self.start_time = self.timer.value
		else: 
			if(self.frame_counter_speed % 5 == FRAMES_FOR_SPEED-1):
				self.TransTranslation2 = self.pcNode.Transform.value.get_translate()
				self.end_time=self.timer.value
				div = self.TransTranslation2-self.TransTranslation1
				length = math.sqrt(div.x**2 + div.y**2 + div.z**2)
				time = self.end_time-self.start_time
				self.current_speed_translate = length/time

				if(self.current_speed_translate < 10**-3):#noise filter
					self.current_speed_translate =0

				if(self.current_speed_translate > self.peak_speed_translate):
					self.peak_speed_translate = self.current_speed_translate
		
	def setAccelerationTranslate(self):
		if(self.frame_counter_acceleration % 5 == 0):
			self.speed_time1=self.current_speed_translate
			self.start_time2=self.timer.value
		else:
			if(self.frame_counter_acceleration % 5 == FRAMES_FOR_SPEED-1):
				self.speed_time2 = self.current_speed_translate
				self.end_time2 = self.timer.value
				div = self.speed_time2-self.speed_time1
				time = self.end_time2-self.start_time2
				self.current_acceleration_translate = div/time

				if(self.current_acceleration_translate > self.peak_acceleration_translate):
					self.peak_acceleration_translate = self.current_acceleration_translate

	def setAccelerationRotate(self):
		if(self.frame_counter_acceleration % 5 == 0):
			self.speed_time1=self.current_speed_rotate
			self.start_time2=self.timer.value
		else:
			if(self.frame_counter_acceleration % 5 == FRAMES_FOR_SPEED-1):
				self.speed_time2=self.current_speed_rotate
				self.end_time2 = self.timer.value
				div = self.speed_time2 - self.speed_time1
				time = self.end_time2-self.start_time2
				self.current_acceleration_rotate = div/time

				if(self.current_acceleration_rotate > self.peak_acceleration_rotate):
					self.peak_acceleration_rotate = self.current_acceleration_rotate

	def resetValues(self):
		self.overshootsTranslate=0
		pass

	def setID(self, index):
		if(index<len(ID)):
			self.ID = ID[index]
		print("ID: "+ str(self.ID))

	def setMT(self, start, end):
		self.MT=end-start
		self.lastTime=self.timer.value
		print("Time: " + str(self.MT))

	def setTP(self, index):
		if(self.MT>0 and self.current_index<len(ID)):
			self.TP=ID[index]/self.MT

	def handle_key(self, key, scancode, action, mods):
		if action == 1:
			#32 is space 335 is num_enter
			if key==32 or key==335:
				if(self.endedTests==False):
					self.Button.value=True
				else:
					print("Test ended")
		else:
			self.flagPrinted=False


def start ():
	trackManager = trackingManager()
	trackManager.userID=input("USER_ID: ")
	trackManager.group=input("GROUP: ")

	setupEnvironment.getWindow().on_key_press(trackManager.handle_key)
	setupEnvironment.setup(graph)

	aimBalloon = loader.create_geometry_from_file("pointer_object_abstract", "data/objects/sphere_new.obj", avango.gua.LoaderFlags.NORMALIZE_SCALE)
	aimBalloon.Transform.value = avango.gua.make_trans_mat(-D_trans/2, 0, 0)*avango.gua.make_scale_mat(W_trans[0])
	aimBalloon.Material.value.set_uniform("Color", avango.gua.Vec4(1, 1, 0, 1))
	setupEnvironment.everyObject.Children.value.append(aimBalloon)

	aimShadow  = loader.create_geometry_from_file("pointer_object_abstract", "data/objects/sphere_new.obj", avango.gua.LoaderFlags.NORMALIZE_SCALE)
	aimShadow.Transform.value = avango.gua.make_trans_mat(D_trans/2, 0, 0)*avango.gua.make_scale_mat(W_trans[0])
	aimShadow.Material.value.set_uniform("Color", avango.gua.Vec4(0.5, 0.5, 0.5, 0.1))
	setupEnvironment.everyObject.Children.value.append(aimShadow)

	trackManager.aim = aimBalloon;
	trackManager.aimShadow = aimShadow

	#loadMeshes
	trackManager.pcNode = setupEnvironment.PencilContainer().getNode()

	if (not DISABLEROTATION):
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