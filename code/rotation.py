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
		D=90
		W.append(D/(2**ID[i]-1))

targetDiameter = [
	2*r*math.tan(W[0]/2*math.pi/180),
	2*r*math.tan(W[1]/2*math.pi/180),
	2*r*math.tan(W[2]/2*math.pi/180)
]#größe (Druchmesser) der Gegenkathete auf dem kreisumfang

print(targetDiameter)

graph = avango.gua.nodes.SceneGraph(Name="scenegraph") #Create Graph
pencil_transform = avango.gua.nodes.TransformNode()

logmanager=logManager.logManager()

class trackingManager(avango.script.Script):
	Button = avango.SFBool()
	pencilTransMat = avango.gua.SFMatrix4()
	disksMat = avango.gua.SFMatrix4()
	timer = avango.SFFloat()
	
	lastTime=0
	time2=0

	startedTest = False
	endedTest = False

	created_file =  False
	flagPrinted = False

	index=0
	counter=0

	error=0

	#Logging
	userID=0
	group=0
	trial=0
	succesful_clicks=0
	MT=0
	ID=0
	TP=0

	goal=False

	def __init__(self):
		self.super(trackingManager).__init__()
		self.isInside = False;
		self.startTime = 0
		self.endTime = 0
		self.backAndForth = False
		self.backAndForthAgain = False;
		self.disks = setupEnvironment.DisksContainer()

	def __del__(self):
		if setupEnvironment.logResults:
			self.result_file.close()

	@field_has_changed(Button)
	def button_pressed(self):
		if self.Button.value==True:
			if(self.endedTest==False):
				self.nextSettingStep()
			else:
				print("Test ended")
		else:
			self.flagPrinted = False

	@field_has_changed(pencilTransMat)
	def pointermat_changed(self):
		if (not self.endedTest):
			#attach disks to pointer
			self.disksMat.value = avango.gua.make_trans_mat(self.pencilTransMat.value.get_translate())*avango.gua.make_rot_mat(self.disksMat.value.get_rotate_scale_corrected())*avango.gua.make_scale_mat(self.disksMat.value.get_scale()) #keep rotation and scale and move to pointer
			

	@field_has_changed(timer)
	def updateTimer(self):
		self.pencilTransMat.value = setupEnvironment.reducePencilMat(self.pencilTransMat.value)
		
		if setupEnvironment.logResults:	
			self.logData()
	

	def nextSettingStep(self):
		self.startedTest=True
		print(self.index)
		if(self.counter%N == N-1):
			self.index=self.index+1

		if(self.index==len(W)):
			self.endedTest=True

		self.error = setupEnvironment.getRotationError1D(
			self.pencilTransMat.value.get_rotate_scale_corrected(),
			self.disksMat.value.get_rotate_scale_corrected()
		)

		#print("P:"+str( pencilRot )+"")
		#print("T:"+str( self.disksMat.value.get_rotate_scale_corrected() )+"")
		if(self.index < len(W)):
			if self.error < W[self.index]/2:
				print("HIT:" + str(self.error)+"°")
				self.goal=True
				setupEnvironment.setBackgroundColor(avango.gua.Color(0, 0.2, 0.05), 0.18)
				if(setupEnvironment.useAutoDetect==False):
					self.succesful_clicks=self.succesful_clicks+1
			else:
				print("MISS:" + str(self.error)+"°")
				self.goal=False
				setupEnvironment.setBackgroundColor(avango.gua.Color(0.3, 0, 0), 0.18)

			#move target			
			if setupEnvironment.randomTargets:
				if THREEDIMENSIONTASK:
					rotation=self.getRandomRotation3D()
					self.disksMat.value = rotation
				else:
					rotation=self.getRandomRotation2D()
					self.disksMat.value = rotation

			else:
				if self.backAndForth: #aim get right
					self.disksMat.value = avango.gua.make_rot_mat(0, 0, 1, 0)
					self.backAndForth=False
				else:
					self.backAndForth=True
					rotateAroundX=0
					if not self.backAndForthAgain:
						self.backAndForthAgain=True
						if THREEDIMENSIONTASK:
							rotateAroundX=1
						else:
							rotateAroundX=0
					self.disksMat.value = avango.gua.make_rot_mat(D, rotateAroundX, 1, 0)
			
				self.disks.setDisksTransMats(targetDiameter[self.index])

			
			self.counter=self.counter+1

			self.setID(self.index)
		else: #trial over
			setupEnvironment.setBackgroundColor(avango.gua.Color(0,0,1), 1)

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
		

	def logData(self):
		if THREEDIMENSIONTASK:
			path="results/results_rotation_3D/"
		else:
			path="results/results_rotation_2D/"
		if(self.startedTest and self.endedTest==False):
			if self.created_file==False: #create File 
				self.num_files=len([f for f in os.listdir(path)
					if os.path.isfile(os.path.join(path, f))])
				self.created_file=True
			else: #write permanent values
				self.result_file=open(path+"rotation2D_trial"+str(self.num_files)+".replay", "a+")
				
				self.result_file.write(
					"TimeStamp: "+str(self.timer.value)+"\n"+
					"Error: "+str(self.error)+"\n"+
					"Pointerpos: \n"+str(self.pencilTransMat.value)+"\n"+
					"Aimpos: \n"+str(self.disksMat.value)+"\n\n")
				self.result_file.close()
			
				if self.Button.value: #write resulting values
					self.result_file=open(path+"rotation2D_trial"+str(self.num_files)+".log", "a+")
					if(self.flagPrinted==False):
						self.logSetter()
						logmanager.log(self.result_file)
						self.flagPrinted=True
					self.result_file.close()

	def logSetter(self):
		self.setID(self.index)
		self.setMT(self.lastTime, self.timer.value)
		self.setTP(self.index)
		logmanager.setUserID(self.userID)
		logmanager.setGroup(self.group)
		if setupEnvironment.space3D:
			if setupEnvironment.reduceDOFTranslate:
				logmanager.setCondition("rotation2D_air_locked_virtual")
				logmanager.setDOFVirtual(0, 1)
			else:
				logmanager.setCondition("rotation2D_air_free_virtual")
				logmanager.setDOFVirtual(0, 3)
			logmanager.setDOFReal(0, 3)
		else:
			if setupEnvironment.reduceDOFTranslate:
				logmanager.setCondition("rotation2D_table_locked_virtual")
				logmanager.setDOFVirtual(0, 1)
				logmanager.setDOFReal(0, 1)

		if self.backAndForth:
			logmanager.setMovementDirection("r")
		else:
			logmanager.setMovementDirection("l")

		logmanager.setRotationAxis("y")
		logmanager.setTargetDistance_r(D)
		logmanager.setTargetWidth_r(W[self.index])
		logmanager.setID_combined(0, self.ID)
		logmanager.setRepetition(N)
		logmanager.setTrial(self.trial)
		if(setupEnvironment.useAutoDetect==False):
			logmanager.setClicks(self.trial, self.succesful_clicks)
			hittype="BUTTON"
		else:
			hittype="AUTO"
		logmanager.setSuccess(self.goal)
		logmanager.setHit(hittype, self.MT, 0, self.error)

		logmanager.setThroughput()

		self.trial=self.trial+1

	def setID(self, index):
		if(index<len(ID)):
			self.ID = ID[index]
		print("ID: "+ str(self.ID))

	def setMT(self, start, end):
		self.MT=end-start
		self.lastTime=self.timer.value
		print("Time: " + str(self.MT))

	def setTP(self, index):
		if(self.MT>0 and self.index<len(ID)):
			self.TP=ID[index]/self.MT

	def handle_key(self, key, scancode, action, mods):
		if action == 1:
			#32 is space 335 is num_enter
			if key==32 or key==335:
				if(self.endedTest==False):
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
	pencil = setupEnvironment.loader.create_geometry_from_file("colored_cross", "data/objects/colored_cross.obj", avango.gua.LoaderFlags.DEFAULTS |  avango.gua.LoaderFlags.LOAD_MATERIALS)
	#pencil.Transform.value = avango.gua.make_scale_mat(1)#to prevent that this gets huge
	#pencil.Material.value.set_uniform("Color", avango.gua.Vec4(0.6, 0.6, 0.6, 1))
	#pencil.Material.value.set_uniform("Emissivity", 1.0)

	disksNode = trackManager.disks.setupDisks(pencil.Transform.value.get_translate())
	trackManager.disks.setDisksTransMats(targetDiameter[0])

	everyObject = avango.gua.nodes.TransformNode(
		Children = [disksNode, pencil], 
		Transform = setupEnvironment.centerPosition#*avango.gua.make_scale_mat(3)
	)

	#add nodes to root
	graph.Root.value.Children.value.append(everyObject)

	#listen to tracked position of pointer
	pointer_device_sensor = avango.daemon.nodes.DeviceSensor(DeviceService = avango.daemon.DeviceService())
	pointer_device_sensor.TransmitterOffset.value = setupEnvironment.offsetTracking

	pointer_device_sensor.Station.value = "pointer"

	trackManager.pencilTransMat.connect_from(pointer_device_sensor.Matrix)
	pencil.Transform.connect_from(trackManager.pencilTransMat)

	#connect pencil
	#pencil.Transform.connect_from(trackManager.pencilTransMat)

	#listen to button
	button_sensor=avango.daemon.nodes.DeviceSensor(DeviceService=avango.daemon.DeviceService())
	button_sensor.Station.value="device-pointer"

	trackManager.Button.connect_from(button_sensor.Button0)

	#connect disks
	trackManager.disksMat.connect_from(disksNode.Transform)
	disksNode.Transform.connect_from(trackManager.disksMat)

	#timer
	timer = avango.nodes.TimeSensor()
	trackManager.timer.connect_from(timer.Time)


	setupEnvironment.launch(globals())


if __name__ == '__main__':
  start()