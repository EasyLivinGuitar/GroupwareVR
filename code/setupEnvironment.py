import avango
import avango.daemon
import avango.gua
import avango.script

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



def print_graph(root_node):
	stack = [ ( root_node, 0) ]
	while stack:
		node, level = stack.pop()
		print("│   " * level + "├── {0} <{1}>".format(node.Name.value, node.__class__.__name__))
		stack.extend( [ (child, level + 1) for child in reversed(node.Children.value) ] )


viewer = avango.gua.nodes.Viewer()

resolution = avango.gua.Vec2ui(1920, 1080)
screenSize = avango.gua.Vec2(1.235, 0.695) # in meters
#screenSize = avango.gua.Vec2(1., 0.495) # in meters
window = avango.gua.nodes.GlfwWindow(
		Size=resolution,
		LeftResolution=resolution,
		RightResolution=resolution,
		StereoMode=avango.gua.StereoMode.CHECKERBOARD
		)


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
		#Transform=avango.gua.make_rot_mat(180 , 0.0, 0.0, 0.0),
		Children=[cam]
		)

	#Sieht netter aus
	res_pass = avango.gua.nodes.ResolvePassDescription()
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


	graph.Root.value.Children.value=[light, screen]

	#setup viewer
	viewer.SceneGraphs.value = [graph]
	viewer.Windows.value = [window]

	'''fieldmanager = FieldManager()
	headtracking = avango.daemon.nodes.DeviceSensor(DeviceService=avango.daemon.DeviceService())
	headtracking.TransmitterOffset.value = getOffsetTracking()
	headtracking.Station.value = "glass-1"
	fieldmanager.TransMat.connect_from(headtracking.Matrix)
	cam.Transform.connect_from(fieldmanager.TransMat)'''

class FieldManager(avango.script.Script):
	TransMat = avango.gua.SFMatrix4()

	def __init__(self):
		self.super(FieldManager).__init__()
	
	@field_has_changed(TransMat)
	def transMatHasChanged(self):
		print(self.TransMat.value)

def getWindow():
	return window

def launch():
	guaVE = GuaVE()
	guaVE.start(locals(), globals())

	viewer.run()

'''if the z value should be locked'''
def ignoreZ():
	return False

def space3D():
	return False

def getOffsetTracking():
	return avango.gua.make_trans_mat(0.0, -1.0, 0.0) 