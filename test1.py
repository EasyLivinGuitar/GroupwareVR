import avango
import avango.daemon
import avango.gua
import avango.script
import random

from examples_common.GuaVE import GuaVE
from avango.script import field_has_changed

def print_graph(root_node):
	stack = [ ( root_node, 0) ]
	while stack:
		node, level = stack.pop()
		print("│   " * level + "├── {0} <{1}>".format(node.Name.value, node.__class__.__name__))
		stack.extend( [ (child, level + 1) for child in reversed(node.Children.value) ] )

class PointerStuff(avango.script.Script):
	TopButton = avango.SFBool()
	CenterButton = avango.SFBool()
	BottomButton = avango.SFBool()


	OutColor = avango.gua.Vec4(1.0, 0.0, 0.0, 1.0)

	def __init__(self):
		self.super(PointerStuff).__init__()
		self.top_button_last_time = False
		self.cylinderRef = None

	@field_has_changed(TopButton)
	def top_button_has_changed(self):
		pass

	def evaluate(self):
		if self.TopButton.value:
			print("TopButton down")
			self.cylinderRef.Material.value.set_uniform("Color", avango.gua.Vec4(random.random(), random.random(), random.random(), 1.0))
		if self.CenterButton.value:
			print("CenterButton down")
			self.cylinderRef.Transform.value = avango.gua.make_trans_mat(0, 0, -0.1)*self.cylinderRef.Transform.value
			#self.cylinderRef.Transform.value = avango.gua.make_trans_mat(0, 0, -1)*avango.gua.make_scale_mat(0.01, 0.01, 10.0)
		if self.CenterButton.value==False:
			print("CenterButton up")
			self.cylinderRef.Transform.value = avango.gua.make_trans_mat(0, 0, 0.1)*self.cylinderRef.Transform.value
			#self.cylinderRef.Transform.value = avango.gua.make_trans_mat(0, 0, -1)*avango.gua.make_scale_mat(0.01, 0.01, 10.0)
		if self.BottomButton.value:
			print("BottomButton down")

def start ():
	graph=avango.gua.nodes.SceneGraph(Name="scenegraph") #Create Graph
	loader = avango.gua.nodes.TriMeshLoader() #Create Loader

	#Meshes
	cube=loader.create_geometry_from_file("cube", "data/objects/cube.obj", avango.gua.LoaderFlags.NORMALIZE_SCALE)

	monkey=loader.create_geometry_from_file("monkey", "data/objects/monkey.obj", avango.gua.LoaderFlags.NORMALIZE_SCALE)

	monkey.Transform.value=avango.gua.make_scale_mat(0.1)

	cube_transform=avango.gua.nodes.TransformNode(Children=[cube], Transform=avango.gua.make_scale_mat(0.1))

	monkey_transform=avango.gua.nodes.TransformNode(Children=[monkey])

	cylinder=loader.create_geometry_from_file("cylinder", "data/objects/cylinder.obj", avango.gua.LoaderFlags.NORMALIZE_SCALE)

	cylinder.Transform.value=avango.gua.make_scale_mat(0.01, 0.01, 10.0)

	cylinder_transform=avango.gua.nodes.TransformNode(Children=[cylinder])

	#Material 
	cube.Material.value.set_uniform("Color", avango.gua.Vec4(0.0, 0.8, 0.136, 0.8))
	cube.Material.value.set_uniform("Roughness", 0.4)
	cube.Material.value.set_uniform("Metalness", 0.2)

	light = avango.gua.nodes.LightNode(
		Type=avango.gua.LightType.POINT,
		Name="light",
		Color=avango.gua.Color(1.0, 1.0, 1.0),
		Brightness=100.0,
		Transform=(avango.gua.make_trans_mat(1, 1, 5) *
				   avango.gua.make_scale_mat(30, 30, 30))
		)

	resolution = avango.gua.Vec2ui(1920, 1080)
	screenSize = avango.gua.Vec2(1.235, 0.695) # in meters

	window = avango.gua.nodes.GlfwWindow(
		Size=resolution,
		LeftResolution=resolution,
		RightResolution=resolution,
		StereoMode=avango.gua.StereoMode.CHECKERBOARD
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
		Transform=avango.gua.make_rot_mat(40.0 , -1.0, 0.0, 0.0),
		#Children=[cam]
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
	res_pass.BackgroundColor.value = avango.gua.Color(0.45, 0.5, 0.6)

	anti_aliasing = avango.gua.nodes.SSAAPassDescription()

	pipeline_description = avango.gua.nodes.PipelineDescription(
		Passes=[
			avango.gua.nodes.TriMeshPassDescription(),
			avango.gua.nodes.LightVisibilityPassDescription(),
			res_pass,
			anti_aliasing,
			])

	cam.PipelineDescription.value = pipeline_description

	graph.Root.value.Children.value=[light, cube_transform, cylinder_transform, screen, cam]

	#setup viewer
	viewer = avango.gua.nodes.Viewer()
	viewer.SceneGraphs.value = [graph]
	viewer.Windows.value = [window]

	offset_tracking=avango.gua.make_trans_mat(-0.05, 0.05, 0.825)

	headtracking = avango.daemon.nodes.DeviceSensor(DeviceService=avango.daemon.DeviceService())
	headtracking.TransmitterOffset.value = offset_tracking
	headtracking.Station.value = "head"
	cam.Transform.connect_from(headtracking.Matrix)

	pointertracking = avango.daemon.nodes.DeviceSensor(
		DeviceService=avango.daemon.DeviceService()
		)
	pointertracking.TransmitterOffset.value = offset_tracking
	pointertracking.Station.value = "pointer"

	cylinder_transform.Transform.connect_from(pointertracking.Matrix)

	pointer_device_sensor = avango.daemon.nodes.DeviceSensor(
		DeviceService = avango.daemon.DeviceService()
		)
	pointer_device_sensor.Station.value = "device-pointer"

	pointerstuff = PointerStuff()
	pointerstuff.TopButton.connect_from(pointer_device_sensor.Button0)
	pointerstuff.CenterButton.connect_from(pointer_device_sensor.Button1)
	pointerstuff.BottomButton.connect_from(pointer_device_sensor.Button2)
	pointerstuff.cylinderRef = cylinder

	#light.Color.connect_from(pointerstuff.OutColor)

	guaVE = GuaVE()
	guaVE.start(locals(), globals())

	viewer.run()


if __name__ == '__main__':
  start()