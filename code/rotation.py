# coding=utf-8

import avango
import avango.daemon
import avango.gua
import avango.script
import random
import core
import LogManager
import math
import glob

from examples_common.GuaVE import GuaVE
from avango.script import field_has_changed

FRAMES_FOR_SPEED = 4
FRAMES_FOR_AUTODETECT = 3
THRESHHOLD = 40

print(
    "Welcome to the VR motor movement study application. To change the parameters and/or cahnge the group and user id open the 'core.py'.")
environment = core.setupEnvironment().create(int(input("Config Number: ")))

rotation2D = [avango.gua.make_rot_mat(20, 1, 0.8, 0),
              avango.gua.make_rot_mat(90, 0.1, 0.2, 0)]

rotation3D = [avango.gua.make_rot_mat(20, 1, 0.8, 0.3),
              avango.gua.make_rot_mat(90, 0.1, 0.2, 0.9)]

ID = environment.ID
W_rot = []

for i in range(0, len(ID)):
    if environment.randomTargets:
        environment.D_rot = [
            environment.getRotationError1D(rotation2D[0].get_rotate(), rotation2D[1].get_rotate())]  # in degrees
        W_rot = [core.IDtoW(ID[0], environment.D_rot[0]), core.IDtoW(ID[1], environment.D_rot[1]),
                 core.IDtoW(ID[2], environment.D_rot[2])]  # in degrees, Fitt's Law umgeformt nach W_rot
    else:
        environment.D_rot = 100
        W_rot.append(core.IDtoW(ID[i], environment.D_rot))

targetDiameter = [
    2 * environment.r * math.tan(W_rot[0] / 2 * math.pi / 180),
    2 * environment.r * math.tan(W_rot[1] / 2 * math.pi / 180),
    2 * environment.r * math.tan(W_rot[2] / 2 * math.pi / 180)
]  # größe (Druchmesser) der Gegenkathete auf dem kreisumfang

# print(targetDiameter)

graph = avango.gua.nodes.SceneGraph(Name="scenegraph")  # Create Graph
pencil_transform = avango.gua.nodes.TransformNode()

logmanager = LogManager.LogManager()


class trackingManager(avango.script.Script):
    Button = avango.SFBool()
    timer = avango.SFFloat()

    PencilRotation1 = None
    PencilRotation2 = None

    lastTime = 0

    startedTests = False
    endedTests = False

    created_replayfile = False
    flagPrinted = False

    index = 0
    counter = 0

    frame_counter = 0
    frame_counter2 = 0
    start_time1 = 0
    start_time2 = 0
    end_time2 = 0
    end_time1 = 0

    current_speed = 0
    current_acceleration = 0
    peak_acceleration_r = 0
    peak_speed_r = 0
    speed_time1 = 0
    speed_time2 = 0
    first = False
    reversal_points_r = []
    first_reversal_acceleration_r = 0
    first_reversal_point_r = 0
    low_speed_counter = 0
    speededup = True
    local_peak_speed_r = 0

    # Logging
    trial = 1
    succesful_clicks = 0
    MT = 0
    ID = 0
    TP = 0
    overshoots_r = 0
    points = 0

    overshootInside = False
    goal = False

    def __init__(self):
        self.super(trackingManager).__init__()
        self.isInside = False
        self.startTime = 0
        self.endTime = 0
        self.backAndForth = False
        self.backAndForthAgain = False
        self.disks = core.DisksContainer(environment)
        self.pcNode = None
        self.taskNum = 0

    def __del__(self):
        if environment.logResults:
            self.result_file.close()

    @field_has_changed(Button)
    def button_pressed(self):
        if self.Button.value:
            if not self.endedTests:
                self.select()
                if environment.logResults and self.startedTests and not self.endedTests:
                    self.logSetter()
                    environment.logData(logmanager)
                    self.resetValues()

                self.nextSettingStep()
            else:
                print("Tests ended")
        else:
            self.flagPrinted = False

    @field_has_changed(timer)
    def updateTimer(self):
        # attach disks to pointer
        self.disks.setTranslate(
            avango.gua.make_trans_mat(self.pcNode.Transform.value.get_translate())
        )

        if not self.endedTests:
            # highlight rotation if near target
            if environment.showWhenInTarget:
                # highlight rotation if near target
                if self.getErrorRotate() < W_rot[self.index] / 2:
                    self.disks.highlightRed()
                    environment.setBackgroundColor(avango.gua.Color(0.3, 0.5, 0.1))
                else:
                    self.disks.setColor()
                    environment.setBackgroundColor(avango.gua.Color(0, 0, 0))

        if self.startedTests and self.endedTests == False:
            self.setSpeed()
            self.setAcceleration()
            self.setOvershoots()
            self.autoDetect()

        if environment.saveReplay:
            self.logReplay()  # save replay, todo

    def select(self):
        if self.getErrorRotate() < W_rot[self.index] / 2:
            # print("HIT:" + str(self.getErrorRotate())+"°")
            self.goal = True
            environment.setBackgroundColor(avango.gua.Color(0, 0.2, 0.05), 0.18)
            if not environment.useAutoDetect:
                self.succesful_clicks += 1
            environment.playSound("hit_rotate")
            if self.startedTests:
                self.setMT(self.lastTime, self.timer.value)
                self.points = self.points + (self.ID / self.MT)
        else:
            # print("MISS:" + str(self.getErrorRotate())+"°")
            self.goal = False
            environment.setBackgroundColor(avango.gua.Color(0.3, 0, 0), 0.18)
            environment.playSound("miss")

    def nextSettingStep(self):
        # print(self.index)
        if self.counter % environment.N == environment.N - 1:
            self.index += 1

        if self.index == len(W_rot):
            self.endedTests = True
            environment.setBackgroundColor(avango.gua.Color(0, 0, 0.5))
            print("Your Score: " + str(self.points))

        # print("P:"+str( pencilRot )+"")
        # print("T:"+str( self.disksMat.value.get_rotate_scale_corrected() )+"")
        if self.index < len(W_rot):

            # move target
            if environment.randomTargets:  # select from random targets?
                if environment.taskDOFRotate == 3:
                    self.disks.setRotation(self.getRandomRotation3D())
                else:
                    self.disks.setRotation(self.getRandomRotation2D())

            else:
                if self.taskNum == 0 or self.taskNum == 2:
                    distance = environment.D_rot
                    if environment.taskDOFRotate == 3:
                        rotateAroundX = 1
                    else:
                        rotateAroundX = 0
                else:
                    rotateAroundX = 0
                    distance = 0

                self.disks.setRotation(avango.gua.make_rot_mat(distance, rotateAroundX, 1, 0))
                self.taskNum = (self.taskNum + 1) % 2

                self.disks.setDisksTransMats(targetDiameter[self.index])

            if self.startedTests:
                self.counter += 1
            else:
                self.startedTests = True

            self.setID(self.index)

    def getErrorRotate(self):
        return core.getRotationError1D(
            self.pcNode.Transform.value.get_rotate_scale_corrected(),
            self.disks.getRotate()
        )

    def autoDetect(self):
        if math.fabs(self.current_speed) < THRESHHOLD < self.peak_speed_r:
            if self.low_speed_counter < FRAMES_FOR_AUTODETECT - 1:
                self.low_speed_counter += 1
            else:
                self.low_speed_counter = 0
                if self.first:
                    self.first_reversal_point_r = self.pcNode.Transform.value.get_rotate().get_angle()
                    # print(self.first_reversal_point_r)
                    self.first_reversal_acceleration_r = self.current_acceleration
                    self.first = False

                # print(self.local_peak_speed_r)
                if self.local_peak_speed_r > THRESHHOLD:
                    self.speededup = True
                    self.local_peak_speed_r = 0

                if self.speededup:
                    print("reversal")
                    self.reversal_points_r.append(self.pcNode.Transform.value.get_rotate().get_angle())
                    self.speededup = False

    def setSpeed(self):
        if self.frame_counter % 5 == 0:
            self.PencilRotation1 = self.pcNode.Transform.value.get_rotate()
            self.start_time = self.timer.value
        else:
            if self.frame_counter % 5 == FRAMES_FOR_SPEED - 1:
                self.PencilRotation2 = self.pcNode.Transform.value.get_rotate()
                div = core.getRotationError1D(self.PencilRotation1, self.PencilRotation2)

                time = self.timer.value - self.start_time
                self.current_speed = div / time

                if self.current_speed < 10 ** -3:
                    self.current_speed = 0

                if self.current_speed > self.peak_speed_r:
                    self.peak_speed_r = self.current_speed

                if self.current_speed > self.local_peak_speed_r:
                    self.local_peak_speed_r = self.current_speed

                    # print(self.current_speed)
                    # print(self.peak_speed_r)
        self.frame_counter += 1

    def setAcceleration(self):
        if self.frame_counter2 % 5 == 0:
            self.speed_time1 = self.current_speed
            self.start_time2 = self.timer.value
        else:
            if self.frame_counter2 % 5 == FRAMES_FOR_SPEED - 1:
                self.speed_time2 = self.current_speed
                self.end_time2 = self.timer.value
                div = self.speed_time2 - self.speed_time1
                time = self.end_time2 - self.start_time2
                self.current_acceleration = div / time

                if self.current_acceleration > self.peak_acceleration_r:
                    self.peak_acceleration_r = self.current_acceleration

        self.frame_counter2 += 1

    def setOvershoots(self):
        if self.getErrorRotate() < W_rot[self.index] / 2:
            self.overshootInside = True
        else:
            if self.overshootInside:
                self.overshoots_r += 1
                self.overshootInside = False

    def resetValues(self):
        self.overshoots_r = 0
        self.peak_acceleration_r = 0
        self.first_reversal_acceleration_r = 0
        self.peak_speed_r = 0
        self.first = True
        self.overshootInside = False
        self.goal = False
        self.reversal_points_r = []

    def getRandomRotation3D(self):
        settings = [avango.gua.make_rot_mat(20, 1, 0.8, 0.3),
                    avango.gua.make_rot_mat(90, 0.1, 0.2, 0.9)]

        index = random.randint(0, len(settings) - 1)

        return settings[index]

    def getRandomRotation2D(self):
        settings = [avango.gua.make_rot_mat(20, 1, 0.8, 0),
                    avango.gua.make_rot_mat(90, 0.1, 0.2, 0)]

        index = random.randint(0, len(settings) - 1)

        return settings[index]

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

                self.result_file.write(
                    "TimeStamp: " + str(self.timer.value) + "\n" +
                    "ErrorRotate: " + str(self.getErrorRotate()) + "\n" +
                    "Pointerpos: \n" + str(self.pcNode.Transform.value) + "\n\n"
                )
                self.result_file.close()

    def logSetter(self):
        self.setID(self.index)
        self.setTP(self.index)

        if self.getErrorRotate() < W_rot[self.index] / 2:
            self.goal = True
        else:
            self.goal = False

        if environment.useAutoDetect:
            hit_type = "Auto"
        else:
            hit_type = "Manual"
            # self.clicks = self.clicks+1
            if self.goal:
                self.succesful_clicks += 1

        logmanager.set("User Id", environment.userId)
        logmanager.set("Group", environment.group)
        if environment.space3D:
            logmanager.set("DOF real R", 3)
        else:
            logmanager.set("DOF real R", 1)
        logmanager.set("DOF virtual R", environment.virtualDOFRotate)
        logmanager.set("target distance R", environment.D_rot)
        logmanager.set("target width R", W_rot[self.index])
        logmanager.set("TARGET_DISTANCE_ROTATE", environment.D_rot)
        logmanager.set("TARGET_WIDTH_ROTATE", W_rot[self.index])
        logmanager.set("ID combined", self.ID)
        logmanager.set("ID R", self.ID)
        logmanager.set("REPETITION", environment.N)
        logmanager.set("TRIAL", self.trial)
        # logmanager.set("BUTTON CLICKS", self.clicks)
        logmanager.set("SUCCESSFUL CLICKS", self.succesful_clicks)
        if self.goal:
            logmanager.set("Hit", 1)
        else:
            logmanager.set("Hit", 0)
        logmanager.set("OVERSHOOTS R", self.overshoots_r)
        logmanager.set("PEAK ACCELERATION R", self.peak_acceleration_r)
        if self.peak_acceleration_r > 0:
            logmanager.set("MOVEMENT CONTINUITY R", self.first_reversal_acceleration_r / self.peak_acceleration_r)
        else:
            logmanager.set("MOVEMENT CONTINUITY R", "#DIV0")
        logmanager.set("PEAK SPEED R", self.peak_speed_r)
        logmanager.set("HIT TYPE", hit_type)
        logmanager.set("MT", self.MT)
        logmanager.set("ERROR R ", self.getErrorRotate())
        logmanager.set("FIRST REVERSAL R", self.first_reversal_point_r)
        logmanager.set("REVERSAL POINTS R", len(self.reversal_points_r))

        self.trial += 1

    def setID(self, index):
        if index < len(ID):
            self.ID = ID[index]
            # print("ID: "+ str(self.ID))

    def setMT(self, startTime, endTime):
        """

        :param startTime:
        :param endTime:
        """
        self.MT = endTime - startTime
        self.lastTime = self.timer.value

    # print("Time: " + str(self.MT))

    def setTP(self, index):
        if self.MT > 0 and self.index < len(ID):
            self.TP = ID[index] / self.MT

    def handle_key(self, key, scancode, action, mods):
        if action == 1:
            # 32 is space 335 is num_enter
            if key == 32 or key == 335:
                if not self.endedTests:
                    # trackManager.nextSettingStep()
                    self.Button.value = True
                else:
                    print("Test ended")
        else:
            self.flagPrinted = False


def start():
    trackManager = trackingManager()

    environment.getWindow().on_key_press(trackManager.handle_key)
    environment.setup(graph)

    # loadMeshes
    trackManager.pcNode = core.PencilContainer().create(environment).getNode()

    trackManager.disks.setupDisks(trackManager.pcNode)
    trackManager.disks.setDisksTransMats(targetDiameter[0])

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
