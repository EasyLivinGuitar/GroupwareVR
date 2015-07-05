import avango
import avango.daemon
import avango.gua
import avango.script
import random
import setupEnvironment
import math

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

targetDiameter = [2*r*math.tan(W[0]/2*math.pi/180), 2*r*math.tan(W[1]/2*math.pi/180), 2*r*math.tan(W[2]/2*math.pi/180)]#größe (Druchmesser) der Gegenkathete auf dem kreisumfang

graph = avango.gua.nodes.SceneGraph(Name="scenegraph") #Create Graph
loader = avango.gua.nodes.TriMeshLoader() #Create Loader
pencil_transform = avango.gua.nodes.TransformNode()
aimPencil = avango.gua.nodes.TransformNode()

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
			self.pencilTransMat.value = avango.gua.make_trans_mat(0,0,0)*avango.gua.make_rot_mat(self.pencilTransMat.value.get_rotate())

	def nextSettingStep(self):
		self.startedTest=True
		print(self.current_index)
		self.error = setupEnvironment.getRotationError1D(
			self.pencilTransMat.value.get_rotate_scale_corrected(),
			self.torusMat.value.get_rotate_scale_corrected()
		)

		print("P:"+str( self.pencilTransMat.value.get_rotate_scale_corrected() )+"")
		print("T:"+str( self.torusMat.value.get_rotate_scale_corrected() )+"")
		print("Error Gesamt:"+str( self.error )+"°")

		if self.error < W/2:
			print("HIT:" + str(self.error)+"°")
			setupEnvironment.setBackgroundColor(avango.gua.Color(0, 0.2, 0.05), 0.18)
		else:
			print("MISS:" + str(self.error)+"°")
			setupEnvironment.setBackgroundColor(avango.gua.Color(0.3, 0, 0), 0.18)

		if self.backAndForth:
			self.aimMat.value = (
				avango.gua.make_trans_mat(0, 0, 0)
				*avango.gua.make_rot_mat(D,-1,0,1)
				*avango.gua.make_rot_mat(90,1,0,0)
			)
			self.torusMat.value = (
				avango.gua.make_trans_mat(0, 0, 0)
				*avango.gua.make_rot_mat(D,-1,0,1)
				*avango.gua.make_rot_mat(90,1,0,0)
				*avango.gua.make_trans_mat(0, 0, -r)
				*avango.gua.make_scale_mat(targetDiameter[self.current_index])
			)
			self.backAndForth=False
		else:
			self.aimMat.value = (
				avango.gua.make_trans_mat(0, 0, 0)
				#*avango.gua.make_rot_mat(D,-1,0,1)
				*avango.gua.make_rot_mat(90,1,0,0)
			)
			self.torusMat.value = (
				avango.gua.make_trans_mat(0, 0, 0)
				#*avango.gua.make_rot_mat(D,-1,0,1)
				*avango.gua.make_rot_mat(90,1,0,0)
				*avango.gua.make_trans_mat(0, 0, -r)
				*avango.gua.make_scale_mat(targetDiameter[self.current_index])
			)
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
	if action == 1:
		#32 is space 335 is num_enter
		if key==32 or key==335:
			trackManager.nextSettingStep()

trackManager = trackingManager()
def start ():

	setupEnvironment.getWindow().on_key_press(handle_key)
	setupEnvironment.setup(graph)

	#loadMeshes
	pencil = loader.create_geometry_from_file("tracked_object", "data/objects/thin_pointer_abstract.obj", avango.gua.LoaderFlags.NORMALIZE_SCALE)
	pencil.Transform.value = avango.gua.make_scale_mat(1)#to prevent that this gets huge
	pencil.Material.value.set_uniform("Color", avango.gua.Vec4(0.5, 0.5, 0.5, 0.5))

	pencil_transform=avango.gua.nodes.TransformNode(Children=[pencil])

	aim = loader.create_geometry_from_file("tracked_object", "data/objects/thin_pointer_abstract.obj", avango.gua.LoaderFlags.NORMALIZE_SCALE)
	aim.Transform.value = avango.gua.make_trans_mat(0,0,0)*avango.gua.make_rot_mat(-90,1,0,0)*avango.gua.make_rot_mat(180, 0, 1, 0)*avango.gua.make_rot_mat(180, 0, 0, 1)
	aim.Material.value.set_uniform("Color", avango.gua.Vec4(0.4, 0.3, 0.3, 0.5))

	torus = loader.create_geometry_from_file("torus", "data/objects/torus_rotated.obj", avango.gua.LoaderFlags.NORMALIZE_SCALE)
	torus.Transform.value = (
				avango.gua.make_trans_mat(0, 0, 0)
				#*avango.gua.make_rot_mat(D,-1,0,1)
				*avango.gua.make_rot_mat(-90,1,0,0)
				*avango.gua.make_trans_mat(0, 0, r)
				*avango.gua.make_scale_mat(targetDiameter[0])
			)
	torus.Material.value.set_uniform("Color", avango.gua.Vec4(0.2, 0.6, 0.3, 0.6))

	#add nodes to root
	graph.Root.value.Children.value.extend([aim, torus, pencil_transform])

	
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


	setupEnvironment.launch(globals())

if __name__ == '__main__':
  start()