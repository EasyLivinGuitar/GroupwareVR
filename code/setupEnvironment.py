import avango
import avango.daemon
import avango.gua
import avango.script
import avango.sound
import avango.sound.openal

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

resolution = avango.gua.Vec2ui(1920, 1080)
#screenSize = avango.gua.Vec2(1.235, 0.695) # in meters
screenSize = avango.gua.Vec2(1.445, 0.81) # in meters
window = avango.gua.nodes.GlfwWindow(
		Size=resolution,
		LeftResolution=resolution,
		RightResolution=resolution,
		StereoMode=avango.gua.StereoMode.CHECKERBOARD
		)

soundtraverser = avango.sound.nodes.SoundTraverser()
soundRenderer = avango.sound.openal.nodes.OpenALSoundRenderer()
soundRenderer.Device.value = ""
soundtraverser.Renderers.value = [soundRenderer]

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
	head_device_sensor.TransmitterOffset.value = getOffsetTracking()

	head_device_sensor.Station.value = "glasses"

	cam.Transform.connect_from(head_device_sensor.Matrix)


	graph.Root.value.Children.value=[light, screen]

	soundtraverser.RootNode.value = graph.Root.value
	soundtraverser.Traverse.value = True

	soundRenderer.ListenerPosition.connect_from(cam.Transform)

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

def launch():
	guaVE = GuaVE()
	guaVE.start(locals(), globals())
	'''
	balloonSound = avango.sound.nodes.SoundSource()
	balloonSound.URL.value = "data/sounds/balloon_pop.ogg"
	balloonSound.Loop.value = True
	balloonSound.Play.value = True
	viewer.SceneGraphs.value[0].Root.value.Children.value.extend([balloonSound])
	'''
	viewer.frame
	#balloonSound.Play.value = True
	viewer.run()

def setBackgroundColor(color, time):
	manager.time=timer.Time.value+time
	
	res_pass.BackgroundColor.value=color


'''if the z value should be locked'''
def ignoreZ():
	return True

def space3D():
	return False

def getOffsetTracking():
	return avango.gua.make_trans_mat(0.0, -0.14 - 0.405, 0.65)

def getTargetDepth():
	return 1.4;

def logResults():
	return False

'''if true needs a button press or next step, if false then autodetects'''
def onButtonPress():
	return True
