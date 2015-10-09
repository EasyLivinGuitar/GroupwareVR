import avango
import avango.daemon
import avango.gua
import avango.script
import avango.sound
import avango.sound.openal


class DisksContainer:

        def __init__(self, setenv):
            self.disk1 = None
            self.disk2 = None
            self.disk3 = None
            self.disk4 = None
            self.disk5 = None
            self.disk6 = None
            self.phone = None
            self.human = None
            self.node = None
            self.setup = setenv
            self.errormargin = 0

        '''for attaching the disk to the pointer, the pointer is needed'''
        def setupDisks(self, pencilNode):
            #attack boundsContainer to pointer
            self.node = avango.gua.nodes.TransformNode(
                Transform = avango.gua.make_trans_mat(pencilNode.Transform.value.get_translate())
            )

            if self.setup.usePhoneCursor:
                self.phone = self.setup.loader.create_geometry_from_file("phone_outline", "data/objects/phone/phoneAntennaOutlines.obj", avango.gua.LoaderFlags.DEFAULTS | avango.gua.LoaderFlags.LOAD_MATERIALS)
                self.setErrorMargin(0)
                self.node.Children.value.append(self.phone)
            else:
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

            if self.setup.showHuman:
                self.human = self.setup.loader.create_geometry_from_file("human", "data/objects/MaleLow.obj", avango.gua.LoaderFlags.NORMALIZE_SCALE)
                self.human.Material.value.set_uniform("Color", avango.gua.Vec4(1, 1, 1, 0.3))
                self.human.Material.value.EnableBackfaceCulling.value = False
                self.node.Children.value.append(self.human)

            self.setup.everyObject.Children.value.append(self.node)
            return self.node

        '''setup the position of the disk inside the container'''
        def setDisksTransMats(self, diam):
            # print("scaling to"+str(diam))
            if not self.setup.usePhoneCursor:
                self.disk1.Transform.value = avango.gua.make_trans_mat(0, 0, -self.setup.r)*avango.gua.make_scale_mat(diam)
                self.disk3.Transform.value = avango.gua.make_rot_mat(90,0,1,0) *avango.gua.make_trans_mat(0, 0, -self.setup.r)*avango.gua.make_scale_mat(diam)
                self.disk2.Transform.value = avango.gua.make_rot_mat(-90,0,1,0)*avango.gua.make_trans_mat(0, 0, -self.setup.r)*avango.gua.make_scale_mat(diam)
                self.disk6.Transform.value = avango.gua.make_rot_mat(180,0,1,0)*avango.gua.make_trans_mat(0, 0, -self.setup.r)*avango.gua.make_scale_mat(diam)

                if self.setup.virtualDOFRotate==3:
                    self.disk5.Transform.value = avango.gua.make_rot_mat(-90,1,0,0)*avango.gua.make_trans_mat(0, 0, -self.setup.r)*avango.gua.make_scale_mat(diam)
                    self.disk4.Transform.value = avango.gua.make_rot_mat(90,1,0,0) *avango.gua.make_trans_mat(0, 0, -self.setup.r)*avango.gua.make_scale_mat(diam)
                if self.setup.showHuman:
                    self.human.Transform.value = (
                        avango.gua.make_scale_mat(0.007)
                    )

        def setErrorMargin(self, errormargin):
            self.errormargin = errormargin
            if self.setup.usePhoneCursor:
                self.phone.Transform.value = avango.gua.make_scale_mat(
                    (4.4*0.01+errormargin)/(4.4*0.01)*0.001,
                    (1.5*0.01+errormargin)/(1.5*0.01)*0.001,
                    (11*0.01 +errormargin)/(11*0.01)*0.001
                )

        def setRotation(self, rotMat):
            self.node.Transform.value = avango.gua.make_trans_mat(self.node.Transform.value.get_translate()) * rotMat *avango.gua.make_scale_mat(self.node.Transform.value.get_scale())

        def setTranslate(self, transl):
            self.node.Transform.value = transl * avango.gua.make_rot_mat(self.node.Transform.value.get_rotate_scale_corrected())*avango.gua.make_scale_mat(self.node.Transform.value.get_scale())

        def getRotate(self):
            return self.node.Transform.value.get_rotate_scale_corrected()

        def highlightRed(self):
            if not self.setup.usePhoneCursor:
                self.disk1.Material.value.set_uniform("Color", avango.gua.Vec4(0.2, 0.0, 0.9, 0.6))
                self.disk2.Material.value.set_uniform("Color", avango.gua.Vec4(1.0, 0.0, 0.0, 0.6))
                self.disk3.Material.value.set_uniform("Color", avango.gua.Vec4(0.7, 0.4, 0.4, 0.6))
                self.disk6.Material.value.set_uniform("Color", avango.gua.Vec4(0.7, 0.4, 0.4, 0.6))

                if self.setup.virtualDOFRotate == 3:
                    self.disk4.Material.value.set_uniform("Color", avango.gua.Vec4(0.4, 0.9, 0.0, 0.6))
                    self.disk5.Material.value.set_uniform("Color", avango.gua.Vec4(0.7, 0.4, 0.4, 0.6))

        def setColor(self):
            if not self.setup.usePhoneCursor:
                self.disk1.Material.value.set_uniform("Color", avango.gua.Vec4(0.0, 0.0, 1.0, 0.6))
                self.disk2.Material.value.set_uniform("Color", avango.gua.Vec4(1.0, 0.0, 0.0, 0.6))
                self.disk3.Material.value.set_uniform("Color", avango.gua.Vec4(0.5, 0.5, 0.5, 0.6))
                self.disk6.Material.value.set_uniform("Color", avango.gua.Vec4(0.5, 0.5, 0.5, 0.6))

                if self.setup.virtualDOFRotate == 3:
                    self.disk4.Material.value.set_uniform("Color", avango.gua.Vec4(0.0, 1.0, 0.0, 0.6))
                    self.disk5.Material.value.set_uniform("Color", avango.gua.Vec4(0.5, 0.5, 0.5, 0.6))