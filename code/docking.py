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

graph = avango.gua.nodes.SceneGraph(Name="scenegraph") #Create Graph
loader = avango.gua.nodes.TriMeshLoader() #Create Loader
pencil_transform = avango.gua.nodes.TransformNode()

logmanager=logManager.logManager()

class trackingManager(avango.script.Script):
	Button = avango.SFBool()
	pencilTransMat = avango.gua.SFMatrix4()
	timer = avango.SFFloat()
	
	time2=0

	startedTest = False
	endedTest = False

	created_file =  False
	flagPrinted = False

	current_index=0
	counter=0

	#Logging
	userID=0
	group=0
	trial=0
	MT=0
	ID=0
	TP=0

	goal=False

	succesful_clicks=0


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

	def __del__(self):
		if setupEnvironment.logResults:
			pass # self.result_file.close()

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
		if (not self.endedTest and setupEnvironment.getDistance3D(self.pencilTransMat.value, self.aim.Transform.value) <= W_trans[self.index]) :
			#attach disks to pointer
			self.disks.getNode().Transform.value = avango.gua.make_trans_mat(self.pencilTransMat.value.get_translate())*avango.gua.make_rot_mat(self.disks.getNode().Transform.value.get_rotate_scale_corrected())*avango.gua.make_scale_mat(self.disks.getNode().Transform.value.get_scale()) #keep rotation and scale and move to pointer
			#self.aim.Tags.value = []
			# print("then")
			#self.disks.getNode().Tags.value = []
		else:
			#attach disks to aim
			self.disks.getNode().Transform.value = avango.gua.make_trans_mat(self.aim.Transform.value.get_translate())*avango.gua.make_rot_mat(self.disks.getNode().Transform.value.get_rotate_scale_corrected())*avango.gua.make_scale_mat(self.disks.getNode().Transform.value.get_scale()) #keep rotation and scale and move to pointe
			# print("else")
			#self.disks.getNode().Tags.value = ["invisible"]

	@field_has_changed(timer)
	def updateTimer(self):
		# print("timer")
		self.pencilTransMat.value = setupEnvironment.reducePencilMat(self.pencilTransMat.value)
		
		if setupEnvironment.logResults:	
			self.logData()
		

	def nextSettingStep(self):
		self.startedTest=True
		print(self.index)
		if(self.counter%N == N-1):
			self.index=self.index+1

		if(self.index==len(W_rot)):
			self.endedTest=True

		#print("P:"+str( pencilRot )+"")
		#print("T:"+str( self.disksMat.value.get_rotate_scale_corrected() )+"")
		if(self.index < len(W_rot)):
			if self.getErrorRotate() < W_rot[self.index]/2 and self.getErrorTranslate() < W_trans[self.index]/2:
				print("HIT: Rot: " + str(self.getErrorRotate())+"° "+ "Trans: "+ str(self.getErrorTranslate()))
				self.goal=True
				setupEnvironment.setBackgroundColor(avango.gua.Color(0, 0.2, 0.05), 0.18)
				if(setupEnvironment.useAutoDetect==False):
					self.succesful_clicks=self.succesful_clicks+1
			else:
				print("MISS: Rot: " + str(self.getErrorRotate())+"° "+ "Trans: "+ str(self.getErrorTranslate()))
				self.goal=False
				setupEnvironment.setBackgroundColor(avango.gua.Color(0.3, 0, 0), 0.18)

			#move target			
			if setupEnvironment.randomTargets:
				if THREEDIMENSIONTASK:
					rotation=self.getRandomRotation3D()
					self.disks.getNode().value = rotation
				else:
					rotation=self.getRandomRotation2D()
					self.disksMat.getNode().value = rotation

			else:

				#switches aim and shadow aim
				temp = self.aimShadow.Transform.value
				self.aimShadow.Transform.value = self.aim.Transform.value 
				self.aim.Transform.value = temp

				self.aim.Transform.value = avango.gua.make_trans_mat(self.aim.Transform.value.get_translate())* avango.gua.make_scale_mat(W_trans[self.index])
				self.aimShadow.Transform.value = avango.gua.make_trans_mat(self.aimShadow.Transform.value.get_translate())* avango.gua.make_scale_mat(W_trans[self.index])	

				if self.backAndForth: #aim get right
					self.disks.getNode().Transform.value = avango.gua.make_rot_mat(0, 0, 1, 0)
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
					self.disks.getNode().Transform.value = avango.gua.make_rot_mat(D_rot, rotateAroundX, 1, 0)
			
				self.disks.setDisksTransMats(targetDiameter[self.index])

			
			self.counter=self.counter+1

			self.setID(self.index)
		else: #trial over
			setupEnvironment.setBackgroundColor(avango.gua.Color(0,0,1), 1)
		
	def getErrorRotate(self):
		return setupEnvironment.getRotationError1D(
			self.pencilTransMat.value.get_rotate_scale_corrected(),
			self.disks.getNode().Transform.value.get_rotate_scale_corrected()
		)

	def getErrorTranslate(self):
		return setupEnvironment.getDistance3D(self.pencilTransMat.value, self.aim.Transform.value)

	def logData(self):
		if THREEDIMENSIONTASK==False:
			path="results/results_docking_2D/"
		else:
			path="results/results_docking_3D/"

		if not os.path.exists(path):
			os.makedirs(path)

		if(self.startedTest and self.endedTest==False):
			if self.created_file==False: #create File 
				self.num_files=len([f for f in os.listdir(path)
					if os.path.isfile(os.path.join(path, f))])
				self.created_file=True
			else: #write permanent values
				self.result_file=open(path+"docking_trial"+str(self.num_files)+".replay", "a+")
				
				self.result_file.write(
					"TimeStamp: "+str(self.timer.value)+"\n"+
					"Error: "+str(self.getErrorRotate())+"\n"+
					"Pointerpos: \n"+str(self.pencilTransMat.value)+"\n"+
					"Aimpos: \n"+str(self.pencilTransMat.value)+"\n\n")
				self.result_file.close()
			
				if self.Button.value: #write resulting values
					self.result_file=open(path+"docking_trial"+str(self.num_files)+".log", "a+")
					if(self.flagPrinted==False):
						self.logSetter()
						logmanager.log(self.result_file)
						self.flagPrinted=True
					self.result_file.close()

	def logSetter(self):
		logmanager.setUserID(self.userID)
		logmanager.setGroup(self.group)

		if(setupEnvironment.space3D):
			if(setupEnvironment.reduceDOFTranslate and setupEnvironment.reduceDOFRotate):
				logmanager.setCondition("docking2D_air_locked_virtual")
				logmanager.setDOFVirtual(2, 1)
			else:
				logmanager.setCondition("docking2D_air_free_virtual")
				logmanager.setDOFVirtual(3, 3)
			logmanager.setDOFReal(3, 3)
		else:
			logmanager.setCondition("docking2D_table_locked_virtual")
			logmanager.setDOFVirtual(2, 1)
			logmanager.setDOFReal(2, 2)

		if self.backAndForth:
			logmanager.setMovementDirection("r")
		else:
			logmanager.setMovementDirection("l")

		# logmanager.setID_combined()
		logmanager.setRepetition(N)
		logmanager.setTrial(self.trial)
		self.trial=self.trial+1

	def setID(self, index):
		if(index<len(ID)):
			self.ID = ID[index]
		print("ID: "+ str(self.ID))

	def setMT(self, start, end):
		self.MT=end-start
		print("Time: " + str(self.MT))

	def setTP(self, index):
		if(self.MT>0 and self.current_index<len(ID)):
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


def start ():
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

	pencil_transform = avango.gua.nodes.TransformNode(
		Children=[pencil]#, 
		#Transform=avango.gua.make_trans_mat(0, screenOffsetBottom, setupEnvironment.getTargetDepth())
	)

	disksNode = trackManager.disks.setupDisks(pencil.Transform.value.get_translate())
	trackManager.disks.setDisksTransMats(targetDiameter[0])

	aimBalloon = loader.create_geometry_from_file("pointer_object_abstract", "data/objects/sphere_new.obj", avango.gua.LoaderFlags.NORMALIZE_SCALE)
	aimBalloon.Transform.value = avango.gua.make_trans_mat(-D_trans/2, 0, 0)*avango.gua.make_trans_mat(0, 0, r)*avango.gua.make_scale_mat(0.2)
	aimBalloon.Material.value.set_uniform("Color", avango.gua.Vec4(1, 1, 0, 1))

	aimShadow  = loader.create_geometry_from_file("pointer_object_abstract", "data/objects/sphere_new.obj", avango.gua.LoaderFlags.NORMALIZE_SCALE)
	aimShadow.Transform.value = avango.gua.make_trans_mat(D_trans/2, 0, 0)*avango.gua.make_scale_mat(W_trans[0])
	aimShadow.Material.value.set_uniform("Color", avango.gua.Vec4(0.5, 0.5, 0.5, 0.1))

	everyObject = avango.gua.nodes.TransformNode(
		Children = [aimBalloon, aimShadow, disksNode, pencil_transform], 
		Transform = setupEnvironment.centerPosition
	)

	#add nodes to root
	graph.Root.value.Children.value.append(everyObject)


	#connect aimPencil
	trackManager.aim = aimBalloon;
	trackManager.aimShadow = aimShadow
	
	#listen to tracked position of pointer
	pointer_device_sensor = avango.daemon.nodes.DeviceSensor(DeviceService = avango.daemon.DeviceService())
	pointer_device_sensor.TransmitterOffset.value = setupEnvironment.offsetTracking

	pointer_device_sensor.Station.value = "pointer"

	#connect pencil
	trackManager.pencilTransMat.connect_from(pointer_device_sensor.Matrix)
	pencil.Transform.connect_from(trackManager.pencilTransMat)

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