# coding=utf-8
import math
import glob

import avango
import avango.daemon
import avango.gua
import avango.script
import core
import BoundsContainer
import Cursor
import LogManager
import random
from avango.script import field_has_changed

print(
    "Welcome to the VR motor movement study application. To change the parameters and/or change the group and user id open the 'core.py'.")
environment = core.setupEnvironment().create()

# fitt's law parameter

ID = environment.ID

W_rot = environment.W_rot
W_trans = environment.W_trans


targetDiameter = []
for i in range(0, environment.config.getTrialsCount()):
    #if not environment.randomTargets:
    #    W_rot.append(core.IDtoW(ID[int(i/environment.levelSize)], environment.D_rot[int(i/environment.levelSize)]))  # in degrees, Fitt's Law umgeformt nach W
    #    W_trans.append(core.IDtoW(ID[int(i/environment.levelSize)], environment.D_trans[int(i/environment.levelSize)]))  # in degrees, Fitt's Law umgeformt nach W
    #else:
    #    W_rot.append(i*2+2)  # in degrees
    #    W_trans.append(core.IDtoW(ID[int(i/environment.levelSize)], environment.D_trans[int(i/environment.levelSize)]))  # in degrees, Fitt's Law umgeformt nach W

    # add ID wenn es noch einen Rotations-Anteil gibt
    if environment.taskDOFRotate > 0:
        targetDiameter.append(2 * environment.r * math.tan(environment.W_rot[i] * math.pi / 180))  # größe (Durchmesser) der Gegenkathete auf dem kreisumfang

THRESHHOLD_TRANSLATE = 0.3
FRAMES_FOR_AUTODETECT_TRANSLATE = 3

FRAMES_FOR_AUTODETECT_ROTATE = 3
THRESHHOLD_ROTATE = 40
FRAMES_FOR_SPEED = 4  # How many frames taken to calculate speed and acceleration

graph = avango.gua.nodes.SceneGraph(Name="scenegraph")  # Create Graph
loader = avango.gua.nodes.TriMeshLoader()  # Create Loader
pencil_transform = avango.gua.nodes.TransformNode()

logmanager = LogManager.LogManager()


class trackingManager(avango.script.Script):
    Button = avango.SFBool()
    timer = avango.SFFloat()

    time2 = 0

    startedTests = False
    endedTests = False

    created_logfile = False
    created_replayfile = False

    current_level = 0
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
        self.super(trackingManager).__init__()
        self.isInside = False
        self.startTime = 0
        self.boundsContainer = BoundsContainer.DisksContainer(environment)
        self.aim = None
        self.aimShadow = None
        self.level = 0
        self.cursorNode = None
        self.points = 0
        self.id_e = 0

    def __del__(self):
        if environment.logResults:
            pass  # self.result_file.close()

    @field_has_changed(Button)
    def button_pressed(self):
        if self.Button.value:
             self.select()
        else:
            self.flagPrinted = False

    @field_has_changed(timer)
    def updateTimer(self):
        if not self.endedTests:
            highlightR = False

            # position boundsContainer2
            if environment.taskDOFRotate > 0:
                if environment.taskDOFTranslate == 0\
                        or (environment.snapBoundsContainerIfNear and core.getDistance3D(self.cursorNode.Transform.value, self.aim.Transform.value) <= W_trans[self.counter]):
                    # attach boundsContainer to cursor
                    self.boundsContainer.setTranslate(avango.gua.make_trans_mat(self.cursorNode.Transform.value.get_translate()))
                else:
                    # attach boundsContainer to aim
                    self.boundsContainer.setTranslate(avango.gua.make_trans_mat(self.aim.Transform.value.get_translate()))

                # highlight rotation if near target
                if (environment.showWhenInTarget
                    and (environment.taskDOFTranslate == 0 or core.getDistance3D(self.cursorNode.Transform.value, self.aim.Transform.value) <= W_trans[self.counter])
                    and self.getErrorRotate() < environment.W_rot[self.counter] / 2
                ):
                    highlightR = True
                    self.boundsContainer.highlightRed()
                else:
                    self.boundsContainer.setColor()

            # highlight translation
            highlightT = False
            if environment.showWhenInTarget:
                if environment.taskDOFTranslate > 0:
                    if self.getErrorTranslate() < W_trans[self.counter] / 2:
                        self.aim.Material.value.set_uniform("Color", avango.gua.Vec4(1, 0.8, 0, 0.8))
                        highlightT = True
                    else:
                        self.aim.Material.value.set_uniform("Color", avango.gua.Vec4(1, 1, 0, 0.8))

            if highlightT:
                environment.setBackgroundColor(avango.gua.Color(0.1, 0.2, 0.2))
            if highlightR:
                environment.setBackgroundColor(avango.gua.Color(0.2, 0.1, 0.0))

            if (highlightT and highlightR) or (environment.taskDOFRotate == 0 and highlightT):
                environment.setBackgroundColor(avango.gua.Color(0.3, 0.5, 0.1))

            if (not highlightT) and (not highlightR):
                environment.setBackgroundColor(avango.gua.Color(0.0, 0.0, 0.0))

        # set logging vars
        if self.startedTests and not self.endedTests:
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
        if self.level < environment.config.getTrialsCount() and not self.cursorContainer.isAnimating():
            # auswerten
            if self.startedTests:
                self.MT = self.timer.value - self.startTime
                self.startTime = 0 #reset starting time
                self.points += ID[self.level] + ID[self.level] / self.MT

                if self.getErrorRotate() < environment.W_rot[self.counter] / 2 and self.getErrorTranslate() < W_trans[self.counter] / 2:
                    # hit
                    self.goal = True
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
                    self.logSetter()
                    environment.logData(logmanager)
                    self.resetValues()

            self.nextSettingStep()

    def nextSettingStep(self):
        if not self.startedTests:
            self.startedTests = True
        else:
            self.counter += 1

        if self.counter % environment.levelSize == environment.levelSize - 1:
            if environment.config.playLevelUpSound:
                environment.playSound("levelUp")
            self.level += 1

        if self.level == environment.config.getTrialsCount():
            self.endedTests = True
            environment.setBackgroundColor(avango.gua.Color(0, 0, 0.5))
            print("Your Score: " + str(self.points))

        # print("P:"+str( pencilRot )+"")
        # print("T:"+str( self.disksMat.value.get_rotate_scale_corrected() )+"")
        if self.level < environment.config.getTrialsCount():
            if environment.taskDOFTranslate > 0:
                # move target
                sign = 1
                if self.counter % 2 == 1:
                    sign = -1

                self.aim.Transform.value = avango.gua.make_trans_mat(sign * environment.D_trans[self.level] / 2, 0, 0) * avango.gua.make_scale_mat(W_trans[self.counter])
                self.aimShadow.Transform.value = avango.gua.make_trans_mat(sign * -environment.D_trans[self.level] / 2, 0, 0) * avango.gua.make_scale_mat(W_trans[self.counter])

            if environment.randomTargets:
                if environment.taskDOFRotate > 0:
                    if environment.taskDOFRotate == 3:
                        rotation = self.getRandomRotation3D()
                        self.boundsContainer.setRotation(rotation)
                    else:
                        rotation = self.getRandomRotation2D()
                        self.boundsContainer.setRotation(rotation)
            else:
                if environment.taskDOFRotate > 0:
                    if self.counter % 2 == 0:  # toggle beetwen
                        distance = environment.D_rot[self.level]
                        if environment.taskDOFRotate == 3:
                            rotateAroundX = 1
                        else:
                            rotateAroundX = 0
                    else:
                        rotateAroundX = 0
                        distance = 0

                    self.boundsContainer.setRotation(avango.gua.make_rot_mat(distance, rotateAroundX, 1, 0))
                    self.boundsContainer.setDisksTransMats(targetDiameter[self.counter])

            self.boundsContainer.setErrorMargin(environment.W_trans[self.counter])#todo should be W_t

            if environment.animationPreview:
                if self.aim is None:
                    self.cursorContainer.animateTo(
                        None,
                        self.boundsContainer.getRotate()
                    )
                else:
                    self.cursorContainer.animateTo(
                        self.aim.Transform.value.get_translate(),
                        self.boundsContainer.getRotate()
                    )

    def getErrorRotate(self):
        if environment.taskDOFRotate > 0:
            return core.getRotationError1D(
                self.cursorNode.Transform.value.get_rotate_scale_corrected(),
                self.boundsContainer.getRotate()
            )
        return 0

    '''Get the translation error from the cursor to the aim in m'''
    def getErrorTranslate(self):
        if environment.taskDOFTranslate > 0:
            return core.getDistance3D(self.cursorNode.Transform.value, self.aim.Transform.value)
        else:
            return 0

    def getRandomRotation3D(self):
        return avango.gua.make_rot_mat(random.uniform(0.0, environment.D_rot[self.level]), random.randint(0, 1), random.randint(0, 1), random.randint(0, 1))

    def getRandomRotation2D(self):
        return avango.gua.make_rot_mat(random.uniform(0.0, environment.D_rot[self.level]), 0, random.randint(0, 1), 0)

    def logReplay(self):
        path = environment.getPath()

        if not self.endedTests:
            if not self.created_replayfile:  # create File
                self.num_files = len(glob.glob1(path, "*.csv"))
                # if os.path.isfile(os.path.join(path, f)):
                self.created_replayfile = True
            else:  # write permanent values
                self.result_file = open(path + environment.taskString + "_trial" + str(self.num_files) + ".replay",
                                        "a+")
                if environment.taskDOFTranslate > 0:
                    aimString = "Aimpos: \n" + str(self.aim.Transform.value)
                else:
                    aimString = "Aimpos: \nnone"

                self.result_file.write(
                    "TimeStamp: " + str(self.timer.value) + "\n" +
                    "ErrorRotalen(te: " + str(self.getErrorRotate()) + "\n" +
                    "Pointerpos: \n" + str(self.cursorNode.Transform.value) + "\n" +
                    aimString + "\n\n")
                self.result_file.close()

    def checkTranslateOvershoots(self):
        if environment.taskDOFTranslate > 0:
            if self.getErrorTranslate() < self.aim.Transform.value.get_scale().x / 2:
                self.overshootInside_translate = True
            else:
                if self.overshootInside_translate:  #
                    self.overshoots_t += 1
                    self.overshootInside_translate = False

    def checkRotateOvershoots(self):
        if self.getErrorRotate() < environment.W_rot[self.counter] / 2:
            self.overshootInside_rotate = True
        else:
            if self.overshootInside_rotate:
                self.overshoots_r += 1
                self.overshootInside_rotate = False

    # sets the fields in the logmanager
    def logSetter(self):
        if self.getErrorRotate() < environment.W_rot[self.counter] / 2 and self.getErrorTranslate() < W_trans[self.counter] / 2:
            self.goal = True
        else:
            self.goal = False

        # record the rotation error
        self.error_r.append(self.getErrorRotate())

        if environment.levelSize > 1 and self.counter % environment.levelSize == environment.levelSize - 1:# is at end of level
            # berechne erwartungswert
            erw = 0
            for i in range(environment.levelSize*self.level, environment.levelSize*(self.level+1)):
                erw += self.error_r[i]
            erw /= environment.levelSize # jedes ereignis ist gleich wahrscheinlich

            # berechne varianz
            varianz = 0
            for i in range(environment.levelSize*self.level, environment.levelSize*(self.level+1)):
                varianz += (self.error_r[i]-erw)*(self.error_r[i]-erw)
            varianz /= environment.levelSize # jedes ereignis ist gleich wahrscheinlich

            # berechne standardabweichung
            sd = math.sqrt(varianz)

            # berechne effektive breite
            W_e = 4.133*sd

            if environment.logEffectiveForR:
                # effektiver ID
                self.id_e = math.log(2*environment.D_rot[self.level] / W_e, 2)
            elif environment.logEffectiveForT:
                # effektiver ID
                self.id_e = math.log(2*environment.D_trans[self.level] / W_e, 2)
        else:
            self.id_e = 0

        if environment.useAutoDetect:
            hit_type = "Auto"
        else:
            hit_type = "Manual"
            self.clicks += 1
            if self.goal:
                self.successful_clicks += 1

        logmanager.set("User Id", environment.userId)
        logmanager.set("Group", environment.group)

        if environment.space3D:
            logmanager.set("DOF real T", 3)
            logmanager.set("DOF real R", 3)
        else:
            logmanager.set("DOF real T", 2)
            logmanager.set("DOF real R", 1)
        logmanager.set("DOF virtual T", environment.getDOFTranslateVirtual())
        logmanager.set("DOF virtual R", environment.virtualDOFRotate)
        logmanager.set("task R DOF", environment.taskDOFRotate)
        if environment.taskDOFTranslate > 0:
            logmanager.set("movement direction",
                       self.aim.Transform.value.get_translate() - self.aimShadow.Transform.value.get_translate())
        else:
            logmanager.set("movement direction", "(0.0  0.0  0.0)")

        logmanager.set("target distance T", environment.D_trans[self.counter])
        logmanager.set("target width T", W_trans[self.counter])
        logmanager.set("target distance R", environment.D_rot[self.counter])
        logmanager.set("target width R", W_rot[self.counter])
        logmanager.set("ID combined", ID[self.level] + ID[self.counter])  # add and rot
        if environment.taskDOFRotate == 0:#no rotation
            logmanager.set("ID T", ID[self.level])
            logmanager.set("ID R", 0)
        else:
            logmanager.set("ID T", ID[self.counter])
            logmanager.set("ID R ", ID[self.counter])
        logmanager.set("ID effective ", self.id_e)
        logmanager.set("repetition", environment.levelSize)
        logmanager.set("trial", self.counter)
        logmanager.set("Button clicks", self.clicks)
        logmanager.set("succesfull clicks", self.successful_clicks)
        if self.goal:
            logmanager.set("Hit", 1)
        else:
            logmanager.set("Hit", 0)
        logmanager.set("overshoots R", self.overshoots_r)
        logmanager.set("overshoots T", self.overshoots_t)
        logmanager.set("peak acceleration T", self.peak_acceleration_t)
        logmanager.set("peak acceleration R", self.peak_acceleration_r)
        if self.peak_acceleration_r > 0:
            logmanager.set("movement continuity R", self.first_reversal_acceleration_rotate / self.peak_acceleration_r)
        else:
            logmanager.set("movement continuity R", "#div0")
        if self.peak_acceleration_t > 0:
            logmanager.set("movement continuity T", self.first_reversal_acceleration_t / self.peak_acceleration_t)
        else:
            logmanager.set("movement continuity T", "#div0")
        logmanager.set("peak speed R", self.peak_speed_r)
        logmanager.set("peak speed T", self.peak_speed_t)
        logmanager.set("hit type", hit_type)
        logmanager.set("MT", self.MT)
        logmanager.set("error R", self.getErrorRotate())
        logmanager.set("error T", self.getErrorTranslate())
        logmanager.set("first reversal R", self.first_reversal_point_r)
        logmanager.set("first reversal T", self.first_reversal_point_t)
        logmanager.set("reversal points R", len(self.reversal_points_r))
        logmanager.set("reversal points T", len(self.reversal_points_t))

    def setSpeedRotate(self):
        if self.frame_counter_speed % 5 == 0:
            self.PencilRotation1 = self.cursorNode.Transform.value.get_rotate()
            self.start_time = self.timer.value
        else:
            if self.frame_counter_speed % 5 == FRAMES_FOR_SPEED - 1:
                self.PencilRotation2 = self.cursorNode.Transform.value.get_rotate()
                self.end_time = self.timer.value
                div = core.getRotationError1D(self.PencilRotation1, self.PencilRotation2)
                time = self.end_time - self.start_time
                self.current_speed_rotate = div / time

                if self.current_speed_rotate < 10 ** -3:
                    self.current_speed_rotate = 0

                if self.current_speed_rotate > self.peak_speed_r:
                    self.peak_speed_r = self.current_speed_rotate

                if self.current_speed_rotate > self.local_peak_speed_r:
                    self.local_peak_speed_r = self.current_speed_rotate

        print (self.current_speed_rotate)

    def setSpeedTranslate(self):
        if self.frame_counter_speed % 5 == 0:
            self.TransTranslation1 = self.cursorNode.Transform.value.get_translate()
            self.start_time = self.timer.value
        else:
            if self.frame_counter_speed % 5 == FRAMES_FOR_SPEED - 1:
                self.TransTranslation2 = self.cursorNode.Transform.value.get_translate()
                self.end_time = self.timer.value
                div = self.TransTranslation2 - self.TransTranslation1
                length = math.sqrt(div.x ** 2 + div.y ** 2 + div.z ** 2)
                time = self.end_time - self.start_time
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
                    self.first_reversal_point_t = self.cursorNode.Transform.value.get_translate().x
                    self.first_reversal_acceleration_t = self.current_acceleration_translate
                    self.first_translate = False
                self.reversal_points_t.append(self.cursorNode.Transform.value.get_translate().x)

    def checkReversalRotate(self):
        if math.fabs(self.current_speed_rotate) < THRESHHOLD_ROTATE < self.peak_speed_r:
            if self.low_speed_counter_rotate < FRAMES_FOR_AUTODETECT_ROTATE - 1:
                self.low_speed_counter_rotate += 1
            else:
                self.low_speed_counter_rotate = 0
                if self.first_rotate:
                    self.first_reversal_point_r = self.cursorNode.Transform.value.get_rotate().get_angle()
                    self.first_reversal_acceleration_rotate = self.current_acceleration_rotate
                    self.reversal_points_r.append(self.first_reversal_point_r)
                    self.first_rotate = False

                if self.local_peak_speed_r > THRESHHOLD_ROTATE:
                    self.speededup = True
                    self.local_peak_speed_r = 0

                if self.speededup:
                    self.reversal_points_r.append(self.cursorNode.Transform.value.get_rotate().get_angle())
                    self.speededup = False

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
        if self.MT > 0 and self.current_level < environment.config.getTrialsCount():
            self.TP = ID[index] / self.MT

    def handle_key(self, key, scancode, action, mods):
        if action == 1:
            # 32 is space 335 is num_enter
            if key == 32 or key == 335:
                if self.endedTests:
                    print("Test ended")
                else:
                    self.Button.value = True


def start():
    trackManager = trackingManager()

    environment.getWindow().on_key_press(trackManager.handle_key)
    environment.setup(graph)

    if environment.taskDOFTranslate > 0:
        trackManager.aim = loader.create_geometry_from_file(
            "modified_sphere",
            "data/objects/modified_sphere.obj",
            avango.gua.LoaderFlags.NORMALIZE_SCALE
        )
        trackManager.aim.Transform.value = (
            avango.gua.make_trans_mat(-environment.D_trans[0] / 2, 0, 0)
            * avango.gua.make_scale_mat(W_trans[0])
        )
        trackManager.aim.Material.value.set_uniform("Color", avango.gua.Vec4(0, 1, 0, 0.8))
        trackManager.aim.Material.value.EnableBackfaceCulling.value = False
        environment.everyObject.Children.value.append(trackManager.aim)

        trackManager.aimShadow = loader.create_geometry_from_file(
            "modified_sphere",
            "data/objects/modified_sphere.obj",
            avango.gua.LoaderFlags.NORMALIZE_SCALE
        )
        trackManager.aimShadow.Transform.value = avango.gua.make_trans_mat(
            environment.D_trans[0] / 2, 0, 0 )\
             * avango.gua.make_scale_mat(W_trans[0]
        )
        trackManager.aimShadow.Material.value.set_uniform("Color", avango.gua.Vec4(0.5, 0.5, 0.5, 0.1))
        trackManager.aimShadow.Material.value.EnableBackfaceCulling.value = False
        environment.everyObject.Children.value.append(trackManager.aimShadow)

    # loadMeshes
    trackManager.cursorContainer = Cursor.Cursor().create(environment)
    trackManager.cursorNode = trackManager.cursorContainer.getNode()

    if environment.taskDOFRotate > 0:
        trackManager.boundsContainer.setupDisks(trackManager.cursorNode)
        trackManager.boundsContainer.setDisksTransMats(targetDiameter[0])
        trackManager.boundsContainer.setRotation(avango.gua.make_rot_mat(environment.D_rot[0], 0, 1, 0))
        #trackManager.boundsContainer.setDisksTransMats(targetDiameter[0])

    # listen to button
    button_sensor = avango.daemon.nodes.DeviceSensor(DeviceService=avango.daemon.DeviceService())
    button_sensor.Station.value = "device-pointer"
    trackManager.Button.connect_from(button_sensor.Button0)

    # timer
    timer = avango.nodes.TimeSensor()
    trackManager.timer.connect_from(timer.Time)

    environment.launch(globals())


if __name__ == '__main__':
    start()
