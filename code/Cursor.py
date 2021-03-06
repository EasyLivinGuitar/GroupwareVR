import avango
import avango.daemon
import avango.gua
import avango.script
import avango.sound
import avango.sound.openal
import math
import core

'''The cursor and target. Can have a human'''
class Cursor(avango.script.Script):
    TimeIn = avango.SFFloat()
    inputMatA = avango.gua.SFMatrix4()
    animationStartTime = 0

    def __init__(self):
        self.super(Cursor).__init__()
        self.always_evaluate(True)
        self.animEndPos = None
        self.animEndRot = None
        self.startPos = None
        self.startRot = None
        self.setup = None
        self.human = None
        self.cursor = None #the geometry
        self.timer = None

    def create(self, setup):
        self.setup = setup

        if setup.usePhoneCursor:
            # create cross
            '''
            self.cursor = setup.setup.loader.create_geometry_from_file("phone",
                                                                 "/opt/3d_models/targets/phone/phone_ao.obj",
                                                                avango.gua.LoaderFlags.DEFAULTS | avango.gua.LoaderFlags.LOAD_MATERIALS)
            self.cursor.Transform.value = setup.offsetPointer * avango.gua.make_scale_mat(0.001)
            self.cursor.Material.value.EnableBackfaceCulling.value = False
            self.cursor.Material.value.set_uniform("Emissivity", 0.5)
            self.cursor.Material.value.set_uniform("Color", avango.gua.Vec4(1, 1, 1, 1))
            '''
            phone_body = setup.loader.create_geometry_from_file("phone_body",
                                                 "/opt/3d_models/targets/phone_parts/phone_body.obj",
                                                avango.gua.LoaderFlags.DEFAULTS | avango.gua.LoaderFlags.LOAD_MATERIALS)
            phone_body.Transform.value *=avango.gua.make_scale_mat(0.001)
            phone_body.Material.value.EnableBackfaceCulling.value = False
            phone_body.Material.value.set_uniform("ColorMap", "/opt/3d_models/targets/phone_parts/textures/New_Base_Color.png")
            phone_body.Material.value.set_uniform("NormalMap", "/opt/3d_models/targets/phone_parts/textures/New_Normal.png")
            phone_body.Material.value.set_uniform("RoughnessMap", "/opt/3d_models/targets/phone_parts/textures/New_Roughness.png")
            phone_body.Material.value.set_uniform("MetalnessMap", "/opt/3d_models/targets/phone_parts/textures/New_Metallic.png")

    
            phone_buttons = setup.loader.create_geometry_from_file("phone_buttons",
                                                     "/opt/3d_models/targets/phone_parts/phone_buttons.obj",
                                                    avango.gua.LoaderFlags.DEFAULTS | avango.gua.LoaderFlags.LOAD_MATERIALS)
            phone_buttons.Transform.value *=avango.gua.make_scale_mat(0.001)
            phone_buttons.Material.value.EnableBackfaceCulling.value = False
            phone_buttons.Material.value.set_uniform("ColorMap", "/opt/3d_models/targets/phone_parts/textures/Plastic_Base_Color.png")
            phone_buttons.Material.value.set_uniform("NormalMap", "/opt/3d_models/targets/phone_parts/textures/Plastic_Normal.png")
            phone_buttons.Material.value.set_uniform("RoughnessMap", "/opt/3d_models/targets/phone_parts/textures/Plastic_Roughness.png")
            phone_buttons.Material.value.set_uniform("MetalnessMap", "/opt/3d_models/targets/phone_parts/textures/Plastic_Metallic.png")
    
            phone_screen = setup.loader.create_geometry_from_file("phone_screen",
                                                     "/opt/3d_models/targets/phone_parts/phone_screen.obj",
                                                    avango.gua.LoaderFlags.DEFAULTS | avango.gua.LoaderFlags.LOAD_MATERIALS)
            phone_screen.Transform.value *=avango.gua.make_scale_mat(0.001)
            phone_screen.Material.value.EnableBackfaceCulling.value = False
            phone_screen.Material.value.set_uniform("ColorMap", "/opt/3d_models/targets/phone_parts/textures/Silver_Base_Color.png")
            phone_screen.Material.value.set_uniform("NormalMap", "/opt/3d_models/targets/phone_parts/textures/Silver_Normal.png")
            phone_screen.Material.value.set_uniform("RoughnessMap", "/opt/3d_models/targets/phone_parts/textures/Silver_Roughness.png")
            phone_screen.Material.value.set_uniform("MetalnessMap", "/opt/3d_models/targets/phone_parts/textures/Silver_Metallic.png")
    
            phone_antenna = setup.loader.create_geometry_from_file("phone_antenna",
                                                     "/opt/3d_models/targets/phone_parts/phone_antenna.obj",
                                                    avango.gua.LoaderFlags.DEFAULTS | avango.gua.LoaderFlags.LOAD_MATERIALS)
            phone_antenna.Transform.value *=avango.gua.make_scale_mat(0.001)
            phone_antenna.Material.value.EnableBackfaceCulling.value = False
            phone_antenna.Material.value.set_uniform("ColorMap", "/opt/3d_models/targets/phone_parts/textures/Black_Base_Color.png")
            phone_antenna.Material.value.set_uniform("NormalMap", "/opt/3d_models/targets/phone_parts/textures/Black_Normal.png")
            phone_antenna.Material.value.set_uniform("RoughnessMap", "/opt/3d_models/targets/phone_parts/textures/Black_Roughness.png")
            phone_antenna.Material.value.set_uniform("MetalnessMap", "/opt/3d_models/targets/phone_parts/textures/Black_Metallic.png")
    
            phone_cam = setup.loader.create_geometry_from_file("phone_cam",
                                                     "/opt/3d_models/targets/phone_parts/phone_cam.obj",
                                                    avango.gua.LoaderFlags.DEFAULTS | avango.gua.LoaderFlags.LOAD_MATERIALS)
            phone_cam.Transform.value *=avango.gua.make_scale_mat(0.001)
            phone_cam.Material.value.EnableBackfaceCulling.value = False
            phone_cam.Material.value.set_uniform("ColorMap", "/opt/3d_models/targets/phone_parts/textures/Black_Base_Color.png")
            phone_cam.Material.value.set_uniform("NormalMap", "/opt/3d_models/targets/phone_parts/textures/Black_Normal.png")
            phone_cam.Material.value.set_uniform("RoughnessMap", "/opt/3d_models/targets/phone_parts/textures/Black_Roughness.png")
            phone_cam.Material.value.set_uniform("MetalnessMap", "/opt/3d_models/targets/phone_parts/textures/Black_Metallic.png")
    

            self.cursor = avango.gua.nodes.TransformNode(
                Children=[phone_body, phone_buttons, phone_screen, phone_cam, phone_antenna])



        else:
            self.cursor = setup.setup.loader.create_geometry_from_file("colored_cross",
                                                                 "data/objects/colored_cross.obj",
                                                                avango.gua.LoaderFlags.DEFAULTS | avango.gua.LoaderFlags.LOAD_MATERIALS)
            self.cursor.Transform.value = setup.offsetPointer * avango.gua.make_scale_mat(self.setup.r / self.setup.r_model)

        #self.cursor.Material.value.EnableBackfaceCulling.value = False
        # pencil.Transform.value = avango.gua.make_scale_mat(1)#to prevent that this gets huge
        # pencil.Material.value.set_uniform("Color", avango.gua.Vec4(0.6, 0.6, 0.6, 1))
        # pencil.Material.value.set_uniform("Emissivity", 1.0)
        self.setup.everyObject.Children.value.append(self.cursor)
        if setup.showHuman:
            self.human = setup.setup.loader.create_geometry_from_file("human", "data/objects/MaleLow.obj",
                                                                avango.gua.LoaderFlags.DEFAULTS)
            self.human.Material.value.set_uniform("Color", avango.gua.Vec4(1, 1, 1, 0.3))
            self.human.Material.value.EnableBackfaceCulling.value = False
            self.setup.everyObject.Children.value.append(self.human)

        # listen to tracked position of pointers
        pointer_device_sensor = avango.daemon.nodes.DeviceSensor(DeviceService=avango.daemon.DeviceService())
        pointer_device_sensor.TransmitterOffset.value = self.setup.offsetTracking

        # connect pencil->inputMatA
        pointer_device_sensor.Station.value = "pointer"
        self.inputMatA.connect_from(pointer_device_sensor.Matrix)

        self.timer = avango.nodes.TimeSensor()
        self.TimeIn.connect_from(self.timer.Time)

        return self

    def evaluate(self):#each frame
        # get input
        self.cursor.Transform.value = self.setup.offsetPointer * self.inputMatA.value * avango.gua.make_scale_mat(
            self.cursor.Transform.value.get_scale())#keep scale
        # then reduce
        self.reducePencilMat()

        # copy to human
        if self.setup.showHuman:
            self.human.Transform.value = (
                avango.gua.make_trans_mat(self.cursor.Transform.value.get_translate())
                * avango.gua.make_rot_mat(self.cursor.Transform.value.get_rotate_scale_corrected())
                * avango.gua.make_scale_mat(0.007)
            )

        if (self.animEndPos is not None) or (self.animEndRot is not None):
            # animate the movement preview
            percentile = (self.TimeIn.value - self.animationStartTime) / self.setup.animationTime
            # if no end position give n use cursor position instead
            if self.animEndPos is None:
                translateMat = avango.gua.make_trans_mat(self.cursor.Transform.value.get_translate())
            else:
                translateMat = avango.gua.make_trans_mat(
                    self.startPos.lerp_to(self.animEndPos, percentile)
                )
            if self.setup.showHuman:
                self.human.Transform.value = (
                    translateMat
                    * avango.gua.make_rot_mat(
                        self.startRot.slerp_to(self.animEndRot, percentile)
                    )
                    * avango.gua.make_scale_mat(
                        self.human.Transform.value.get_scale()
                    )
                )
            else:
                self.cursor.Transform.value = (
                    translateMat
                    * avango.gua.make_rot_mat(
                        self.startRot.slerp_to(self.animEndRot, percentile)
                    )
                    * avango.gua.make_scale_mat(
                        self.cursor.Transform.value.get_scale()
                    )
                )

        # animation over?
        if self.TimeIn.value - self.animationStartTime > self.setup.animationTime:
            self.animEndPos = None
            self.animEndRot = None

    def getNode(self):
        return self.cursor

    def getTransfromValue(self):
        return self.cursor.Transform.value

    '''reduce a transform matrix according to the constrainst '''

    def reducePencilMat(self):
        if self.setup.virtualDOFRotate == 1:
            # erase 2dof at table, unstable operation, calling this twice destroys the rotation information
            # get angle between rotation and y axis
            q = self.cursor.Transform.value.get_rotate_scale_corrected()
            q.z = 0  # tried to fix to remove roll
            q.x = 0  # tried to fix to remove roll
            q.normalize()
            rot = avango.gua.make_rot_mat(core.get_euler_angles(q)[0] * 180.0 / math.pi, 0, 1,
                                           0)  # get euler y rotation, has also roll in it
        elif self.setup.virtualDOFRotate == 0:
            rot = avango.gua.make_identity_mat()
        else:
            rot = avango.gua.make_rot_mat(self.getTransfromValue().get_rotate_scale_corrected())


        if self.setup.disableAxis[0]:
            x = 0
        else:
            x = self.getTransfromValue().get_translate().x

        if self.setup.disableAxis[1]:
            y = 0
        else:
            if self.setup.space3D:  # on table?
                y = self.getTransfromValue().get_translate().y
            else:
                y = self.getTransfromValue().get_translate().y

        if self.setup.disableAxis[2]:
            z = 0
        else:
            z = self.getTransfromValue().get_translate().z

        translation = avango.gua.make_trans_mat(
            x,
            y,
            z
        )

        self.cursor.Transform.value = translation * rot * avango.gua.make_scale_mat(self.cursor.Transform.value.get_scale())

    '''This method moves the cursor to the target. targetPos can be None'''
    def animateTo(self, targetPos, targetRot):
        self.startPos = self.cursor.Transform.value.get_translate()
        self.startRot = self.cursor.Transform.value.get_rotate_scale_corrected()
        self.animEndPos = targetPos
        self.animEndRot = targetRot
        self.animationStartTime = self.TimeIn.value  # aktuelle Zeit

    def isAnimating(self):
        return self.animEndRot is not None or self.animEndPos is not None