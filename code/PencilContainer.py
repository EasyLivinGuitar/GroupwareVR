import avango
import avango.daemon
import avango.gua
import avango.script
import avango.sound
import avango.sound.openal
import math

from avango.script import field_has_changed


class PencilContainer(avango.script.Script):
    TimeIn = avango.SFFloat()
    pointer_device_sensor = None
    inputMat = avango.gua.SFMatrix4()
    animationTime = 0

    def __init__(self):
        self.super(PencilContainer).__init__()
        self.aimPos = None
        self.aimRot = None
        self.startPos = None
        self.startRot = None
        self.setup = None

    def create(self, setup):
        self.setup = setup

        # create cross
        self.pencil = setup.loader.create_geometry_from_file("colored_cross", "data/objects/colored_cross.obj",
                                                             avango.gua.LoaderFlags.DEFAULTS | avango.gua.LoaderFlags.LOAD_MATERIALS)
        self.pencil.Transform.value = setup.offsetPointer * avango.gua.make_scale_mat(self.setup.r / self.setup.r_model)
        # pencil.Transform.value = avango.gua.make_scale_mat(1)#to prevent that this gets huge
        # pencil.Material.value.set_uniform("Color", avango.gua.Vec4(0.6, 0.6, 0.6, 1))
        # pencil.Material.value.set_uniform("Emissivity", 1.0)
        self.setup.everyObject.Children.value.append(self.pencil)
        if setup.showHuman:
            self.human = setup.loader.create_geometry_from_file("human", "data/objects/MaleLow.obj",
                                                                avango.gua.LoaderFlags.DEFAULTS)
            self.human.Material.value.set_uniform("Color", avango.gua.Vec4(1, 1, 1, 0.3))
            self.human.Material.value.EnableBackfaceCulling.value = False
            self.setup.everyObject.Children.value.append(self.human)

        # listen to tracked position of pointer
        self.pointer_device_sensor = avango.daemon.nodes.DeviceSensor(DeviceService=avango.daemon.DeviceService())
        self.pointer_device_sensor.TransmitterOffset.value = self.setup.offsetTracking

        self.pointer_device_sensor.Station.value = "pointer"
        # connect pencil->inputMat
        self.inputMat.connect_from(self.pointer_device_sensor.Matrix)

        timer = avango.nodes.TimeSensor()
        self.TimeIn.connect_from(timer.Time)

        return self

    @field_has_changed(inputMat)
    def pointermat_changed(self):
        # not animation preview
        if self.aimPos is None:
            # get input
            self.pencil.Transform.value = self.setup.offsetPointer * self.inputMat.value * avango.gua.make_scale_mat(
                self.pencil.Transform.value.get_scale())
            # then reduce
            self.reducePencilMat()
            # apply to human
            if self.setup.showHuman:
                self.human.Transform.value = (
                    avango.gua.make_trans_mat(self.pencil.Transform.value.get_translate())
                    * avango.gua.make_rot_mat(self.pencil.Transform.value.get_rotate_scale_corrected())
                    * avango.gua.make_scale_mat(0.007)
                )

    def evaluate(self):
        # animate preview
        if self.aimPos is not None:
            percentile = (self.TimeIn.value - self.animationTime) / 1
            self.human.Transform.value = (
                avango.gua.make_trans_mat(
                    self.startPos.lerp_to(self.aimPos, percentile)
                )
                * avango.gua.make_rot_mat(
                    self.startRot.slerp_to(self.aimRot, percentile)
                )
                * avango.gua.make_scale_mat(
                    self.human.Transform.value.get_scale()
                )
            )
            if self.TimeIn.value - self.animationTime > 1:
                self.aimPos = None

    def getNode(self):
        return self.pencil

    def getTransfromValue(self):
        return self.pencil.Transform.value

    '''reduce a transform matrix according to the constrainst '''

    def reducePencilMat(self):
        if self.setup.virtualDOFRotate == 1:
            # erase 2dof at table, unstable operation, calling this twice destroys the rotation information
            # get angle between rotation and y axis
            q = self.pencil.Transform.value.get_rotate_scale_corrected()
            q.z = 0  # tried to fix to remove roll
            q.x = 0  # tried to fix to remove roll
            q.normalize()
            yRot = avango.gua.make_rot_mat(get_euler_angles(q)[0] * 180.0 / math.pi, 0, 1,
                                           0)  # get euler y rotation, has also roll in it
        else:
            yRot = avango.gua.make_rot_mat(self.getTransfromValue().get_rotate_scale_corrected())

        if self.setup.disableAxis[0]:
            x = 0
        else:
            x = self.getTransfromValue().get_translate().x - self.setup.offsetTracking.get_translate().x

        if self.setup.disableAxis[1]:
            y = 0
        else:
            if self.setup.space3D:  # on table?
                y = self.getTransfromValue().get_translate().y
            else:
                y = self.getTransfromValue().get_translate().y - self.setup.offsetTracking.get_translate().y

        if self.setup.disableAxis[2]:
            z = 0
        else:
            z = self.getTransfromValue().get_translate().z - self.setup.offsetTracking.get_translate().z

        translation = avango.gua.make_trans_mat(
            x,
            y,
            z
        )

        self.pencil.Transform.value = translation * yRot * avango.gua.make_scale_mat(
            self.pencil.Transform.value.get_scale())

    '''This method moves the cursor to the aim'''

    def moveToGoal(self, aimPos, aimRot):
        self.startPos = self.pencil.Transform.value.get_translate()
        self.startRot = self.pencil.Transform.value.get_rotate_scale_corrected()
        self.aimPos = aimPos
        self.aimRot = aimRot
        self.animationTime = self.TimeIn.value  # aktuelle Zeit
