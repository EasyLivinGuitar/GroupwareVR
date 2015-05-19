import avango
import avango.daemon
import avango.gua
import avango.script
import random
import setupEnvironment

from examples_common.GuaVE import GuaVE
from avango.script import field_has_changed

class PointerStuff(avango.script.Script):
	TopButton = avango.SFBool()
	CenterButton = avango.SFBool()
	BottomButton = avango.SFBool()
	TransMat = avango.gua.SFMatrix4()


	OutColor = avango.gua.Vec4(1.0, 0.0, 0.0, 1.0)

	def __init__(self):
		self.super(PointerStuff).__init__()
		self.top_button_last_time = False
		self.cylinderRef = None

	@field_has_changed(TopButton)
	def top_button_has_changed(self):
		pass

	@field_has_changed(TransMat)
	def transMatHasChanged(self):
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
	tracked_object=loader.create_geometry_from_file("tracked_object", "data/objects/tracked_object.obj", avango.gua.LoaderFlags.NORMALIZE_SCALE)

	object_transform=avango.gua.nodes.TransformNode(Children=[tracked_object], Transform=avango.gua.make_scale_mat(0.01))

	home=loader.create_geometry_from_file("light_sphere", "data/objects/light_sphere.obj", avango.gua.LoaderFlags.NORMALIZE_SCALE)
	home.Transform.value = avango.gua.make_scale_mat(0.2)
	home.Material.value.set_uniform("Color", avango.gua.Vec4(1, 0,0, 0.5)) #Transparenz funktioniert nicht
	tracking = setupEnvironment.setup(graph)

	graph.Root.value.Children.value.extend([object_transform, home])

	tracked_object.Transform.connect_from(tracking.Matrix)

	pointer_device_sensor = avango.daemon.nodes.DeviceSensor(
		DeviceService = avango.daemon.DeviceService()
		)
	pointer_device_sensor.Station.value = "device-pointer"

	pointerstuff = PointerStuff()
	pointerstuff.TopButton.connect_from(pointer_device_sensor.Button0)
	pointerstuff.CenterButton.connect_from(pointer_device_sensor.Button1)
	pointerstuff.BottomButton.connect_from(pointer_device_sensor.Button2)
	#pointerstuff.TransMat.connect_from(tracking.Matrix)
	pointerstuff.cylinderRef = tracked_object

	#light.Color.connect_from(pointerstuff.OutColor)
	setupEnvironment.launch()

if __name__ == '__main__':
  start()