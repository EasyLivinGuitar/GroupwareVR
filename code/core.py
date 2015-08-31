import avango
import avango.daemon
import avango.gua
import avango.script
import avango.sound
import avango.sound.openal
import math

from examples_common.GuaVE import GuaVE
from avango.script import field_has_changed

'''
Written by Benedikt Vogler and Marcel Gohsen

How to setup a new test case:

1. use getWindow() to setup the key events
2. call setup()
3. call launch()

Then start the scene with the according start.sh
'''


'''Settings'''
class setupEnvironment(avango.script.Script):

	#here you can canfigure the number of the test
	testConfigNo = 5

	#task config
	'''disable translation on this axis'''
	disableAxisList = [[0,0,0],[0,1,1],[0,1,1],[0,1,0],[0,1,0],[1,1,1],[1,1,1],[1,1,1],[0,0,0],[0,1,0]]#x,y,z
	disableAxis = disableAxisList[testConfigNo]

	'''if one rotation axis should be locked/disabled. Switches beetween 3 and 1 DOF'''
	virtualDOFRotateList = [3,3,3,3,3,3,1,1,3,1]
	virtualDOFRotate = virtualDOFRotateList[testConfigNo]

	'''should the task swich between rotation aims using 3  or 1 DOF or disable it =0?'''
	taskDOFRotateList = [0,0,0,0,0,3,1,1,3,1]
	taskDOFRotate = taskDOFRotateList[testConfigNo]

	if virtualDOFRotate == 1 and taskDOFRotate>1:
		taskDOFRotate = 1

	'''is the task above the table or is it on the table?'''
	space3DList = [True, False, True, False, True, True, False, True, True, False]
	space3D = space3DList[testConfigNo]

	#the amount of trials per ID
	N=8

	#setup
	ID =[4, 5, 6] #fitt's law

	''' difference from screen center to center of tracking'''
	offsetTracking = avango.gua.make_trans_mat(0.0, -0.34, 0.70)

	'''get the offsets of the pointer.'''
	offsetPointer = avango.gua.make_trans_mat(0.0, 0, 0.30)

	'''get the position of the center where the pointer and the aim is located.'''
	displayPosition = avango.gua.make_trans_mat(0.0, 0, .30)

	logResults = True
	saveReplay = True

	'''if false needs a button press or next step, if true then autodetects'''
	useAutoDetect =  False

	randomTargets = False

	'''radius of spikes from center in the model file'''
	r_model=0.10

	'''radius of spikes displayed'''
	r = 0.20

	'''highlight if inside the target'''
	showWhenInTarget = True

	res_pass = avango.gua.nodes.ResolvePassDescription()

	viewer = avango.gua.nodes.Viewer()
	viewer.DesiredFPS.value=60
	resolution = avango.gua.Vec2ui(1920, 1080)
	#screenSize = avango.gua.Vec2(1.235, 0.695) # in meters
	window = avango.gua.nodes.GlfwWindow(
			Size=resolution,
			LeftResolution=resolution,
			RightResolution=resolution,
			StereoMode = avango.gua.StereoMode.CHECKERBOARD
	)

	#sound
	soundtraverser = avango.sound.nodes.SoundTraverser()
	soundRenderer = avango.sound.openal.nodes.OpenALSoundRenderer()
	soundRenderer.Device.value = ""
	soundtraverser.Renderers.value = [soundRenderer]

	hitRotateSound = avango.sound.nodes.SoundSource()
	levelUpSound = avango.sound.nodes.SoundSource()
	balloonSound = avango.sound.nodes.SoundSource()
	missSound = avango.sound.nodes.SoundSource()

	loader = avango.gua.nodes.TriMeshLoader() #Create Loader

	everyObject = avango.gua.nodes.TransformNode(
		Children = [], 
		Transform = displayPosition
	)

	timeSensor = avango.nodes.TimeSensor()
	timerField = avango.SFFloat()

	def __init__(self):
		self.super(setupEnvironment).__init__()
		self.timeTillBlack = 0
		self.permanentBG = False
		self.timerField.connect_from(self.timeSensor.Time)


	'''Get the degrees of freedom on the translation virtually'''
	def getDOFTranslateVirtual(self):
		return 3-self.disableAxis[0]-self.disableAxis[1]-self.disableAxis[2]
	
	def getDOFTranslateReal(self):
		if self.space3D:
			return 3
		else: 
			return 1


	def print_graph(root_node):
		stack = [ ( root_node, 0) ]
		while stack:
			node, level = stack.pop()
			print("│   " * level + "├── {0} <{1}>".format(node.Name.value, node.__class__.__name__))
			stack.extend( [ (child, level + 1) for child in reversed(node.Children.value) ] )

	def setup(self, graph):
		light = avango.gua.nodes.LightNode(
			Type=avango.gua.LightType.POINT,
			Name="light",
			Color=avango.gua.Color(1.0, 1.0, 1.0),
			Brightness=100.0,
			Transform=(avango.gua.make_trans_mat(1, 1, 5) *
					   avango.gua.make_scale_mat(30, 30, 30))
			)

		avango.gua.register_window("window", self.window)

		self.cam = avango.gua.nodes.CameraNode(
			LeftScreenPath="/screen",
			RightScreenPath="/screen",
			SceneGraph="scenegraph",
			Resolution=self.resolution,
			EyeDistance = 0.064,
			EnableStereo = True,
			OutputWindowName="window",
			Transform = avango.gua.make_trans_mat(0.0, 0.0, 3.5)
		)
		screen = avango.gua.nodes.ScreenNode(
			Name="screen",
			Width=1.445,
			Height=0.81,
			Children=[self.cam]
		)

		#Sieht netter aus
		self.res_pass.EnableSSAO.value = True
		self.res_pass.SSAOIntensity.value = 4.0
		self.res_pass.SSAOFalloff.value = 10.0
		self.res_pass.SSAORadius.value = 7.0

		#self.res_pass.EnableScreenSpaceShadow.value = True

		self.res_pass.EnvironmentLightingColor.value = avango.gua.Color(0.1, 0.1, 0.1)
		self.res_pass.ToneMappingMode.value = avango.gua.ToneMappingMode.UNCHARTED
		self.res_pass.Exposure.value = 1.0
		self.res_pass.BackgroundColor.value = avango.gua.Color(0, 0, 0)

		anti_aliasing = avango.gua.nodes.SSAAPassDescription()

		pipeline_description = avango.gua.nodes.PipelineDescription(
			Passes=[
				avango.gua.nodes.TriMeshPassDescription(),
				avango.gua.nodes.LightVisibilityPassDescription(),
				self.res_pass,
				anti_aliasing,
			]
		)

		self.cam.PipelineDescription.value = pipeline_description
		self.cam.PipelineDescription.value.EnableABuffer.value=True

		#Setup headtracking
		self.head_device_sensor = avango.daemon.nodes.DeviceSensor(DeviceService = avango.daemon.DeviceService())
		self.head_device_sensor.TransmitterOffset.value = self.offsetTracking

		self.head_device_sensor.Station.value = "glasses"

		self.cam.Transform.connect_from(self.head_device_sensor.Matrix)


		graph.Root.value.Children.value=[light, screen]

		self.soundtraverser.RootNode.value = graph.Root.value
		self.soundtraverser.Traverse.value = True

		self.soundRenderer.ListenerPosition.connect_from(self.cam.Transform)

		self.balloonSound.URL.value = "data/sounds/balloon_pop.ogg"
		self.balloonSound.Loop.value = False
		self.balloonSound.Play.value = True
		graph.Root.value.Children.value.extend([self.balloonSound])

		self.hitRotateSound.URL.value = "data/sounds/hit_rotate.wav"
		self.hitRotateSound.Loop.value = False
		self.hitRotateSound.Play.value = True
		graph.Root.value.Children.value.extend([self.hitRotateSound])

		self.levelUpSound.URL.value = "data/sounds/level_up.wav"
		self.levelUpSound.Loop.value = False
		self.levelUpSound.Play.value = True
		graph.Root.value.Children.value.extend([self.levelUpSound])

		self.missSound.URL.value = "data/sounds/miss.ogg"
		self.missSound.Loop.value = False
		self.missSound.Play.value = True
		graph.Root.value.Children.value.extend([self.missSound])

		#setup viewer
		self.viewer.SceneGraphs.value = [graph]
		self.viewer.Windows.value = [self.window]

		graph.Root.value.Children.value.append(self.everyObject)


	@field_has_changed(timerField)
	def update(self):
		#print("Update: " +str(self.timeTillBlack))
		if (not self.permanentBG) and (self.timerField.value >= self.timeTillBlack):
			#print("back to black: "+str(self.timerField.value) + " >= " + str(self.timeTillBlack))
			self.res_pass.BackgroundColor.value = avango.gua.Color(0, 0, 0)

	def getWindow(self):
		return self.window

	def launch(self, otherlocals):
		print("Launch")
		guaVE = GuaVE()
		z = globals().copy()
		z.update(otherlocals)
		guaVE.start(locals(), z)
			
		self.viewer.run()


	def setBackgroundColor(self, color, time=0):
		if time > 0:
			self.timeTillBlack = self.timeSensor.Time.value + time #aktuelle Zeit plus Zeit
			self.permanentBG = False
		else:
			self.permanentBG = True
		self.res_pass.BackgroundColor.value=color


	def playSound(self, sound):
		if (sound == "balloon"):
			self.balloonSound.Play.value = True
		else:
			if (sound == "miss"):
				self.missSound.Play.value = True
			else:
				if sound == "hit_rotate":
					self.hitRotateSound.Play.value = True
				else:
					if sound == "levelUp":
				 		self.levelUpSound.Play.value = True

##
# @param ID the index of difficulty
# @param A the amplitude
def IDtoW(ID, A):
	return (2*A) / (2**ID)

## Converts a rotation matrix to the Euler angles yaw, pitch and roll.
# @param q The rotation quat to be converted.
def get_euler_angles(q):
  sqx = q.x * q.x
  sqy = q.y * q.y
  sqz = q.z * q.z
  sqw = q.w * q.w

  unit = sqx + sqy + sqz + sqw # if normalised is one, otherwise is correction factor
  test = (q.x * q.y) + (q.z * q.w)

  if test > 1:
    yaw = 0.0
    roll = 0.0
    pitch = 0.0

  if test > (0.49999 * unit): # singularity at north pole
    yaw = 2.0 * math.atan2(q.x,q.w)
    roll = math.pi/2.0
    pitch = 0.0
  elif test < (-0.49999 * unit): # singularity at south pole
    yaw = -2.0 * math.atan2(q.x,q.w)
    roll = math.pi/-2.0
    pitch = 0.0
  else:
    yaw = math.atan2(2.0 * q.y * q.w - 2.0 * q.x * q.z, 1.0 - 2.0 * sqy - 2.0 * sqz)
    roll = math.asin(2.0 * test)
    pitch = math.atan2(2.0 * q.x * q.w - 2.0 * q.y * q.z, 1.0 - 2.0 * sqx - 2.0 * sqz)

  if yaw < 0.0:
    yaw += 2.0 * math.pi

  if pitch < 0:
    pitch += 2 * math.pi

  if roll < 0:
    roll += 2 * math.pi

  return yaw, pitch, roll 

def getRotationError3D(aMat,bMat):
	#quaternion to euler has an error with the z axis
	a = aMat.get_rotate_scale_corrected()
	a.normalize()
	
	aEuler = get_euler_angles(a)
	

	b = bMat.get_rotate_scale_corrected()
	b.normalize()

	#hack to make the error fit
	b.y = b.z
	b.z =   0
	
	bEuler = get_euler_angles(b)

	error =[
		(aEuler[0]-bEuler[0])*180/math.pi, #Y
		(aEuler[1]-bEuler[1])*180/math.pi, #?
		(aEuler[2]-bEuler[2])*180/math.pi, #?
		0 #gesamt
	]
	error[3]=math.sqrt(error[0]*error[0]+error[1]*error[1]+error[2]*error[2])
	
	'''
	print("P: "+str(a))
	print("T: "+str(b))
	error = math.acos(2*(a.x*b.x+a.y*b.y+a.z*b.z+a.w*b.w)**2-1)
	error *=180/math.pi
	'''
	return error

'''
get rotation error between two rotations
'''
def getRotationError1D(rotA, rotB):
	matA = avango.gua.make_rot_mat(rotA)
	matB = avango.gua.make_rot_mat(rotB)

	diffRotMat = avango.gua.make_inverse_mat(matA)*matB
	return diffRotMat.get_rotate_scale_corrected().get_angle()


def getDistance2D(target1, target2):
	trans_x=target1.get_translate()[0]
	trans_y=target1.get_translate()[1]

	aim_x=target2.get_translate()[0]
	aim_y=target2.get_translate()[1]

	trans_aim_x_square=(trans_x - aim_x)*(trans_x - aim_x)
	trans_aim_y_square=(trans_y - aim_y)*(trans_y - aim_y)
	
	return math.sqrt(trans_aim_x_square+trans_aim_y_square)

def getDistance3D(target1, target2):
	trans_x=target1.get_translate()[0]
	trans_y=target1.get_translate()[1]
	trans_z=target1.get_translate()[2]

	aim_x=target2.get_translate()[0]
	aim_y=target2.get_translate()[1]
	aim_z=target2.get_translate()[2]
	
	return math.sqrt((trans_x - aim_x)**2+(trans_y - aim_y)**2+(trans_z - aim_z)**2)

class PencilContainer(avango.script.Script):
	pencil = None
	inputMat = avango.gua.SFMatrix4()
	loader = avango.gua.nodes.TriMeshLoader()

	def __init__(self):
		self.super(PencilContainer).__init__()

	def create(self, setup):
		self.setup = setup
		self.pencil = self.loader.create_geometry_from_file("colored_cross", "data/objects/colored_cross.obj", avango.gua.LoaderFlags.DEFAULTS |  avango.gua.LoaderFlags.LOAD_MATERIALS)
		self.pencil.Transform.value = setup.offsetPointer*avango.gua.make_scale_mat(self.setup.r/self.setup.r_model)
		#pencil.Transform.value = avango.gua.make_scale_mat(1)#to prevent that this gets huge
		#pencil.Material.value.set_uniform("Color", avango.gua.Vec4(0.6, 0.6, 0.6, 1))
		#pencil.Material.value.set_uniform("Emissivity", 1.0)
		
		#listen to tracked position of pointer
		self.pointer_device_sensor = avango.daemon.nodes.DeviceSensor(DeviceService = avango.daemon.DeviceService())
		self.pointer_device_sensor.TransmitterOffset.value = self.setup.offsetTracking

		self.pointer_device_sensor.Station.value = "pointer"

		self.inputMat.connect_from(self.pointer_device_sensor.Matrix)
		#connect pencil
		self.setup.everyObject.Children.value.append(self.pencil)
		return self


	@field_has_changed(inputMat)
	def pointermat_changed(self):
		#get input
		self.pencil.Transform.value = self.setup.offsetPointer*self.inputMat.value * avango.gua.make_scale_mat(self.pencil.Transform.value.get_scale())
		#then reduce
		self.reducePencilMat()
		#print(self.inputMat.value)

	def getNode(self):
		return self.pencil

	def getTransfromValue(self):
		return self.pencil.Transform.value

	'''reduce a transform matrix according to the constrainst '''
	def reducePencilMat(self):
		if self.setup.virtualDOFRotate==1:
			#erase 2dof at table, unstable operation, calling this twice destroys the rotation information
			#get angle between rotation and y axis
			q = self.pencil.Transform.value.get_rotate_scale_corrected()
			q.z = 0 #tried to fix to remove roll
			q.x = 0 #tried to fix to remove roll
			q.normalize()
			yRot = avango.gua.make_rot_mat(get_euler_angles(q)[0]*180.0/math.pi,0,1,0)#get euler y rotation, has also roll in it
		else:
			yRot = avango.gua.make_rot_mat(self.getTransfromValue().get_rotate_scale_corrected())

		if self.setup.disableAxis[0]:
			x = 0
		else:
			x = self.getTransfromValue().get_translate().x - self.setup.offsetTracking.get_translate().x

		if self.setup.disableAxis[1]:
			y = 0
		else:
			if self.setup.space3D:# on table?
				y = self.getTransfromValue().get_translate().y
			else:
				y = self.getTransfromValue().get_translate().y-self.setup.offsetTracking.get_translate().y

		if self.setup.disableAxis[2]:
			z = 0
		else:
			z = self.getTransfromValue().get_translate().z - self.setup.offsetTracking.get_translate().z

		translation = avango.gua.make_trans_mat(
			x,
			y,
			z
		)

		self.pencil.Transform.value = translation * yRot * avango.gua.make_scale_mat(self.pencil.Transform.value.get_scale())		

class DisksContainer():
		
		def __init__(self, setEnv):
			self.disk1 = None
			self.disk2 = None
			self.disk3 = None
			self.disk4 = None
			self.disk5 = None
			self.disk6 = None
			self.node = None
			self.setup = setEnv

		'''for attaching the disk to the pointer, the pointer is needed'''
		def setupDisks(self, pencilNode):
			#attack disks to pointer
			self.node = avango.gua.nodes.TransformNode(
				Transform = avango.gua.make_trans_mat(pencilNode.Transform.value.get_translate())
			)

			self.disk1 = self.setup.loader.create_geometry_from_file("disk", "data/objects/disk_rotated.obj", avango.gua.LoaderFlags.NORMALIZE_SCALE)
			self.node.Children.value.append(self.disk1)
			
			self.disk2 = self.setup.loader.create_geometry_from_file("cylinder", "data/objects/disk_rotated.obj", avango.gua.LoaderFlags.NORMALIZE_SCALE)
			self.node.Children.value.append(self.disk2)

			self.disk3 = self.setup.loader.create_geometry_from_file("cylinder", "data/objects/disk_rotated.obj", avango.gua.LoaderFlags.NORMALIZE_SCALE)
			self.node.Children.value.append(self.disk3)

			self.disk6 = self.setup.loader.create_geometry_from_file("cylinder", "data/objects/disk_rotated.obj", avango.gua.LoaderFlags.NORMALIZE_SCALE)
			self.node.Children.value.append(self.disk6)

			if self.setup.virtualDOFRotate==3:
				self.disk4 = self.setup.loader.create_geometry_from_file("cylinder", "data/objects/disk_rotated.obj", avango.gua.LoaderFlags.NORMALIZE_SCALE)
				self.node.Children.value.append(self.disk4)
		
				self.disk5 = self.setup.loader.create_geometry_from_file("cylinder", "data/objects/disk_rotated.obj", avango.gua.LoaderFlags.NORMALIZE_SCALE)
				self.node.Children.value.append(self.disk5)


			self.setup.everyObject.Children.value.append(self.node)
			return self.node

		'''setup the position of the disk inside the container'''
		def setDisksTransMats(self, diam):
			# print("scaling to"+str(diam))
			self.disk1.Transform.value = avango.gua.make_trans_mat(0, 0, -self.setup.r)*avango.gua.make_scale_mat(diam)
			self.disk3.Transform.value = avango.gua.make_rot_mat(90,0,1,0) *avango.gua.make_trans_mat(0, 0, -self.setup.r)*avango.gua.make_scale_mat(diam)	
			self.disk2.Transform.value = avango.gua.make_rot_mat(-90,0,1,0)*avango.gua.make_trans_mat(0, 0, -self.setup.r)*avango.gua.make_scale_mat(diam)
			self.disk6.Transform.value = avango.gua.make_rot_mat(180,0,1,0)*avango.gua.make_trans_mat(0, 0, -self.setup.r)*avango.gua.make_scale_mat(diam)

			if self.setup.virtualDOFRotate==3:
				self.disk5.Transform.value = avango.gua.make_rot_mat(-90,1,0,0)*avango.gua.make_trans_mat(0, 0, -self.setup.r)*avango.gua.make_scale_mat(diam)
				self.disk4.Transform.value = avango.gua.make_rot_mat(90,1,0,0) *avango.gua.make_trans_mat(0, 0, -self.setup.r)*avango.gua.make_scale_mat(diam)

		def setRotation(self, rotMat):
			self.node.Transform.value = avango.gua.make_trans_mat( self.node.Transform.value.get_translate() ) * rotMat *avango.gua.make_scale_mat(self.node.Transform.value.get_scale())
			
		def setTranslate(self, transl):
			self.node.Transform.value = transl * avango.gua.make_rot_mat(self.node.Transform.value.get_rotate_scale_corrected())*avango.gua.make_scale_mat(self.node.Transform.value.get_scale())
		
		def getRotate(self):
			return self.node.Transform.value.get_rotate_scale_corrected()

		def highlightRed(self):
			self.disk1.Material.value.set_uniform("Color", avango.gua.Vec4(0.2, 0.0, 0.9, 0.6))
			self.disk2.Material.value.set_uniform("Color", avango.gua.Vec4(1.0, 0.0, 0.0, 0.6))
			self.disk3.Material.value.set_uniform("Color", avango.gua.Vec4(0.7, 0.4, 0.4, 0.6))
			self.disk6.Material.value.set_uniform("Color", avango.gua.Vec4(0.7, 0.4, 0.4, 0.6))

			if self.setup.virtualDOFRotate==3:
				self.disk4.Material.value.set_uniform("Color", avango.gua.Vec4(0.4, 0.9, 0.0, 0.6))
				self.disk5.Material.value.set_uniform("Color", avango.gua.Vec4(0.7, 0.4, 0.4, 0.6))

		def setColor(self):
			self.disk1.Material.value.set_uniform("Color", avango.gua.Vec4(0.0, 0.0, 1.0, 0.6))
			self.disk2.Material.value.set_uniform("Color", avango.gua.Vec4(1.0, 0.0, 0.0, 0.6))
			self.disk3.Material.value.set_uniform("Color", avango.gua.Vec4(0.5, 0.5, 0.5, 0.6))
			self.disk6.Material.value.set_uniform("Color", avango.gua.Vec4(0.5, 0.5, 0.5, 0.6))

			if self.setup.virtualDOFRotate==3:
				self.disk4.Material.value.set_uniform("Color", avango.gua.Vec4(0.0, 1.0, 0.0, 0.6))
				self.disk5.Material.value.set_uniform("Color", avango.gua.Vec4(0.5, 0.5, 0.5, 0.6))