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

'''if one axis should be locked.  TODO: make it an interger'''
reduceDOFTranslate = False

'''if one rotation axis should be locked. TODO: make it an interger'''
reduceDOFRotate = False

'''is the task above the table or is it on the table?'''
space3D = True

offsetTracking =  avango.gua.make_trans_mat(0.0, -0.14 - 0.405, 0.68)

'''get the position pf the cetner where the pointer and the aim is located'''
centerPosition =  avango.gua.make_trans_mat(0.0, 0, 0.38)

logResults = True

'''if true needs a button press or next step, if false then autodetects'''
useAutoDetect =  False

randomTargets = False

'''radius of spikes'''
r=0.10



timer=avango.nodes.TimeSensor()

res_pass = avango.gua.nodes.ResolvePassDescription()

viewer = avango.gua.nodes.Viewer()
viewer.DesiredFPS.value=60
resolution = avango.gua.Vec2ui(1920, 1080)
#screenSize = avango.gua.Vec2(1.235, 0.695) # in meters
screenSize = avango.gua.Vec2(1.445, 0.81) # in meters
window = avango.gua.nodes.GlfwWindow(
		Size=resolution,
		LeftResolution=resolution,
		RightResolution=resolution,
		StereoMode=avango.gua.StereoMode.CHECKERBOARD
		)

#sound
soundtraverser = avango.sound.nodes.SoundTraverser()
soundRenderer = avango.sound.openal.nodes.OpenALSoundRenderer()
soundRenderer.Device.value = ""
soundtraverser.Renderers.value = [soundRenderer]
balloonSound = avango.sound.nodes.SoundSource()
missSound = avango.sound.nodes.SoundSource()

loader = avango.gua.nodes.TriMeshLoader() #Create Loader

def print_graph(root_node):
	stack = [ ( root_node, 0) ]
	while stack:
		node, level = stack.pop()
		print("│   " * level + "├── {0} <{1}>".format(node.Name.value, node.__class__.__name__))
		stack.extend( [ (child, level + 1) for child in reversed(node.Children.value) ] )

def setup(graph):
	light = avango.gua.nodes.LightNode(
		Type=avango.gua.LightType.POINT,
		Name="light",
		Color=avango.gua.Color(1.0, 1.0, 1.0),
		Brightness=100.0,
		Transform=(avango.gua.make_trans_mat(1, 1, 5) *
				   avango.gua.make_scale_mat(30, 30, 30))
		)

	avango.gua.register_window("window", window)

	cam = avango.gua.nodes.CameraNode(
		LeftScreenPath="/screen",
		RightScreenPath="/screen",
		SceneGraph="scenegraph",
		Resolution=resolution,
		EyeDistance = 0.064,
		EnableStereo = True,
		OutputWindowName="window",
		Transform = avango.gua.make_trans_mat(0.0, 0.0, 3.5),
		BlackList = ["invisible"]
	)
	screen = avango.gua.nodes.ScreenNode(
		Name="screen",
		Width=screenSize.x,
		Height=screenSize.y,
		Children=[cam]
	)

	#Sieht netter aus
	res_pass.EnableSSAO.value = True
	res_pass.SSAOIntensity.value = 4.0
	res_pass.SSAOFalloff.value = 10.0
	res_pass.SSAORadius.value = 7.0

	#res_pass.EnableScreenSpaceShadow.value = True

	res_pass.EnvironmentLightingColor.value = avango.gua.Color(0.1, 0.1, 0.1)
	res_pass.ToneMappingMode.value = avango.gua.ToneMappingMode.UNCHARTED
	res_pass.Exposure.value = 1.0
	res_pass.BackgroundColor.value = avango.gua.Color(0, 0, 0)

	anti_aliasing = avango.gua.nodes.SSAAPassDescription()

	pipeline_description = avango.gua.nodes.PipelineDescription(
		Passes=[
			avango.gua.nodes.TriMeshPassDescription(),
			avango.gua.nodes.LightVisibilityPassDescription(),
			res_pass,
			anti_aliasing,
		]
	)

	cam.PipelineDescription.value = pipeline_description
	cam.PipelineDescription.value.EnableABuffer.value=True

	#Setup headtracking
	head_device_sensor = avango.daemon.nodes.DeviceSensor(DeviceService = avango.daemon.DeviceService())
	head_device_sensor.TransmitterOffset.value = offsetTracking

	head_device_sensor.Station.value = "glasses"

	cam.Transform.connect_from(head_device_sensor.Matrix)


	graph.Root.value.Children.value=[light, screen]

	soundtraverser.RootNode.value = graph.Root.value
	soundtraverser.Traverse.value = True

	soundRenderer.ListenerPosition.connect_from(cam.Transform)

	balloonSound.URL.value = "data/sounds/balloon_pop.ogg"
	balloonSound.Loop.value = False
	balloonSound.Play.value = True
	graph.Root.value.Children.value.extend([balloonSound])

	missSound.URL.value = "data/sounds/miss.ogg"
	missSound.Loop.value = False
	missSound.Play.value = True
	graph.Root.value.Children.value.extend([missSound])

	#setup viewer
	viewer.SceneGraphs.value = [graph]
	viewer.Windows.value = [window]

class FieldManager(avango.script.Script):
	TransMat = avango.gua.SFMatrix4()
	timer= avango.SFFloat()
	time= 0

	def __init__(self):

		self.super(FieldManager).__init__()
	
	@field_has_changed(TransMat)
	def transMatHasChanged(self):
		print(self.TransMat.value)

	@field_has_changed(timer)
	def update(self):
		if(self.timer.value>=self.time):
			res_pass.BackgroundColor.value=avango.gua.Color(0, 0, 0)

manager=FieldManager()
manager.timer.connect_from(timer.Time)

def getWindow():
	return window

def launch(otherlocals):
	print("Launch")
	guaVE = GuaVE()
	z = globals().copy()
	z.update(otherlocals)
	guaVE.start(locals(), z)
		
	viewer.run()

def setBackgroundColor(color, time):
	manager.time=timer.Time.value+time
	
	res_pass.BackgroundColor.value=color

def playSound(sound):
	if (sound == "balloon"):
		balloonSound.Play.value = True
	else:
		if (sound == "miss"):
			missSound.Play.value = True


## Converts a rotation matrix to the Euler angles yaw, pitch and roll.
# @param MATRIX The rotation matrix to be converted.
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
	print("P:"+str(a)+" => "+str(aEuler))
	

	b = bMat.get_rotate_scale_corrected()
	b.normalize()

	#hack to make the error fit
	b.y = b.z
	b.z =   0
	
	bEuler = get_euler_angles(b)
	print("T:"+str(b)+" => "+str(bEuler))

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
	
	distance=math.sqrt(trans_aim_x_square+trans_aim_y_square)
	return distance

def getDistance3D(target1, target2):
	trans_x=target1.get_translate()[0]
	trans_y=target1.get_translate()[1]
	trans_z=target1.get_translate()[2]

	aim_x=target2.get_translate()[0]
	aim_y=target2.get_translate()[1]
	aim_z=target2.get_translate()[2]

	trans_aim_x_square=(trans_x - aim_x)*(trans_x - aim_x)
	trans_aim_y_square=(trans_y - aim_y)*(trans_y - aim_y)
	trans_aim_z_square=(trans_z - aim_z)*(trans_z - aim_z)
	
	distance=math.sqrt(trans_aim_x_square+trans_aim_y_square+trans_aim_z_square)
	return distance


'''reduce a transform matrix according to the constrainst '''
def reducePencilMat(mat):
	if not space3D:# on table?
			zCorrection=offsetTracking.get_translate().y
	else:
		zCorrection=0

	if reduceDOFRotate:
		#erase 2dof at table, unstable operation, calling this twice destroys the rotation information
		#get angle between rotation and y axis
		q = mat.get_rotate_scale_corrected()
		q.z = 0 #tried to fix to remove roll
		q.x = 0 #tried to fix to remove roll
		q.normalize()
		yRot = avango.gua.make_rot_mat(get_euler_angles(q)[0]*180.0/math.pi,0,1,0)#get euler y rotation, has also roll in it
	else:
		yRot = avango.gua.make_rot_mat(mat.get_rotate_scale_corrected())

	translation = avango.gua.make_trans_mat(
		mat.get_translate().x-offsetTracking.get_translate().x,
		mat.get_translate().y-zCorrection,
		mat.get_translate().z-offsetTracking.get_translate().z
	)

	if reduceDOFTranslate:
		translation.z = 0

	return translation* yRot		

class DisksContainer():
	
	def __init__(self):
		self.disk1 = None
		self.disk2 = None
		self.disk3 = None
		self.disk4 = None
		self.disk5 = None
		self.disk6 = None

	def setupDisks(self, translate):
		#attack disks to pointer
		disksNode = avango.gua.nodes.TransformNode(
			Transform = avango.gua.make_trans_mat(translate)
		)

		self.disk1 = loader.create_geometry_from_file("disk", "data/objects/disk_rotated.obj", avango.gua.LoaderFlags.NORMALIZE_SCALE)
		self.disk1.Material.value.set_uniform("Color", avango.gua.Vec4(0.0, 0.0, 1.0, 0.6))
		disksNode.Children.value.append(self.disk1)

		if not reduceDOFRotate:
			self.disk2 = loader.create_geometry_from_file("cylinder", "data/objects/disk_rotated.obj", avango.gua.LoaderFlags.NORMALIZE_SCALE)
			self.disk2.Material.value.set_uniform("Color", avango.gua.Vec4(1.0, 0.0, 0.0, 0.6))
			disksNode.Children.value.append(self.disk2)

			self.disk3 = loader.create_geometry_from_file("cylinder", "data/objects/disk_rotated.obj", avango.gua.LoaderFlags.NORMALIZE_SCALE)
			self.disk3.Material.value.set_uniform("Color", avango.gua.Vec4(0.5, 0.5, 0.5, 0.6))
			disksNode.Children.value.append(self.disk3)

			self.disk4 = loader.create_geometry_from_file("cylinder", "data/objects/disk_rotated.obj", avango.gua.LoaderFlags.NORMALIZE_SCALE)
			self.disk4.Material.value.set_uniform("Color", avango.gua.Vec4(0.0, 1.0, 0.0, 0.6))
			disksNode.Children.value.append(self.disk4)

			self.disk5 = loader.create_geometry_from_file("cylinder", "data/objects/disk_rotated.obj", avango.gua.LoaderFlags.NORMALIZE_SCALE)
			self.disk5.Material.value.set_uniform("Color", avango.gua.Vec4(0.5, 0.5, 0.5, 0.6))
			disksNode.Children.value.append(self.disk5)

			self.disk6 = loader.create_geometry_from_file("cylinder", "data/objects/disk_rotated.obj", avango.gua.LoaderFlags.NORMALIZE_SCALE)
			self.disk6.Material.value.set_uniform("Color", avango.gua.Vec4(0.5, 0.5, 0.5, 0.6))
			disksNode.Children.value.append(self.disk6)

			return disksNode

	def setDisksTransMats(self, diam):
		print("scaling to"+str(diam))
		self.disk1.Transform.value = avango.gua.make_trans_mat(0, 0, -r)*avango.gua.make_scale_mat(diam)
		if not reduceDOFRotate:
			self.disk2.Transform.value = avango.gua.make_rot_mat(-90,0,1,0)*avango.gua.make_trans_mat(0, 0, -r)*avango.gua.make_scale_mat(diam)
			self.disk3.Transform.value = avango.gua.make_rot_mat(90,0,1,0) *avango.gua.make_trans_mat(0, 0, -r)*avango.gua.make_scale_mat(diam)	
			self.disk4.Transform.value = avango.gua.make_rot_mat(90,1,0,0) *avango.gua.make_trans_mat(0, 0, -r)*avango.gua.make_scale_mat(diam)
			self.disk5.Transform.value = avango.gua.make_rot_mat(-90,1,0,0)*avango.gua.make_trans_mat(0, 0, -r)*avango.gua.make_scale_mat(diam)
			self.disk6.Transform.value = avango.gua.make_rot_mat(180,0,1,0)*avango.gua.make_trans_mat(0, 0, -r)*avango.gua.make_scale_mat(diam)

