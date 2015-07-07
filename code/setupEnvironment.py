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
timer=avango.nodes.TimeSensor()


res_pass = avango.gua.nodes.ResolvePassDescription()

def print_graph(root_node):
	stack = [ ( root_node, 0) ]
	while stack:
		node, level = stack.pop()
		print("│   " * level + "├── {0} <{1}>".format(node.Name.value, node.__class__.__name__))
		stack.extend( [ (child, level + 1) for child in reversed(node.Children.value) ] )


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

cam = avango.gua.nodes.CameraNode()

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
		Transform=avango.gua.make_trans_mat(0.0, 0.0, 3.5)
		)
	screen = avango.gua.nodes.ScreenNode(
		Name="screen",
		Width=screenSize.x,
		Height=screenSize.y,
		Children=[cam]
		)

	#Sieht netter aus
	res_pass.EnableSSAO.value = False
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
	head_device_sensor.TransmitterOffset.value = getOffsetTracking()

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


'''Settings'''


'''if the z value should be locked'''
def ignoreZ():
	return True

def space3D():
	return True

def getOffsetTracking():
	return avango.gua.make_trans_mat(0.0, -0.14 - 0.405, 0.68)

'''get the position pf the cetner where the pointer and the aim is located'''
def getCenterPosition():
	return avango.gua.make_trans_mat(0.0, 0, 0.38)

def logResults():
	return True

'''if true needs a button press or next step, if false then autodetects'''
def useAutoDetect():
	return False

def randomTargets():
	return False


class logManager(avango.script.Script):
	userID=0
	group=0
	condition=None
	DOF_T=0
	DOF_R=0
	movement_direction=None
	target_distance_t=0
	target_width_t=0
	rotation_axis=None
	target_distance_r=0
	target_width_r=0
	ID_t=0
	ID_r=0
	ID_combined=0
	repetition=0
	trial=0
	button_clicks=0
	succesful_clicks=0
	success=None
	hit_type=None
	hit_time=0
	hit_error_t=0
	hit_error_r=0
	overshoots=0
	throughput=0
	peak_acceleration=0
	movement_continuity_t=0

	header_printed=False

	def setUserID(self, ID):
		self.userID=ID

	def setGroup(self, grp):
		self.group=grp

	def setCondition(self, task):
		self.condition = task

	def setDOF(self, DOFt, DOFr):
		self.DOF_T=DOFt
		self.DOF_R=DOFr

	def setMovementDirection(self, aim_mat, base_mat):
		if(aim_mat.value.get_translate().x > base_mat.value.get_translate().x):
			self.movement_direction="r"
		else:
			self.movement_direction="l"

	def setTargetDistance_t(self, distance):
		self.target_distance_t=distance

	def setTargetWidth_t(self, width):
		self.target_width_t=width

	def setRotationAxis(self, axis):
		self.rotation_axis=axis

	def setTargetDistance_r(self, distance):
		self.target_distance_r=distance

	def setTargetWidth_r(self, width):
		self.target_width_t=width

	def setID_combined(self, idt, idr):
		self.ID_t=idt
		self.ID_r=idr
		self.ID_combined=self.ID_t+self.ID_r

	def setRepetition(self, rep):
		self.repetition=rep

	def setTrial(self, tria):
		self.trial=tria

	def setClicks(self, clicks, clicks_s):
		self.button_clicks=clicks
		self.succesful_clicks=clicks_s

	def setSuccess(self, suc):
		self.success=suc

	def setHit(self, h_type, h_time, error_t, error_r):
		self.hit_type=h_type
		self.hit_time=h_time
		self.hit_error_t=error_t
		self.hit_error_r=error_r
		self.setThroughput()

	def setOvershoots(self, shoots):
		self.overshoots=shoots

	def setThroughput(self):
		if(self.hit_time>0):
			self.throughput=self.ID_combined/self.hit_time

	def setMovementContinuity(self, peak_acc, first_point_acc):
		self.peak_acceleration=peak_acc
		if(peak_acc>0):
			self.movement_continuity_t=first_point_acc/peak_acc


	def log(self, result_file):
		if(self.header_printed==False):
			result_file.write(
				"USERID | "+
				"GROUP | "+
				"CONDITION | "+
				"DOF_T | "+
				"DOF_R | "+
				"MOVEMENT_DIRECTION | "+ 
				"TARGET_DISTANCE_T | "+
				"TARGET_WIDTH_T | "+
				"ROTATION_AXIS | "+
				"TARGET_DISTANCE_R | "+
				"TARGET_WIDTH_R | "+
				"ID_T | "+
				"ID_R | "+
				"ID_COMBINED | "+
				"REPETITION | "+
				"TRIAL | "+
				"BUTTON CLICKS | "+
				"SUCCESFULL CLICKS | " +
				"SUCCESS | "+
				"HIT_TYPE | "+
				"HIT_TIME | "+
				"HIT_ERROR_T | "+
				"HIT_ERROR_R | "+
				"OVERSHOOTS | "+
				"THROUGHPUT | "+
				"PEAK_ACCELERATION | "+
				"MOVEMENT_CONTINUITY_T | "+
				"\n \n")
			self.header_printed=True

		result_file.write(
			str(self.userID)+ " | "+
			str(self.group)+" | "+
			str(self.condition)+" | "+
			str(self.DOF_T)+" | "+
			str(self.DOF_R)+" | "+
			str(self.movement_direction)+" | "+
			str(self.target_distance_t)+" | "+
			str(self.target_width_t)+" | "+
			str(self.rotation_axis)+" | "+
			str(self.target_distance_r)+" | "+
			str(self.target_width_r)+" | "+
			str(self.ID_t)+" | "+
			str(self.ID_r)+" | "+
			str(self.ID_combined)+" | "+
			str(self.repetition)+" | "+
			str(self.trial)+" | "+
			str(self.button_clicks)+" | "+
			str(self.succesful_clicks)+" | "+
			str(self.success)+" | "+
			str(self.hit_type)+" | "+
			str(self.hit_time)+" | "+
			str(self.hit_error_t)+" | "+
			str(self.hit_error_r)+" | "+
			str(self.overshoots)+" | "+
			str(self.throughput)+" | "+
			str(self.peak_acceleration)+" | "+
			str(self.movement_continuity_t)+" | "+
			"\n")