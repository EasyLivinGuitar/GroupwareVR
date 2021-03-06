# coding=utf-8
import math
import glob

import sys
import avango
import avango.daemon
import avango.gua
import avango.script
import core
import RotationTarget
import Phone
import Cursor
import LogManager
import random
from avango.script import field_has_changed

class taskManager(avango.script.Script):
    button = avango.SFBool()
    timer = avango.SFFloat()
    inputMatB = avango.gua.SFMatrix4()

    time2 = 0

    runningTest = False
    endedTests = False

    created_logfile = False
    created_replayfile = False

    counter = 0

    # Logging
    trial = 1
    clicks = 0

    MT = 0
    TP = 0
    overshoots_r = 0
    overshoots_t = 0
    overshootInside_translate = False
    overshootInside_rotate = False

    frame_counter_speed = 0
    frame_counter_acceleration = 0

    low_speed_counter = 0

    goal = False

    peak_speed_t = 0
    peak_speed_r = 0

    current_speed_translate = 0
    current_speed_rotate = 0
    current_acceleration_translate = 0
    current_acceleration_rotate = 0
    peak_acceleration_t = 0
    peak_acceleration_r = 0
    first_reversal_acceleration_t = 0
    first_reversal_acceleration_rotate = 0
    first_reversal_point_t = 0
    first_reversal_point_r = 0
    first_translate = True
    first_rotate = True
    reversal_points_t = []
    reversal_points_r = []
    error_r = []
    error_t = []
    eff_A_trans = []
    eff_A_rot = []


    successful_clicks = 0

    frame_counter = 0
    frame_counter2 = 0

    low_speed_counter_translate = 0
    low_speed_counter_rotate = 0

    local_peak_speed_r = 0
    speededup = False

    inside = False

    # Logging
    hits = 0
    error = 0
    last_error = 0

    cursorContainer = None


    def __init__(self):
        self.super(taskManager).__init__()
        self.isInside = False
        self.startTime = 0
        if not environment.usePhoneCursor:
            self.rotationTarget = RotationTarget.RotationTarget(environment)#use the classical rotation targetCore class
        self.targetCore = None
        self.phone = None
        self.targetShadow = None #geometry
        self.level = 0 #when started is set to level 1
        self.cursorNode = None
        self.points = 0
        self.id_e_r = 0
        self.id_e_t = 0
        self.phoneTargetHull = None
        self.lastEndPos = None
        self.lastEndRot = None
        self.leftRight = False

        #environment.getWindow().on_key_press(self.handle_key)
        environment.setup(graph)

        if environment.usePhoneCursor:
            self.phone = Phone.Phone(environment)
            if config.showFramingBorder:
                self.phone.setErrorMargin(W_trans[self.level])
            else:
                self.phone.setErrorMargin(0)
            self.targetCore = self.phone.geometry
        else:  
            self.targetCore = loader.create_geometry_from_file(
                "modified_sphere",
                "data/objects/modified_sphere.obj",
                avango.gua.LoaderFlags.NORMALIZE_SCALE
            )

        self.targetCore.Material.value.set_uniform("Color", avango.gua.Vec4(0.8, 0.0, 0.8, 1))#avango.gua.Vec4(0.2, 0.3, 0.2, 1)
        self.targetCore.Material.value.set_uniform("Emissivity", 0.5)
        self.targetCore.Material.value.EnableBackfaceCulling.value = False
        environment.everyObject.Children.value.append(self.targetCore)

        if environment.taskDOFTranslate > 0:#show targets
            # init targetCore position
            #set position of targetCore
            self.targetCore.Transform.value = (avango.gua.make_trans_mat((self.leftRight*2-1) * environment.A_trans[self.level] / 2, 0, 0)
                * avango.gua.make_scale_mat(self.targetCore.Transform.value.get_scale()))#keep scale

            if environment.usePhoneCursor:
                if config.showFramingBorder:
                    self.phoneTargetHull = Phone.Phone(environment)
                    self.phoneTargetHull.setTranslate(avango.gua.make_trans_mat(-environment.A_trans[self.level] / 2, 0, 0))
                    self.phoneTargetHull.setErrorMargin(0)
                    environment.everyObject.Children.value.append(self.phoneTargetHull.geometry)

            #configure targetCore shadow
            if environment.usePhoneCursor:   
                self.targetShadow = loader.create_geometry_from_file(
                    "phone",
                    "/opt/3d_models/targets/phone/phoneAntennaOutlines.obj",
                    avango.gua.LoaderFlags.NORMALIZE_SCALE
                )
                Phone.setErrorMargin(self.targetShadow, W_trans[self.level])
            else:  
                self.targetShadow = loader.create_geometry_from_file(
                    "modified_sphere",
                    "data/objects/modified_sphere.obj",
                    avango.gua.LoaderFlags.NORMALIZE_SCALE
                )
                #may need to apply size here

            self.targetShadow.Material.value.set_uniform("Color", avango.gua.Vec4(0.5, 0.5, 0.5, 0.1))
            self.targetShadow.Material.value.EnableBackfaceCulling.value = False
            environment.everyObject.Children.value.append(self.targetShadow)
            #set position
            self.targetShadow.Transform.value = (avango.gua.make_trans_mat((self.leftRight*2-1) * -environment.A_trans[self.level] / 2, 0, 0)
            * avango.gua.make_scale_mat(self.targetShadow.Transform.value.get_scale()))
                    

        # loadMeshes
        self.cursorContainer = Cursor.Cursor().create(environment)
        self.cursorNode = self.cursorContainer.getNode()

        if config.taskDOFRotate > 0:
            if config.usePhoneCursor:
                if self.phone is None:
                    self.phone = Phone.Phone(environment)
                    self.phone.setErrorMargin(0)
            else:
                self.rotationTarget.setupDisks(self.cursorNode)
                self.rotationTarget.setDisksTransMats(targetDiameter[0])
                self.rotationTarget.setRotation(avango.gua.make_rot_mat(environment.A_rot[0], 0, 1, 0))
                #self.rotationTarget.setDisksTransMats(targetDiameter[0])

        # listen to button
        button_sensor = avango.daemon.nodes.DeviceSensor(DeviceService=avango.daemon.DeviceService())
        button_sensor.Station.value = "gua-device-keyboard"
        self.button.connect_from(button_sensor.Button0)

        # listen to tracked position of pointers
        pointer_device_sensor = avango.daemon.nodes.DeviceSensor(DeviceService=avango.daemon.DeviceService())
        pointer_device_sensor.TransmitterOffset.value = environment.offsetTracking

        # connect pencil->inputMatA
        pointer_device_sensor.Station.value = "pointer2"
        self.inputMatB.connect_from(pointer_device_sensor.Matrix)

        # timer
        timer = avango.nodes.TimeSensor()
        self.timer.connect_from(timer.Time)
        environment.launch(globals())

    def __del__(self):
        if environment.logResults:
            pass  # self.result_file.close()

    @field_has_changed(button)
    def button_pressed(self):
        if self.button.value:
             self.select()
        else:
            self.flagPrinted = False

    @field_has_changed(inputMatB)
    def matChanged(self):
        if config.bimanual:
            self.targetCore.Transform.value = (environment.offsetPointer
                    * avango.gua.make_trans_mat(self.inputMatB.value.get_translate())
                    * avango.gua.make_rot_mat(self.inputMatB.value.get_rotate_scale_corrected())
                    * avango.gua.make_scale_mat(self.targetCore.Transform.value.get_scale()))

    @field_has_changed(timer)
    def updateTimer(self):#each frame

        if not self.endedTests:

            # position rotationTarget
            if environment.taskDOFRotate > 0:
                if environment.taskDOFTranslate == 0\
                        or (environment.snapRotationTargetIfNear and core.getDistance3D(self.cursorNode.Transform.value, self.targetCore.Transform.value) <= W_trans[self.level]):
                    # attach rotationTarget to cursor
                    if config.usePhoneCursor:
                        self.phone.setTranslate(avango.gua.make_trans_mat(self.cursorNode.Transform.value.get_translate()))
                    else:
                        self.rotationTarget.setTranslate(avango.gua.make_trans_mat(self.cursorNode.Transform.value.get_translate()))
                else:
                    if not config.usePhoneCursor:
                        # attach rotationTarget to targetCore
                        self.rotationTarget.setTranslate(avango.gua.make_trans_mat(self.targetCore.Transform.value.get_translate()))

                highlightR = False
                if not config.usePhoneCursor:    
                    # highlight rotation if near targetCore
                    if (environment.showWhenInTarget
                        and (config.taskDOFTranslate == 0 or core.getDistance3D(self.cursorNode.Transform.value, self.targetCore.Transform.value) <= W_trans[self.level])
                        and self.getErrorRotate() < environment.W_rot[self.level] / 2
                    ):
                        highlightR = True
                        self.rotationTarget.highlightRed()
                    else:
                        self.rotationTarget.setColor()

            # highlight translation
            if config.showWhenInTarget:
                highlightT = False
                if config.taskDOFTranslate > 0:
                    if self.getErrorTranslate() < W_trans[self.level] / 2:
                        self.targetCore.Material.value.set_uniform("Color", avango.gua.Vec4(1, 0.8, 0, 0.8))
                        highlightT = True
                    else:
                        self.targetCore.Material.value.set_uniform("Color", avango.gua.Vec4(1, 1, 0, 0.8))

                if highlightT:
                    environment.setBackgroundColor(avango.gua.Color(0.1, 0.2, 0.2))
                if highlightR:
                    environment.setBackgroundColor(avango.gua.Color(0.2, 0.1, 0.0))

                if (highlightT and highlightR) or (config.taskDOFRotate == 0 and highlightT):
                    environment.setBackgroundColor(avango.gua.Color(0.3, 0.5, 0.1))

                if not highlightT and not highlightR:
                    environment.setBackgroundColor(avango.gua.Color(0.0, 0.0, 0.0))

        # set logging vars
        if self.runningTest and not self.endedTests:
            # only set starting time after animation
            if self.startTime == 0 and not self.cursorContainer.isAnimating():
                self.startTime = self.timer.value

            self.setSpeedTranslate()
            self.setSpeedRotate()
            self.frame_counter_speed += 1
            self.setAccelerationTranslate()
            self.setAccelerationRotate()
            self.frame_counter_acceleration += 1
            self.checkTranslateOvershoots()
            self.checkRotateOvershoots()
            self.checkReversalTranslate()
            self.checkReversalRotate()

        if environment.saveReplay:
            self.logReplay()

            # hack to prevent failing field connection
            # environment.cam.Transform.connect_from(environment.head_device_sensor.Matrix)

    def select(self):
        print(str(self.level) + "/"+str(config.getLevelsCount()-1)+" "+str(self.counter))
        if self.level < config.getLevelsCount() and not self.cursorContainer.isAnimating():
            # auswerten
            if self.runningTest:
                self.MT = self.timer.value - self.startTime

                if(self.MT < 0.5):
                    print("Too fast.")
                    return

                self.startTime = 0 #reset starting time
                # hit?
                if self.getErrorRotate() <= environment.W_rot[self.level] / 2 \
                    and self.getErrorTranslate() <= W_trans[self.level] / 2:
                    self.goal = True
                    pointsGet = (ID_t[self.level] + ID_r[self.level]) / self.MT
                    self.points += pointsGet
                    print("Hit! +"+str(pointsGet)+" Points")
                    if environment.provideFeedback:
                        environment.setBackgroundColor(avango.gua.Color(0, 0.2, 0.05), 0.18)
                        if environment.taskDOFRotate == 0:
                            environment.playSound("balloon")
                        else:
                            environment.playSound("hit_rotate")
                else:
                    # miss
                    self.goal = False
                    if environment.provideFeedback:
                        environment.setBackgroundColor(avango.gua.Color(0.3, 0, 0), 0.18)
                        environment.playSound("miss")

                if environment.logResults and not self.endedTests:
                    print("  "+str(self.level) + "/"+str(config.getLevelsCount())+" "+str(self.counter))
                    self.logSetter()
                    logmanager.writeToFile(environment.getFolderPath())
                    self.resetValues()
            else:
                self.lastEndPos = self.cursorNode.Transform.value.get_translate()
                self.lastEndRot = self.cursorNode.Transform.value.get_rotate_scale_corrected()
            self.button.value = False

            self.nextSettingStep()


    def nextSettingStep(self):
        self.leftRight = not self.leftRight
        if not self.runningTest:#if not running start
            self.runningTest = True
            #if self.counter > 0 and self.level < environment.config.getLevelsCount()-1:
            #    self.counter += 1
        else:
            self.counter += 1

            if self.counter % environment.levelSize == 0 and self.counter > 0:
                if environment.config.playLevelUpSound:
                    environment.playSound("levelUp")
                self.level += 1
                self.runningTest = False

        if self.runningTest:
            #environment.setBackgroundColor(avango.gua.Color(0.5, 0.5, 0.5))
            self.targetCore.Material.value.set_uniform("Color", avango.gua.Vec4(0.8, 0.0, 0.8, 1))
        else: 
            self.targetCore.Material.value.set_uniform("Color", avango.gua.Vec4(0.8, 0.8, 0.8, 1))
            #environment.setBackgroundColor(avango.gua.Color(0, 0, 0.5))

        if self.level >= environment.config.getLevelsCount():
            self.endedTests = True
            print("Your Score: " + str(self.points))
        else:
            if config.taskDOFTranslate > 0:
                # move targetCore
                self.targetCore.Transform.value = (avango.gua.make_trans_mat((self.leftRight*2-1) * environment.A_trans[self.level] / 2, 0, 0)
                    * avango.gua.make_scale_mat(W_trans[self.level]))

                self.targetShadow.Transform.value = (avango.gua.make_trans_mat((self.leftRight*2-1) * -environment.A_trans[self.level] / 2, 0, 0)
                    * avango.gua.make_rot_mat(self.targetShadow.Transform.value.get_rotate_scale_corrected())#keep rot
                    * avango.gua.make_scale_mat(self.targetShadow.Transform.value.get_scale())#keep scale
                )
                
                if config.usePhoneCursor:
                    #self.phoneTargetHull.geometry.Transform.value = (avango.gua.make_trans_mat(self.leftRight * environment.A_trans[self.level] / 2, 0, 0)
                    #* avango.gua.make_scale_mat(W_trans[self.level]))
                    if config.showFramingBorder:
                        self.phoneTargetHull.setTranslate(avango.gua.make_trans_mat((self.leftRight*2-1) * environment.A_trans[self.level] / 2, 0, 0))
                        Phone.setErrorMargin(self.phoneTargetHull.geometry, W_trans[self.level])
                    Phone.setErrorMargin(self.targetCore, 0)
                    Phone.setErrorMargin(self.targetShadow, W_trans[self.level])

            #apply rotation to targetCore
            if config.taskDOFRotate > 0:
                if environment.randomTargets:
                    if config.taskDOFRotate > 0:
                        if config.taskDOFRotate == 3:
                            rotation = self.getRandomRotation3D()
                            self.rotationTarget.setRotation(rotation)
                        else:
                            rotation = self.getRandomRotation2D()
                            self.rotationTarget.setRotation(rotation)
                else:
                    if self.leftRight:  # toggle beetwen
                        distance = environment.A_rot[self.level]
                        if config.taskDOFRotate == 3:
                            rotateAroundX = 1
                        else:
                            rotateAroundX = 0
                    else:
                        rotateAroundX = 0
                        distance = 0

                    #apply directly to targetCore if a rotation task     
                    if config.usePhoneCursor:
                        if self.phoneTargetHull is not None:
                            self.phoneTargetHull.setRotation(avango.gua.make_rot_mat(distance, rotateAroundX, 1, 0))
                        self.phone.setRotation(avango.gua.make_rot_mat(distance, rotateAroundX, 1, 0))
                        if config.showFramingBorder:
                            self.phone.setErrorMargin(W_trans[self.level])
                        else:
                            self.phone.setErrorMargin(0)
                    else: 
                        self.rotationTarget.setRotation(avango.gua.make_rot_mat(distance, rotateAroundX, 1, 0))
                        self.rotationTarget.setDisksTransMats(targetDiameter[self.level])

            if environment.animationPreview:
                if self.targetCore is None:
                    self.cursorContainer.animateTo(
                        None,
                        self.rotationTarget.getRotate()
                    )
                else:
                    self.cursorContainer.animateTo(
                        self.targetCore.Transform.value.get_translate(),
                        self.rotationTarget.getRotate()
                    )

    '''returns the error by comparing the cursorNode with the rotationTarget'''
    def getErrorRotate(self):
        if environment.taskDOFRotate > 0:
            return core.getRotationError1D(
                self.cursorNode.Transform.value.get_rotate_scale_corrected(),
                self.targetCore.Transform.value.get_rotate_scale_corrected()
            )
        return 0

    '''Get the translation error from the cursor to the target in m'''
    def getErrorTranslate(self):
        if environment.taskDOFTranslate > 0:
            return core.getDistance3D(self.cursorNode.Transform.value, self.targetCore.Transform.value)
        else:
            return 0

    def getRandomRotation3D(self):
        return avango.gua.make_rot_mat(random.uniform(0.0, environment.A_rot[self.level]), random.randint(0, 1), random.randint(0, 1), random.randint(0, 1))

    def getRandomRotation2D(self):
        return avango.gua.make_rot_mat(random.uniform(0.0, environment.A_rot[self.level]), 0, random.randint(0, 1), 0)

    def logReplay(self):
        path = environment.getFolderPath()

        if not self.endedTests:
            if not self.created_replayfile:  # create File
                self.num_files = len(glob.glob1(path, "*.csv"))
                # if os.path.isfile(os.path.join(path, f)):
                self.created_replayfile = True
            else:  # write permanent values
                self.result_file = open(path + environment.taskString + "_trial" + str(self.num_files) + ".replay",
                                        "a+")
                if environment.taskDOFTranslate > 0:
                    targetString = "Target Pos: \n" + str(self.targetCore.Transform.value) + "\n"
                else:
                    targetString = "Target Pos: \n" + str(self.cursorNode.Transform.value) + "\n"

                self.result_file.write(
                    "TimeStamp: " + str(self.timer.value) + "\n" +
                    "Pointerpos: \n" + str(self.cursorNode.Transform.value) + "\n" +
                    targetString + "\n\n")
                self.result_file.close()

    def checkTranslateOvershoots(self):
        if environment.taskDOFTranslate > 0:
            if config.usePhoneCursor and self.getErrorTranslate() < 0.01 or (not config.usePhoneCursor and self.getErrorTranslate() < self.targetCore.Transform.value.get_scale().x / 2):
                self.overshootInside_translate = True
            else:
                if self.overshootInside_translate:
                    self.overshoots_t += 1
                    self.overshootInside_translate = False

    def checkRotateOvershoots(self):
        if self.getErrorRotate() < environment.W_rot[self.level] / 2:
            self.overshootInside_rotate = True
        else:
            if self.overshootInside_rotate:
                self.overshoots_r += 1
                self.overshootInside_rotate = False

    '''returns the effective ID for the colected values. can return for rotation or translation'''
    def calcEffectiveID(self, rot, level):
        # berechne erwartungswert
        print("Level:"+str(level))
        erw = 0
        for i in range(environment.levelSize*level, environment.levelSize*(level+1)):
            if rot:
                erw += self.error_r[i]
            else: 
                erw += self.error_t[i]
        erw /= environment.levelSize # jedes ereignis ist gleich wahrscheinlich

        # berechne varianz
        varianz = 0
        for i in range(environment.levelSize*(level), environment.levelSize*(level+1)):
            if rot:
                 varianz += (self.error_r[i]-erw)*(self.error_r[i]-erw)
            else: 
                 varianz += (self.error_t[i]-erw)*(self.error_t[i]-erw)

        varianz /= environment.levelSize # jedes ereignis ist gleich wahrscheinlich

        # berechne standardabweichung
        sd = math.sqrt(varianz)

        # berechne effektive breite
        W_e = 4.133*sd

        #effektive amplitude translate
        sumOfA = 0
        for i in range(environment.levelSize*(level), environment.levelSize*(level+1)):
            if rot:
                 sumOfA += self.eff_A_rot[i]
            else: 
                 sumOfA += self.eff_A_trans[i]

        A_e = sumOfA/environment.levelSize # jedes ereignis ist gleich wahrscheinlich

        # effektiver ID
        if rot: 
            self.id_e_r = math.log(2*A_e / W_e, 2)
        else:
            self.id_e_t = math.log(2*A_e / W_e, 2)

    # sets the fields in the logmanager
    def logSetter(self):
        # record the rotation error
        self.error_r.append(self.getErrorRotate())
        self.error_t.append(self.getErrorTranslate())
        self.eff_A_trans.append((self.lastEndPos - self.cursorNode.Transform.value.get_translate()).length())
        self.eff_A_rot.append(core.getRotationError1D(self.lastEndRot, self.cursorNode.Transform.value.get_rotate_scale_corrected()))

        #berechne effektiven ID
        if environment.levelSize > 1 and self.counter % environment.levelSize == environment.levelSize - 1:# is at end of level
            if environment.logEffectiveForR and environment.taskDOFRotate>0:
                self.calcEffectiveID(True, self.level)
            if environment.logEffectiveForT and environment.taskDOFTranslate>0:
                self.calcEffectiveID(False, self.level)
        else:
            self.id_e_r = 0
            self.id_e_t = 0

        if environment.useAutoDetect:
            hit_type = "Auto"
        else:
            hit_type = "Manual"
            self.clicks += 1
            if self.goal:
                self.successful_clicks += 1

        logmanager.set("User Id", environment.userId)
        logmanager.set("Group", environment.groupId)

        if environment.space3D:
            logmanager.set("DOF real T", 3)
            logmanager.set("DOF real R", 3)
        else:
            logmanager.set("DOF real T", 2)
            logmanager.set("DOF real R", 1)
        logmanager.set("DOF virtual T", environment.getDOFTranslateVirtual())
        logmanager.set("DOF virtual R", environment.virtualDOFRotate)
        logmanager.set("task R DOF", environment.taskDOFRotate)
        logmanager.set("task T DOF", environment.taskDOFTranslate)
        # if environment.taskDOFTranslate > 0:
        #     logmanager.set(
        #         "movement direction",
        #         self.targetCore.Transform.value.get_translate() - self.targetShadow.Transform.value.get_translate()
        #     )
        
        #if environment.taskDOFTranslate > 0:
        logmanager.set("target distance T [m]", environment.A_trans[self.level])
        logmanager.set("target width T [m]", W_trans[self.level])
    #if environment.taskDOFRotate > 0:
        logmanager.set("target distance R [m]", environment.A_rot[self.level])
        logmanager.set("target width R [m]", W_rot[self.level])

        ID_R = 0
        ID_T = 0
        if environment.logEffectiveForR:
            ID_R = self.id_e_r
            logmanager.set("ID effective R [bit]", ID_R)
        else:
            if environment.taskDOFRotate > 0:#has rotation
                ID_R = ID_r[self.level]
            if (ID_R==0):
                logmanager.set("ID effective R [bit]", "-")
            else:
                logmafnager.set("ID R [bit]", ID_R)

        if environment.logEffectiveForT:
            ID_T = self.id_e_t
            if (ID_T==0):
                logmanager.set("ID effective T [bit]", "-")
            else:
                logmanager.set("ID effective T [bit]", ID_T)
        else:
            if environment.taskDOFTranslate != 0:#has translation
                ID_T = ID_t[self.level]
            logmanager.set("ID T", ID_T)

        logmanager.set("ID combined [bit]", (ID_R + ID_T))
        logmanager.set("repetition", environment.levelSize)
        logmanager.set("trial", self.counter)
        logmanager.set("button clicks", self.clicks)
        logmanager.set("successful clicks", self.successful_clicks)

        if self.goal:
            logmanager.set("Hit", 1)
        else:
            logmanager.set("Hit", 0)

        logmanager.set("hit type", hit_type)
        logmanager.set("MT [s]", self.MT)        

        #if environment.taskDOFTranslate > 0:#has translation
        logmanager.set("effective end pos", self.cursorNode.Transform.value.get_translate())
        logmanager.set("effective A trans [m]", (self.lastEndPos - self.cursorNode.Transform.value.get_translate()).length())
        self.lastEndPos = self.cursorNode.Transform.value.get_translate()
         
        logmanager.set("overshoots T", self.overshoots_t)
        logmanager.set("peak acceleration T [m/s^2]", self.peak_acceleration_t)
        if self.peak_acceleration_t > 0:
            logmanager.set("movement continuity T", self.first_reversal_acceleration_t / self.peak_acceleration_t)
        else:
            logmanager.set("movement continuity T", "#div0")
        logmanager.set("error T [m]", self.getErrorTranslate())
        logmanager.set("peak speed T [m/s]", self.peak_speed_t)
        logmanager.set("first reversal T", self.first_reversal_point_t)
        logmanager.set("reversal points T", len(self.reversal_points_t))

        #if environment.taskDOFRotate > 0:#has rotation  
        logmanager.set("effective end rot", self.cursorNode.Transform.value.get_rotate_scale_corrected())
        logmanager.set("effective A rot [m]", core.getRotationError1D(self.lastEndRot, self.cursorNode.Transform.value.get_rotate_scale_corrected())) 
        self.lastEndRot = self.cursorNode.Transform.value.get_rotate_scale_corrected()
        logmanager.set("overshoots R", self.overshoots_r)
        logmanager.set("peak acceleration R [°/s^2]", self.peak_acceleration_r)

        if self.peak_acceleration_r > 0:
            logmanager.set("movement continuity R", self.first_reversal_acceleration_rotate / self.peak_acceleration_r)
        else:
            logmanager.set("movement continuity R", "#div0")
        logmanager.set("error R", self.getErrorRotate())    
        logmanager.set("peak speed R", self.peak_speed_r)

        logmanager.set("first reversal R", self.first_reversal_point_r)
        logmanager.set("reversal points R", len(self.reversal_points_r))

        if environment.config.usePhoneCursor:
            logmanager.set("Cursor", "Phone")
        elif environment.config.showHuman:
            logmanager.set("Cursor", "Human")
        else:
            logmanager.set("Cursor", "Cursor")

    def setSpeedRotate(self):
        if self.frame_counter_speed % 5 == 0:
            self.PencilRotation1 = self.cursorNode.Transform.value.get_rotate_scale_corrected()
            self.start_time_rotate_speed = self.timer.value
        else:
            if self.frame_counter_speed % 5 == FRAMES_FOR_SPEED - 1:
                self.PencilRotation2 = self.cursorNode.Transform.value.get_rotate_scale_corrected()
                self.end_time_rotate_speed = self.timer.value
                div = core.getRotationError1D(self.PencilRotation1, self.PencilRotation2)
                time = self.end_time_rotate_speed - self.start_time_rotate_speed
                self.current_speed_rotate = div / time

                if self.current_speed_rotate < 0.001:
                    self.current_speed_rotate = 0

                if self.current_speed_rotate > self.peak_speed_r:
                    self.peak_speed_r = self.current_speed_rotate

                if self.current_speed_rotate > self.local_peak_speed_r:
                    self.local_peak_speed_r = self.current_speed_rotate

    def setSpeedTranslate(self):
        if self.frame_counter_speed % 5 == 0:
            self.TransTranslation1 = self.cursorNode.Transform.value.get_translate()
            self.start_time_translate_speed = self.timer.value
        else:
            if self.frame_counter_speed % 5 == FRAMES_FOR_SPEED - 1:
                self.TransTranslation2 = self.cursorNode.Transform.value.get_translate()
                self.end_time_translate_speed = self.timer.value
                div = self.TransTranslation2 - self.TransTranslation1
                length = math.sqrt(div.x ** 2 + div.y ** 2 + div.z ** 2)
                time = self.end_time_translate_speed - self.start_time_translate_speed
                self.current_speed_translate = length / time

                if self.current_speed_translate < 10 ** -3:  # noise filter
                    self.current_speed_translate = 0

                if self.current_speed_translate > self.peak_speed_t:
                    self.peak_speed_t = self.current_speed_translate

    def setAccelerationTranslate(self):
        if self.frame_counter_acceleration % 5 == 0:
            self.speed_at_start_translate = self.current_speed_translate
            self.start_time_translate = self.timer.value
        else:
            if self.frame_counter_acceleration % 5 == FRAMES_FOR_SPEED - 1:

                div = self.current_speed_translate - self.speed_at_start_translate
                time = self.timer.value - self.start_time_translate

                self.current_acceleration_translate = div / time

                if self.current_acceleration_translate > self.peak_acceleration_t:
                    self.peak_acceleration_t = self.current_acceleration_translate

    def setAccelerationRotate(self):
        if self.frame_counter_acceleration % 5 == 0:
            self.speed_at_start_rotate = self.current_speed_rotate
            self.start_time_rotate = self.timer.value
        else:
            if self.frame_counter_acceleration % 5 == FRAMES_FOR_SPEED - 1:
                div = self.current_speed_rotate - self.speed_at_start_rotate
                time = self.timer.value - self.start_time_rotate
                self.current_acceleration_rotate = div / time

                # noise filter
                if math.fabs(self.current_acceleration_rotate) < 1:
                    self.current_acceleration_rotate = 0

                if self.current_acceleration_rotate > self.peak_acceleration_r:
                    self.peak_acceleration_r = self.current_acceleration_rotate

    def checkReversalTranslate(self):
        if math.fabs(self.current_speed_translate) < THRESHHOLD_TRANSLATE < self.peak_speed_t:
            if self.low_speed_counter_translate < FRAMES_FOR_AUTODETECT_TRANSLATE - 1:
                self.low_speed_counter_translate += 1
            else:
                self.low_speed_counter_translate = 0
                if self.first_translate:
                    self.first_reversal_point_t = self.getErrorTranslate()
                    self.first_reversal_acceleration_t = self.current_acceleration_translate
                    self.first_translate = False
                    self.reversal_points_t.append(self.first_reversal_point_t)
                else:
                    self.reversal_points_t.append(self.getErrorTranslate())

 
    def checkReversalRotate(self):
        # print ("Rotation Speed: "+str(self.current_speed_rotate))
        if math.fabs(self.current_speed_rotate) < 40 < self.peak_speed_r:
            if self.low_speed_counter_rotate < FRAMES_FOR_AUTODETECT_ROTATE - 1:
                self.low_speed_counter_rotate += 1
            else:
                self.low_speed_counter_rotate = 0
                if self.first_rotate:
                    self.first_reversal_point_r = self.getErrorRotate()
                    self.first_reversal_acceleration_rotate = self.current_acceleration_rotate
                    self.reversal_points_r.append(self.first_reversal_point_r)
                    self.first_rotate = False
                    #self.button.value = True

                if self.local_peak_speed_r > 100:
                    self.speededup = True
                    self.local_peak_speed_r = 0

                if self.speededup:
                    self.reversal_points_r.append(self.getErrorRotate())
                    if(environment.config.useAutoDetect):
                        if(self.getErrorRotate() <= W_rot[self.level]):
                            self.button.value = True

                    self.speededup = False

        else:
            self.low_speed_counter_rotate = 0

    def resetValues(self):
        self.overshoots_t = 0
        self.overshoots_r = 0
        self.peak_speed_t = 0
        self.peak_acceleration_t = 0
        self.peak_speed_r = 0
        self.peak_acceleration_r = 0
        self.reversal_points_t = []
        self.reversal_points_r = []
        self.first_translate = True
        self.first_rotate = True

    def setTP(self, index):
        if self.MT > 0 and self.level < environment.config.getLevelsCount():
            self.TP = (ID_t[index]+ID_r[index]) / self.MT

    def handle_key(self, key, scancode, action, mods):
        if action == 1:
            # 32 is space 335 is num_enter
            if key == 32 or key == 335:
                if self.endedTests:
                    print("Test ended")
                else:
                    self.button.value = True

if __name__ == '__main__':
    environment = core.setupEnvironment()

    if len(sys.argv) > 2:
        environment.userId = int(sys.argv[1])
        environment.groupId = int(sys.argv[2])

    environment.create()
    config = environment.config

    # fitt's law parameter

    ID_t = environment.ID_t
    ID_r = environment.ID_r

    W_rot = environment.W_rot
    W_trans = environment.W_trans


    targetDiameter = []
    for i in range(0, config.getLevelsCount()):
        #if not environment.randomTargets:
        #    W_rot.append(core.IDtoW(ID[int(i/environment.levelSize)], environment.A_rot[int(i/environment.levelSize)]))  # in degrees, Fitt's Law umgeformt nach W
        #    W_trans.append(core.IDtoW(ID[int(i/environment.levelSize)], environment.A_trans[int(i/environment.levelSize)]))  # in degrees, Fitt's Law umgeformt nach W
        #else:
        #    W_rot.append(i*2+2)  # in degrees
        #    W_trans.append(core.IDtoW(ID[int(i/environment.levelSize)], environment.A_trans[int(i/environment.levelSize)]))  # in degrees, Fitt's Law umgeformt nach W

        # add ID wenn es noch einen Rotations-Anteil gibt
        if environment.taskDOFRotate > 0:
            targetDiameter.append(2 * environment.r * math.tan(environment.W_rot[i] * math.pi / 180))  # größe (Durchmesser) der Gegenkathete auf dem kreisumfang

    THRESHHOLD_TRANSLATE = 0.3
    FRAMES_FOR_AUTODETECT_TRANSLATE = 3

    FRAMES_FOR_AUTODETECT_ROTATE = 3
    THRESHHOLD_ROTATE = 60
    FRAMES_FOR_SPEED = 4  # How many frames taken to calculate speed and acceleration

    graph = avango.gua.nodes.SceneGraph(Name="scenegraph")  # Create Graph
    loader = avango.gua.nodes.TriMeshLoader()  # Create Loader
    pencil_transform = avango.gua.nodes.TransformNode()

    logmanager = environment.logmanager    
    taskManager = taskManager()