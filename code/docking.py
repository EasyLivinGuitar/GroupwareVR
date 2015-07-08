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

THREEDIMTASK=False

r=0.16 #circle radius
r1 =0.15 #circle des stabes
r2 = 0.05#länge des stabes


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
aimPencil = avango.gua.nodes.TransformNode()
disk1 = avango.gua.nodes.TransformNode()


class trackingManager(avango.script.Script):
	Button = avango.SFBool()
	pencilTransMat = avango.gua.SFMatrix4()
	aimPencilMat = avango.gua.SFMatrix4()
	aimHullMat = avango.gua.SFMatrix4()
	disksMat = avango.gua.SFMatrix4()
	cylinder1Mat = avango.gua.SFMatrix4()
	cylinder2Mat = avango.gua.SFMatrix4()
	timer = avango.SFFloat()
	
	time2=0

	startedTest = False
	endedTest = False

	created_file =  False
	flagPrinted = False

	current_index=0
	counter=0

	error=[]

	MT=0
	ID=0
	TP=0

	goal=False


	def __init__(self):
		self.super(trackingManager).__init__()
		self.isInside = False;
		self.startTime = 0
		self.aimPencilRef = None
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
		print(self.current_index)
		if(self.counter==N):
			self.current_index=self.current_index+1
			self.counter=0

		if(self.current_index==len(W_rot)):
			self.endedTest=True

		self.error = setupEnvironment.getRotationError1D(
			self.pencilTransMat.value.get_rotate_scale_corrected(),
			self.disk1Mat.value.get_rotate_scale_corrected()
		)

		#print("P:"+str( pencilRot )+"")
		#print("T:"+str( self.disk1Mat.value.get_rotate_scale_corrected() )+"")
		if(self.current_index < len(W_rot)):
			if self.error < W_rot[self.current_index]/2:
				print("HIT:" + str(self.error)+"°")
				self.goal=True
				setupEnvironment.setBackgroundColor(avango.gua.Color(0, 0.2, 0.05), 0.18)
			else:
				print("MISS:" + str(self.error)+"°")
				self.goal=False
				setupEnvironment.setBackgroundColor(avango.gua.Color(0.3, 0, 0), 0.18)

			if THREEDIMTASK:
				rotateAroundX = 1
			else:
				rotateAroundX = 0

			#move target
			if self.backAndForth:
				self.aimPencilMat.value = avango.gua.make_trans_mat(-D_trans/2,0,0)*avango.gua.make_rot_mat(-D_rot/2, rotateAroundX, 1, 0)*avango.gua.make_trans_mat(0, 0, -r)
				self.aimHullMat.value = self.aimPencilMat.value*avango.gua.make_scale_mat(W_trans[self.current_index])
				self.disk1Mat.value = avango.gua.make_trans_mat(-D_trans/2,0,0)*avango.gua.make_rot_mat(D_rot/2, rotateAroundX, 1, 0)*avango.gua.make_trans_mat(0, 0, r) * avango.gua.make_scale_mat(targetDiameter[self.current_index]) #copy from aim

				self.backAndForth=False
			else:
				self.backAndForth=True
				self.aimPencilMat.value = avango.gua.make_trans_mat(D_trans/2,0,0)*avango.gua.make_rot_mat(D_rot/2, rotateAroundX, 1, 0)*avango.gua.make_trans_mat(0, 0, -r)
				self.aimHullMat.value = self.aimPencilMat.value*avango.gua.make_scale_mat(W_trans[self.current_index])
				self.disk1Mat.value = avango.gua.make_trans_mat(D_trans/2,0,0)*avango.gua.make_rot_mat(D_rot/2, rotateAroundX, 1, 0)*avango.gua.make_trans_mat(0, 0, r) * avango.gua.make_scale_mat(targetDiameter[self.current_index]) #copy from aim

			self.setMT(self.startTime, self.timer.value)
			self.startTime = self.timer.value

			self.counter=self.counter+1
			self.setID(self.current_index)
			self.setTP(self.current_index)
		else: #trial over
			setupEnvironment.setBackgroundColor(avango.gua.Color(0,0,1), 1)
		

	def logData(self):
		if THREEDIMTASK:
			path="results/docking_3D/"
		else:
			path="results/docking_2D/"
		if(self.startedTest and self.endedTest==False):
			if self.created_file==False: #create File 
				self.num_files=len([f for f in os.listdir(path)
					if os.path.isfile(os.path.join(path, f))])
				self.created_file=True
			else: #write permanent values
				self.result_file=open(path+"docking_trial"+str(self.num_files)+".replay", "a+")
				
				self.result_file.write(
					"TimeStamp: "+str(self.timer.value)+"\n"+
					"Error: "+str(self.error)+"\n"+
					"Pointerpos: \n"+str(self.pencilTransMat.value)+"\n"+
					"Aimpos: \n"+str(self.aimPencilMat.value)+"\n\n")
				self.result_file.close()
			
				if self.Button.value: #write resulting values
					self.result_file=open(path+"docking_trial"+str(self.num_files)+".log", "a+")
					if(self.flagPrinted==False):
						self.result_file.write(
							"HT: "+str(self.goal)+"\n"+
							"MT: "+str(self.MT)+"\n"+
							"ID: "+str(self.ID)+"\n"+
							"TP: "+str(self.TP)+"\n"+
							"W : "+str(W_rot[self.current_index])+"\n"
							"Total Error: "+str(self.error)+"\n"+
							"=========================\n\n")
						self.flagPrinted=True
					self.result_file.close()

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

def handle_key(key, scancode, action, mods):
	if action == 1:
		#32 is space 335 is num_enter
		if key==32 or key==335:
			if(trackManager.endedTest==False):
				#trackManager.nextSettingStep()
				trackManager.Button.value=True
			else:
				print("Test ended")
	else:
		trackManager.flagPrinted=False

trackManager = trackingManager()
def start ():

	setupEnvironment.getWindow().on_key_press(handle_key)
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
	aimBalloon.Transform.value = avango.gua.make_trans_mat(0, 0, r)*avango.gua.make_scale_mat(0.2)
	aimBalloon.Material.value.set_uniform("Color", avango.gua.Vec4(0.3, 0.4, 0.3, 0.2))

	disk1 = loader.create_geometry_from_file("disk", "data/objects/disk_rotated.obj", avango.gua.LoaderFlags.NORMALIZE_SCALE)
	disk1.Transform.value = avango.gua.make_trans_mat(0, 0, -r)*avango.gua.make_scale_mat(targetDiameter[0])#position*size
	disk1.Material.value.set_uniform("Color", avango.gua.Vec4(0.2, 0.6, 0.3, 0.6))


	everyObject = avango.gua.nodes.TransformNode(
		Children = [aimBalloon, disksNode, pencil_transform], 
		Transform = setupEnvironment.centerPosition
	)

	#add nodes to root
	graph.Root.value.Children.value.append(everyObject)

	
	#listen to tracked position of pointer
	pointer_device_sensor = avango.daemon.nodes.DeviceSensor(DeviceService = avango.daemon.DeviceService())
	pointer_device_sensor.TransmitterOffset.value = setupEnvironment.offsetTracking

	pointer_device_sensor.Station.value = "pointer"

	trackManager.pencilTransMat.connect_from(pointer_device_sensor.Matrix)

	#connect pencil
	pencil.Transform.connect_from(trackManager.pencilTransMat)

	#listen to button
	button_sensor=avango.daemon.nodes.DeviceSensor(DeviceService=avango.daemon.DeviceService())
	button_sensor.Station.value="device-pointer"

	trackManager.Button.connect_from(button_sensor.Button0)

	#connect aimPencil
	trackManager.aimPencilRef = aimPencil
	trackManager.aimPencilMat.connect_from(aimPencil.Transform)
	aimPencil.Transform.connect_from(trackManager.aimPencilMat)
	trackManager.aimHullMat.connect_from(aimBalloon.Transform)
	aimBalloon.Transform.connect_from(trackManager.aimHullMat)

	#connect disks
	trackManager.disksMat.connect_from(disksNode.Transform)
	disksNode.Transform.connect_from(trackManager.disksMat)

	#timer
	timer = avango.nodes.TimeSensor()
	trackManager.timer.connect_from(timer.Time)


	setupEnvironment.launch(globals())


if __name__ == '__main__':
  start()