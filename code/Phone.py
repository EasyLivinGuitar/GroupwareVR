import avango

'''manages the phone model used as target and cursor'''
class Phone(object):

	def __init__(self, setup):
		self.errormargin = 0
		self.geometry = setup.loader.create_geometry_from_file("phone_outline", "/opt/3d_models/targets/phone/phoneAntennaOutlines.obj", avango.gua.LoaderFlags.DEFAULTS | avango.gua.LoaderFlags.LOAD_MATERIALS)
		setup.everyObject.Children.value.append(self.geometry)
		self.setErrorMargin(0)

	def setErrorMargin(self, errormargin):
		self.errormargin = errormargin
		self.geometry.Transform.value = (
			avango.gua.make_trans_mat(self.geometry.Transform.value.get_translate())#keep translate
			* avango.gua.make_rot_mat(self.geometry.Transform.value.get_rotate_scale_corrected())#keep rot
			* avango.gua.make_scale_mat(
				(4.4*0.01 + errormargin)/(4.4*0.01)*0.001,
				(1.5*0.01 + errormargin)/(1.5*0.01)*0.001,
				(11*0.01  + errormargin)/(11*0.01)*0.001
			)
		)

	def setRotation(self, rotMat):
		self.geometry.Transform.value = (
			avango.gua.make_trans_mat(self.geometry.Transform.value.get_translate())
			* rotMat
			*avango.gua.make_scale_mat(self.geometry.Transform.value.get_scale())
		)

	def setTranslate(self, transl):
		self.geometry.Transform.value = (transl
			* avango.gua.make_rot_mat(self.geometry.Transform.value.get_rotate_scale_corrected())#keep rot
			* avango.gua.make_scale_mat(self.geometry.Transform.value.get_scale())#keep scale
		)

	def getRotate(self):
		return self.geometry.Transform.value.get_rotate_scale_corrected()
