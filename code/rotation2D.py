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

r=0.16 #circle radius
r1 =0.15 #circle des stabes
r2 = 0.05#länge des stabes


#fitt's law parameter
D=45 #in degrees
ID=[4, 5, 6] #fitt's law
N=5 #number of tests per ID
W=[D/(2**ID[0]-1), D/(2**ID[1]-1), D/(2**ID[2]-1)] #in degrees, Fitt's Law umgeformt nach W

torus1Width = [2*r*math.tan(W[0]/2*math.pi/180), 2*r*math.tan(W[1]/2*math.pi/180), 2*r*math.tan(W[2]/2*math.pi/180)]
torus2Width = [2*math.tan(90-W[0]/2*math.pi/180)*(r2-math.tan(W[0]/2*math.pi/180)*r1), 2*math.tan(90-W[1]/2*math.pi/180)*(r2-math.tan(W[1]/2*math.pi/180)*r1), 2*math.tan(90-W[2]/2*math.pi/180)*(r2-math.tan(W[2]/2*math.pi/180)*r1)]

screenOffsetBottom=-0.1

graph = avango.gua.nodes.SceneGraph(Name="scenegraph") #Create Graph
loader = avango.gua.nodes.TriMeshLoader() #Create Loader
pencil_transform = avango.gua.nodes.TransformNode()
aimPencil = avango.gua.nodes.TransformNode()
torus1 = avango.gua.nodes.TransformNode()


class trackingManager(avango.script.Script):
	Button = avango.SFBool()
	pencilTransMat = avango.gua.SFMatrix4()
	aimPencilMat = avango.gua.SFMatrix4()
	torus1Mat = avango.gua.SFMatrix4()
	timer = avango.SFFloat()
	
	time1=0
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

	evenTrial=False


	def __init__(self):
		self.super(trackingManager).__init__()
		self.isInside = False;
		self.startTime = 0
		self.endTime = 0
		self.aimPencilRef = None
		self.backAndForth = False
		#self.aimPencilRef=None

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

	@field_has_changed(timer)
	def updateTimer(self):
		self.tidyMats()

	
		#if self.timer.value-self.startTime > 2 and self.isInside==True: #timer abbgelaufen:
		#	self.isInside = False
		
		if setupEnvironment.logResults():	
			self.logData()
			#self.aimPencilMat.value *= avango.gua.make_trans_mat(500,0,0) 
			#getattr(self, "aimPencilRef").Material.value.set_uniform("Color", avango.gua.Vec4(1, 1,0, 0.5)) #Transparenz funktioniert nicht
			#bewege aimPencil an neue Stelle

	def tidyMats(self):
	
		#erase 2dof, unstable operation, calling this twice destroys the rotation information
		if setupEnvironment.space3D():
			self.pencilTransMat.value = (
				avango.gua.make_rot_mat(self.pencilTransMat.value.get_rotate_scale_corrected()) #add rotation
				* avango.gua.make_trans_mat(0,0,-r)
			)
		else:
			#get angle between rotation and y axis
			q = self.pencilTransMat.value.get_rotate_scale_corrected()
			q.z = 0 #tried to fix to remove roll
			q.x = 0 #tried to fix to remove roll
			q.normalize()
			yRot = setupEnvironment.get_euler_angles(q)[0]#get euler y rotation, has also roll in it
			self.pencilTransMat.value = (
				avango.gua.make_rot_mat(yRot*180.0/math.pi,0,1,0) #add rotation
				* avango.gua.make_trans_mat(0,0,-r)
			)#keep translation
				



	def nextSettingStep(self):
		self.startedTest=True
		print(self.current_index)
		if(self.counter==N):
			self.current_index=self.current_index+1
			self.counter=0

		if(self.current_index==len(W)):
			self.endedTest=True

		#hack for order of rotation, switches y and z axis
		pencilRot = self.pencilTransMat.value.get_rotate_scale_corrected()

		self.error = setupEnvironment.getRotationError1D(
			pencilRot,
			self.torus1Mat.value.get_rotate_scale_corrected()
		)

		#print("P:"+str( pencilRot )+"")
		#print("T:"+str( self.torus1Mat.value.get_rotate_scale_corrected() )+"")
		if(self.current_index<len(W)):
			if self.error < W[self.current_index]/2:
				print("HIT:" + str(self.error)+"°")
				self.goal=True
				setupEnvironment.setBackgroundColor(avango.gua.Color(0, 0.2, 0.05), 0.18)
			else:
				print("MISS:" + str(self.error)+"°")
				self.goal=False
				setupEnvironment.setBackgroundColor(avango.gua.Color(0.3, 0, 0), 0.18)

		#move target
		if self.backAndForth:
			self.aimPencilMat.value = avango.gua.make_trans_mat(0, 0, -r)
			if(self.current_index<len(torus1Width)):
				self.torus1Mat.value = avango.gua.make_trans_mat(0, 0, -r)*avango.gua.make_scale_mat(torus1Width[self.current_index])
			self.backAndForth=False
		else:
			self.aimPencilMat.value = avango.gua.make_rot_mat(D,0,1,0)*avango.gua.make_trans_mat(0, 0, -r)
			self.torus1Mat.value = avango.gua.make_rot_mat(D,0,1,0)*avango.gua.make_trans_mat(0, 0, -r)*avango.gua.make_scale_mat(torus1Width[self.current_index])
			self.backAndForth=True

		if(self.evenTrial==False):
			self.time1=self.timer.value
			self.evenTrial=True
			self.setMT(self.time2, self.time1)
		else:
			self.time2=self.timer.value
			self.evenTrial=False
			self.setMT(self.time1, self.time2)

		self.counter=self.counter+1
		self.setID(self.current_index)
		self.setTP(self.current_index)
		

	def logData(self):
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
					"Aimpos: \n"+str(self.aimPencilMat.value)+"\n\n")
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
	pencil = loader.create_geometry_from_file("pointer_object_abstract", "data/objects/thin_pointer_abstract.obj", avango.gua.LoaderFlags.DEFAULTS)
	#pencil.Transform.value = avango.gua.make_scale_mat(1)#to prevent that this gets huge
	pencil.Material.value.set_uniform("Color", avango.gua.Vec4(0.6, 0.6, 0.6, 1))
	pencil.Material.value.EnableBackfaceCulling.value = False
	#pencil.Material.value.set_uniform("Emissivity", 1.0)



	pencil_transform = avango.gua.nodes.TransformNode(
		Children=[pencil]#, 
		#Transform=avango.gua.make_trans_mat(0, screenOffsetBottom, setupEnvironment.getTargetDepth())
	)

	aimPencil = loader.create_geometry_from_file("pointer_object_abstract", "data/objects/thin_pointer_abstract.obj", avango.gua.LoaderFlags.NORMALIZE_SCALE)
	aimPencil.Transform.value = avango.gua.make_trans_mat(0, 0, -r)
	aimPencil.Material.value.set_uniform("Color", avango.gua.Vec4(0.4, 0.3, 0.3, 0.5))

	torus1 = loader.create_geometry_from_file("torus", "data/objects/disk_rotated.obj", avango.gua.LoaderFlags.NORMALIZE_SCALE)
	torus1.Transform.value = avango.gua.make_trans_mat(0, 0, -r)*avango.gua.make_scale_mat(torus1Width[0])#position*size
	torus1.Material.value.set_uniform("Color", avango.gua.Vec4(0.2, 0.6, 0.3, 0.6))




	everyObject = avango.gua.nodes.TransformNode(
		Children=[aimPencil, torus1, pencil_transform], 
		Transform=avango.gua.make_trans_mat(0, screenOffsetBottom, setupEnvironment.getTargetDepth())
	)

	if setupEnvironment.space3D():
		torus2 = loader.create_geometry_from_file("torus", "data/objects/disk_rotated.obj", avango.gua.LoaderFlags.NORMALIZE_SCALE)
		torus2.Transform.value = avango.gua.make_trans_mat(r2, 0, -r1)*avango.gua.make_scale_mat(torus2Width[0])*avango.gua.make_rot_mat(90,0,1,0)#position*size
		torus2.Material.value.set_uniform("Color", avango.gua.Vec4(0.2, 0.6, 0.3, 0.6))
		everyObject.Children.value.append(torus2)

	#add nodes to root
	graph.Root.value.Children.value.append(everyObject)

	
	#listen to tracked position of pointer
	pointer_device_sensor = avango.daemon.nodes.DeviceSensor(DeviceService = avango.daemon.DeviceService())
	pointer_device_sensor.TransmitterOffset.value = setupEnvironment.getOffsetTracking()

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

	#connect torus1
	trackManager.torus1Mat.connect_from(torus1.Transform)
	torus1.Transform.connect_from(trackManager.torus1Mat)

	#timer
	timer = avango.nodes.TimeSensor()
	trackManager.timer.connect_from(timer.Time)


	setupEnvironment.launch(globals())


if __name__ == '__main__':
  start()