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

THREEDIMENSIONTASK=False

r = 0.16 #circle radius
r1 = 0.15 #circle des stabes
r2 = 0.05#länge des stabes

r_spitze=0.05

rotation2D=[avango.gua.make_rot_mat(20, 1, 0.8, 0),
			avango.gua.make_rot_mat(90, 0.1, 0.2, 0)]

rotation3D=[avango.gua.make_rot_mat(20, 1, 0.8, 0.3),
			avango.gua.make_rot_mat(90, 0.1, 0.2, 0.9)]

N=5 #number of tests per ID
ID=[4, 5, 6] #fitt's law

W=[]

for i in range(0, len(ID)):
	if setupEnvironment.randomTargets():
		D=[ setupEnvironment.getRotationError1D(rotation2D[0].get_rotate(), rotation2D[1].get_rotate()) ] #in degrees
		W=[D[0]/(2**ID[0]-1), D[0]/(2**ID[1]-1), D[0]/(2**ID[2]-1)] #in degrees, Fitt's Law umgeformt nach W
	else:
		D=45
		W.append(D/(2**ID[0]-1))

targetDiameter = [
	2*r_spitze*math.tan(W[0]/2*math.pi/180),
	2*r_spitze*math.tan(W[1]/2*math.pi/180),
	2*r_spitze*math.tan(W[2]/2*math.pi/180)
]#größe (Druchmesser) der Gegenkathete auf dem kreisumfang

graph = avango.gua.nodes.SceneGraph(Name="scenegraph") #Create Graph
loader = avango.gua.nodes.TriMeshLoader() #Create Loader
pencil_transform = avango.gua.nodes.TransformNode()

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
		self.endTime = 0
		self.backAndForth = False
		self.backAndForthAgain = False;

	def __del__(self):
		if setupEnvironment.logResults():
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
			#attach pipes to cursor
			rot = self.pencilTransMat.value.get_rotate_scale_corrected()
			if THREEDIMENSIONTASK:
				rotateAroundX=1
			else:
				rotateAroundX=0

			#move aim and ghost to pointer
			self.disksMat.value = avango.gua.make_trans_mat(self.pencilTransMat.value.get_translate())*avango.gua.make_rot_mat(self.disksMat.value.get_rotate_scale_corrected())*avango.gua.make_scale_mat(self.disksMat.value.get_scale()) #keep rotation and move to pointer
			

	@field_has_changed(timer)
	def updateTimer(self):
		self.tidyMats()
		
		if setupEnvironment.logResults():	
			self.logData()

	def tidyMats(self):
		if not setupEnvironment.space3D():# on table?

			#erase 2dof at table, unstable operation, calling this twice destroys the rotation information
			#get angle between rotation and y axis
			q = self.pencilTransMat.value.get_rotate_scale_corrected()
			q.z = 0 #tried to fix to remove roll
			q.x = 0 #tried to fix to remove roll
			q.normalize()
			yRot = avango.gua.make_rot_mat(setupEnvironment.get_euler_angles(q)[0]*180.0/math.pi,0,1,0)#get euler y rotation, has also roll in it

			zCorrection=setupEnvironment.getOffsetTracking().get_translate().y

		else:
			yRot = avango.gua.make_rot_mat(self.pencilTransMat.value.get_rotate_scale_corrected())
			zCorrection=0

			self.pencilTransMat.value = (
				avango.gua.make_trans_mat(
					self.pencilTransMat.value.get_translate().x-setupEnvironment.getOffsetTracking().get_translate().x,
					self.pencilTransMat.value.get_translate().y-zCorrection,
					self.pencilTransMat.value.get_translate().z-setupEnvironment.getOffsetTracking().get_translate().z
				)
				* yRot #add rotation
			)
				

	def nextSettingStep(self):
		self.startedTest=True
		print(self.current_index)
		if(self.counter==N):
			self.current_index=self.current_index+1
			self.counter=0

		if(self.current_index==len(W)):
			self.endedTest=True

		self.error = setupEnvironment.getRotationError1D(
			self.pencilTransMat.value.get_rotate_scale_corrected(),
			self.disksMat.value.get_rotate_scale_corrected()
		)

		#print("P:"+str( pencilRot )+"")
		#print("T:"+str( self.disksMat.value.get_rotate_scale_corrected() )+"")
		if(self.current_index < len(W)):
			if self.error < W[self.current_index]/2:
				print("HIT:" + str(self.error)+"°")
				self.goal=True
				setupEnvironment.setBackgroundColor(avango.gua.Color(0, 0.2, 0.05), 0.18)
			else:
				print("MISS:" + str(self.error)+"°")
				self.goal=False
				setupEnvironment.setBackgroundColor(avango.gua.Color(0.3, 0, 0), 0.18)

			#move target
			
			if setupEnvironment.randomTargets():
				if THREEDIMENSIONTASK:
					rotation=self.getRandomRotation3D()
					self.disksMat.value = rotation*avango.gua.make_trans_mat(0, 0, -r)*avango.gua.make_scale_mat(targetDiameter[self.current_index])
				else:
					rotation=self.getRandomRotation2D()
					self.disksMat.value = rotation*avango.gua.make_trans_mat(0, 0, -r)*avango.gua.make_scale_mat(targetDiameter[self.current_index])

			else:
				if self.backAndForth:
					self.disksMat.value = avango.gua.make_trans_mat(0, 0, -r)*avango.gua.make_scale_mat(targetDiameter[self.current_index])
					self.backAndForth=False
				else:
					self.backAndForth=True
					if not self.backAndForthAgain:
						self.backAndForthAgain=True
						if THREEDIMENSIONTASK:
							rotateAroundX=1
						else:
							rotateAroundX=0
						self.disksMat.value = avango.gua.make_rot_mat(D,rotateAroundX,1,0)*avango.gua.make_trans_mat(0, 0, -r)*avango.gua.make_scale_mat(targetDiameter[self.current_index])
					else:
						rotateAroundX=0
					self.disksMat.value = avango.gua.make_rot_mat(D, rotateAroundX, 1, 0)*avango.gua.make_trans_mat(0, 0, -r)*avango.gua.make_scale_mat(targetDiameter[self.current_index])
			

			self.setMT(self.lastTime, self.timer.value)
			self.lastTime=self.timer.value
			self.counter=self.counter+1

			self.setID(self.current_index)
			self.setTP(self.current_index)
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
						self.result_file.write(
							"HT: "+str(self.goal)+"\n"+
							"MT: "+str(self.MT)+"\n"+
							"ID: "+str(self.ID)+"\n"+
							"TP: "+str(self.TP)+"\n"+
							"W : "+str(W[self.current_index])+"\n"
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
	pencil = loader.create_geometry_from_file("colored_cross", "data/objects/colored_cross.obj", avango.gua.LoaderFlags.DEFAULTS |  avango.gua.LoaderFlags.LOAD_MATERIALS)
	#pencil.Transform.value = avango.gua.make_scale_mat(1)#to prevent that this gets huge
	#pencil.Material.value.set_uniform("Color", avango.gua.Vec4(0.6, 0.6, 0.6, 1))
	#pencil.Material.value.EnableBackfaceCulling.value = False
	#pencil.Material.value.set_uniform("Emissivity", 1.0)

	disk1 = loader.create_geometry_from_file("disk", "data/objects/disk_rotated.obj", avango.gua.LoaderFlags.NORMALIZE_SCALE)
	disk1.Transform.value = avango.gua.make_trans_mat(0, 0, -r_spitze)*avango.gua.make_scale_mat(targetDiameter[0])#position*size
	disk1.Material.value.set_uniform("Color", avango.gua.Vec4(0.0, 1.0, 0.0, 0.6))

	disksNode = avango.gua.nodes.TransformNode(
		Children = [disk1]
	)	

	if setupEnvironment.space3D():
		disk2 = loader.create_geometry_from_file("cylinder", "data/objects/disk_rotated.obj", avango.gua.LoaderFlags.NORMALIZE_SCALE)
		disk2.Transform.value = avango.gua.make_rot_mat(-90,0,1,0)*avango.gua.make_trans_mat(0, 0, -r_spitze)*avango.gua.make_scale_mat(targetDiameter[0])
		disk2.Material.value.set_uniform("Color", avango.gua.Vec4(1.0, 0.0, 0.0, 0.6))
		disksNode.Children.value.append(disk2)

		disk3 = loader.create_geometry_from_file("cylinder", "data/objects/disk_rotated.obj", avango.gua.LoaderFlags.NORMALIZE_SCALE)
		disk3.Transform.value = avango.gua.make_rot_mat(90,0,1,0)*avango.gua.make_trans_mat(0, 0, -r_spitze)*avango.gua.make_scale_mat(targetDiameter[0])
		disk3.Material.value.set_uniform("Color", avango.gua.Vec4(0.5, 0.5, 0.5, 0.6))
		disksNode.Children.value.append(disk3)

		disk4 = loader.create_geometry_from_file("cylinder", "data/objects/disk_rotated.obj", avango.gua.LoaderFlags.NORMALIZE_SCALE)
		disk4.Transform.value = avango.gua.make_rot_mat(90,1,0,0)*avango.gua.make_trans_mat(0, 0, -r_spitze)*avango.gua.make_scale_mat(targetDiameter[0])
		disk4.Material.value.set_uniform("Color", avango.gua.Vec4(0.0, 0.0, 1.0, 0.6))
		disksNode.Children.value.append(disk4)

		disk5 = loader.create_geometry_from_file("cylinder", "data/objects/disk_rotated.obj", avango.gua.LoaderFlags.NORMALIZE_SCALE)
		disk5.Transform.value = avango.gua.make_rot_mat(-90,1,0,0)*avango.gua.make_trans_mat(0, 0, -r_spitze)*avango.gua.make_scale_mat(targetDiameter[0])
		disk5.Material.value.set_uniform("Color", avango.gua.Vec4(0.5, 0.5, 0.5, 0.6))
		disksNode.Children.value.append(disk5)


		disk6 = loader.create_geometry_from_file("cylinder", "data/objects/disk_rotated.obj", avango.gua.LoaderFlags.NORMALIZE_SCALE)
		disk6.Transform.value = avango.gua.make_rot_mat(180,0,1,0)*avango.gua.make_trans_mat(0, 0, -r_spitze)*avango.gua.make_scale_mat(targetDiameter[0])
		disk6.Material.value.set_uniform("Color", avango.gua.Vec4(0.5, 0.5, 0.5, 0.6))
		disksNode.Children.value.append(disk6)



	everyObject = avango.gua.nodes.TransformNode(
		Children = [disksNode, pencil], 
		Transform = setupEnvironment.getCenterPosition()#*avango.gua.make_scale_mat(3)
	)

	#add nodes to root
	graph.Root.value.Children.value.append(everyObject)

	#listen to tracked position of pointer
	pointer_device_sensor = avango.daemon.nodes.DeviceSensor(DeviceService = avango.daemon.DeviceService())
	pointer_device_sensor.TransmitterOffset.value = setupEnvironment.getOffsetTracking()

	pointer_device_sensor.Station.value = "pointer"

	trackManager.pencilTransMat.connect_from(pointer_device_sensor.Matrix)
	pencil.Transform.connect_from(trackManager.pencilTransMat)

	#connect pencil
	#pencil.Transform.connect_from(trackManager.pencilTransMat)

	#listen to button
	button_sensor=avango.daemon.nodes.DeviceSensor(DeviceService=avango.daemon.DeviceService())
	button_sensor.Station.value="device-pointer"

	trackManager.Button.connect_from(button_sensor.Button0)

	#connect disk1
	trackManager.disksMat.connect_from(disksNode.Transform)
	disksNode.Transform.connect_from(trackManager.disksMat)

	#timer
	timer = avango.nodes.TimeSensor()
	trackManager.timer.connect_from(timer.Time)


	setupEnvironment.launch(globals())


if __name__ == '__main__':
  start()