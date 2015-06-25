import avango
import avango.daemon
import avango.gua
import avango.script
import random
import setupEnvironment
import math

from examples_common.GuaVE import GuaVE
from avango.script import field_has_changed

r=0.15 #circle radius

#fitt's law parameter
D=40 #in degrees
ID=2 #fitt's law
W=D/(2**ID-1) #in degrees, Fitt's Law umgeformt nach W

torusWidth = r*math.tan(W*math.pi/180)

class trackingManager(avango.script.Script):
	Button = avango.SFBool()
	pencilTransMat = avango.gua.SFMatrix4()
	aimMat = avango.gua.SFMatrix4()
	torusMat = avango.gua.SFMatrix4()
	timer = avango.SFFloat()
	startedTest=False


	def __init__(self):
		self.super(trackingManager).__init__()
		self.isInside = False;
		self.startTime = 0
		self.endTime = 0
		self.aimRef = None
		self.backAndForth = False
		#self.aimRef=None

	def __del__(self):
		if setupEnvironment.logResults():
			self.result_file.close()

	@field_has_changed(Button)
	def button_pressed(self):
		if self.Button.value==True:
			self.nextSettingStep()

	@field_has_changed(pencilTransMat)
	def pencilTransMatHasChanged(self):
		pass
		#calculate error
		# currentRot = self.pencilTransMat.value.get_rotate().get_axis()*self.pencilTransMat.value.get_rotate().get_angle()

		# aimRot = self.aimMat.value.get_rotate().get_axis()*self.pencilTransMat.value.get_rotate().get_angle()

		# error = currentRot - aimRot
		# error_x_square = (currentRot[0] - aimRot[0])*(currentRot[0] - aimRot[0])
		# error_y_square = (currentRot[1] - aimRot[1])*(currentRot[1] - aimRot[1])
		# error_z_square = (currentRot[2] - aimRot[2])*(currentRot[2] - aimRot[2])
		
		# distance=math.sqrt(error_x_square+error_y_square+error_z_square)
		# if distance < 0.5:
		# 	self.inRange()
		# else: 
		# 	self.outRange()

	@field_has_changed(timer)
	def updateTimer(self):
		self.tidyMats()

		#if self.timer.value-self.startTime > 2 and self.isInside==True: #timer abbgelaufen:
		#	self.isInside = False
			
		if setupEnvironment.logResults():	
			self.logData()
			#self.aimMat.value *= avango.gua.make_trans_mat(500,0,0) 
			#getattr(self, "aimRef").Material.value.set_uniform("Color", avango.gua.Vec4(1, 1,0, 0.5)) #Transparenz funktioniert nicht
			#bewege aim an neue Stelle

	def tidyMats(self):
		#erase translation in the matrix and keep rotation and scale
		if setupEnvironment.ignoreZ():
			self.pencilTransMat.value = avango.gua.make_scale_mat(self.pencilTransMat.value.get_scale())*avango.gua.make_trans_mat(0,0,setupEnvironment.getTargetDepth())*avango.gua.make_rot_mat(self.pencilTransMat.value.get_rotate())

	def nextSettingStep(self):
		self.tidyMats()
		if self.backAndForth:
			self.aimMat.value *= avango.gua.make_rot_mat(D,1,1,0)
			self.torusMat.value = avango.gua.make_rot_mat(0,0,0,1)*avango.gua.make_trans_mat(0, r, setupEnvironment.getTargetDepth())*avango.gua.make_scale_mat(torusWidth)
			self.backAndForth=False
		else:
			self.aimMat.value *= avango.gua.make_rot_mat(-D,1,1,0)
			self.torusMat.value = avango.gua.make_trans_mat(0, 0, setupEnvironment.getTargetDepth())*avango.gua.make_rot_mat(D,-1,0,1)*avango.gua.make_trans_mat(0, r, 0)*avango.gua.make_scale_mat(torusWidth)
			self.backAndForth=True

	def logData(self):
		path="results/results_pointing_2D/"
		if(self.startedTest and self.endedTest==False):
			if self.created_file==False: #create File 
				self.num_files=len([f for f in os.listdir(path)
					if os.path.isfile(os.path.join(path, f))])
				self.created_file=True
			else: #write permanent values
				self.result_file=open(path+"pointing2D_trial"+str(self.num_files)+".txt", "a+")
				
				self.result_file.write(
					"TimeStamp: "+str(self.timer.value)+"\n"
					"Error: "+str(self.error)+"\n"
					"Pointerpos: \n"+str(self.TransMat.value)+"\n"
					"Homepos: \n"+str(self.HomeMat.value)+"\n\n")
				self.result_file.close()
			
				if self.Button.value: #write resulting values
					self.result_file=open(path+"pointing2D_trial"+str(self.num_files)+".txt", "a+")
					if(self.flagPrinted==False):
						self.result_file.write(
							"MT: "+str(self.MT)+"\n"+
							"ID: "+str(self.ID)+"\n"+
							"TP: "+str(self.TP)+"\n"+
							"Total Error: "+str(self.error)+"\n"+
							"=========================\n\n")
						self.flagPrinted=True
					self.result_file.close()

def handle_key(key, scancode, action, mods):
	if action == 0:
		#32 is space 335 is num_enter
		if key == 335:
			trackManager.nextSettingStep()

trackManager = trackingManager()
def start ():
	graph=avango.gua.nodes.SceneGraph(Name="scenegraph") #Create Graph
	loader = avango.gua.nodes.TriMeshLoader() #Create Loader

	#Meshes
	pencil = loader.create_geometry_from_file("tracked_object", "data/objects/tracked_object.obj", avango.gua.LoaderFlags.NORMALIZE_SCALE)
	pencil.Transform.value= avango.gua.make_rot_mat(180, 1, 0, 0)*avango.gua.make_scale_mat(0.02)
	pencil.Material.value.set_uniform("Color", avango.gua.Vec4(0.5, 0.5, 0.5, 0.5))

	pencil_transform=avango.gua.nodes.TransformNode(Children=[pencil])

	aim = loader.create_geometry_from_file("tracked_object", "data/objects/tracked_object.obj", avango.gua.LoaderFlags.NORMALIZE_SCALE)
	aim.Transform.value = avango.gua.make_trans_mat(0,0,setupEnvironment.getTargetDepth())*avango.gua.make_scale_mat(0.02)*avango.gua.make_rot_mat(-90,1,0,0)
	aim.Material.value.set_uniform("Color", avango.gua.Vec4(0.4, 0.3, 0.3, 0.5))

	torus = loader.create_geometry_from_file("torus", "data/objects/torus.obj", avango.gua.LoaderFlags.NORMALIZE_SCALE)
	torus.Transform.value = avango.gua.make_trans_mat(0, r, setupEnvironment.getTargetDepth())*avango.gua.make_scale_mat(torusWidth)#position*size
	torus.Material.value.set_uniform("Color", avango.gua.Vec4(0.2, 0.6, 0.3, 0.6))


	setupEnvironment.getWindow().on_key_press(handle_key)
	setupEnvironment.setup(graph)

	#add nodes to root
	graph.Root.value.Children.value.extend([aim, torus, pencil_transform])

	#listen to tracked position of pointer
	pointer_device_sensor = avango.daemon.nodes.DeviceSensor(DeviceService = avango.daemon.DeviceService())
	pointer_device_sensor.TransmitterOffset.value = setupEnvironment.getOffsetTracking()

	pointer_device_sensor.Station.value = "pointer"

	trackManager.pencilTransMat.connect_from(pointer_device_sensor.Matrix)

	#connect pencil
	pencil_transform.Transform.connect_from(trackManager.pencilTransMat)

	#listen to button
	button_sensor=avango.daemon.nodes.DeviceSensor(DeviceService=avango.daemon.DeviceService())
	button_sensor.Station.value="device-pointer"

	trackManager.Button.connect_from(button_sensor.Button0)

	#connect aim
	trackManager.aimRef = aim
	trackManager.aimMat.connect_from(aim.Transform)
	aim.Transform.connect_from(trackManager.aimMat)

	#connect torus
	trackManager.torusMat.connect_from(torus.Transform)
	torus.Transform.connect_from(trackManager.torusMat)

	#timer
	timer = avango.nodes.TimeSensor()
	trackManager.timer.connect_from(timer.Time)


	setupEnvironment.launch()

if __name__ == '__main__':
  start()