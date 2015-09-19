# coding=utf-8
import avango
import avango.daemon
import avango.gua
import avango.script
import avango.sound
import avango.sound.openal
import math
import os.path
import glob

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


##
# @param ID the index of difficulty
# @param A the amplitude


def IDtoW(ID, A):
    return (2 * A) / (2 ** ID)


## Converts a rotation matrix to the Euler angles yaw, pitch and roll.
# @param q The rotation quat to be converted.


def  get_euler_angles(q):
    sqx = q.x * q.x
    sqy = q.y * q.y
    sqz = q.z * q.z
    sqw = q.w * q.w

    unit = sqx + sqy + sqz + sqw  # if normalised is one, otherwise is correction factor
    test = (q.x * q.y) + (q.z * q.w)

    if test > 1:
        yaw = 0.0
        roll = 0.0
        pitch = 0.0

    if test > (0.49999 * unit):  # singularity at north pole
        yaw = 2.0 * math.atan2(q.x, q.w)
        roll = math.pi / 2.0
        pitch = 0.0
    elif test < (-0.49999 * unit):  # singularity at south pole
        yaw = -2.0 * math.atan2(q.x, q.w)
        roll = math.pi / -2.0
        pitch = 0.0
    else:
        yaw = math.atan2(2.0 * q.y * q.w - 2.0 * q.x * q.z, 1.0 - 2.0 * sqy - 2.0 * sqz)
        roll = math.asin(2.0 * test)
        pitch = math.atan2(2.0 * q.x * q.w - 2.0 * q.y * q.z, 1.0 - 2.0 * sqx - 2.0 * sqz)

    if yaw < 0.0:
        yaw += 2.0 * math.pi

    if pitch < 0:
        pitch += 2 * math.pi

    if roll < 0:
        roll += 2 * math.pi

    return yaw, pitch, roll


def getRotationError3D(aMat, bMat):
    # quaternion to euler has an error with the z axis
    a = aMat.get_rotate_scale_corrected()
    a.normalize()

    aEuler = get_euler_angles(a)

    b = bMat.get_rotate_scale_corrected()
    b.normalize()

    # hack to make the error fit
    b.y = b.z
    b.z = 0

    bEuler = get_euler_angles(b)

    error = [
        (aEuler[0] - bEuler[0]) * 180 / math.pi,  # Y
        (aEuler[1] - bEuler[1]) * 180 / math.pi,  # ?
        (aEuler[2] - bEuler[2]) * 180 / math.pi,  # ?
        0  # gesamt
    ]
    error[3] = math.sqrt(error[0] * error[0] + error[1] * error[1] + error[2] * error[2])

    '''
    print("P: "+str(a))
    print("T: "+str(b))
    error = math.acos(2*(a.x*b.x+a.y*b.y+a.z*b.z+a.w*b.w)**2-1)
    error *=180/math.pi
    '''
    return error


'''
get rotation error between two rotations
'''


def getRotationError1D(rotA, rotB):
    matA = avango.gua.make_rot_mat(rotA)
    matB = avango.gua.make_rot_mat(rotB)

    diffRotMat = avango.gua.make_inverse_mat(matA) * matB
    return diffRotMat.get_rotate_scale_corrected().get_angle()


def getDistance2D(target1, target2):
    trans_x = target1.get_translate()[0]
    trans_y = target1.get_translate()[1]

    aim_x = target2.get_translate()[0]
    aim_y = target2.get_translate()[1]

    trans_aim_x_square = (trans_x - aim_x) * (trans_x - aim_x)
    trans_aim_y_square = (trans_y - aim_y) * (trans_y - aim_y)

    return math.sqrt(trans_aim_x_square + trans_aim_y_square)


def getDistance3D(target1, target2):
    trans_x = target1.get_translate()[0]
    trans_y = target1.get_translate()[1]
    trans_z = target1.get_translate()[2]

    aim_x = target2.get_translate()[0]
    aim_y = target2.get_translate()[1]
    aim_z = target2.get_translate()[2]

    return math.sqrt((trans_x - aim_x) ** 2 + (trans_y - aim_y) ** 2 + (trans_z - aim_z) ** 2)


def print_graph(root_node):
    stack = [(root_node, 0)]
    while stack:
        node, level = stack.pop()
        print("│   " * level + "├── {0} <{1}>".format(node.Name.value, node.__class__.__name__))
        stack.extend([(child, level + 1) for child in reversed(node.Children.value)])

def printHelp():
    print("Config Numbers (0 - 9):")
    print("0 - 4 : Pointing")
    print("5 - 7 : Rotation")
    print("8 - 9 : Docking\n")

    environment = setupEnvironment()

    for i in range(0, len(environment.disableAxisList)):
        print(str(i) + ": "+str(environment.disableAxisList[i]) + " DOF_R_virtual: "+str(environment.virtualDOFRotateList[i])+" DOF_R_task: "+str(environment.taskDOFRotateList[i]))



'''Settings'''


class setupEnvironment(avango.script.Script):
    userId = 0
    group = 0

    # task config
    '''disable translation on this axis'''
    disableAxisList = [[0, 0, 0], [0, 1, 1], [0, 1, 1], [0, 1, 0], [0, 1, 0], [1, 1, 1], [1, 1, 1], [1, 1, 1],
                       [0, 0, 0], [0, 1, 0]]  # x,y,z

    '''if one rotation axis should be locked/disabled. Switches beetween 3 and 1 DOF'''
    virtualDOFRotateList = [3, 3, 3, 3, 3, 3, 1, 1, 3, 1]

    '''should the task swich between rotation aims using 3  or 1 DOF or disable it =0?'''
    taskDOFRotateList = [0, 0, 0, 0, 0, 3, 1, 1, 3, 1]

    '''should the task swich between translation aims reachable with 1 dof or 0?'''
    taskDOFTranslateList = [1, 1, 1, 1, 1, 0, 0, 0, 1, 1]

    '''is the task above the table or is it on the table?'''
    space3DList = [True, False, True, False, True, True, False, True, True, False]

    # the amount of trials per ID
    N = 8

    # setup
    ID = [4, 5, 6]  # fitt's law

    ''' difference from screen center to center of tracking'''
    offsetTracking = avango.gua.make_trans_mat(0.0, -0.34, 0.70)

    '''get the offsets of the pointer.'''
    offsetPointer = avango.gua.make_trans_mat(0.0, 0, 0.30)

    '''get the position of the center where the pointer and the aim is located.'''
    displayPosition = avango.gua.make_trans_mat(0.0, 0, .30)

    D_rot = 120  # in degrees
    D_trans = 0.3  # in meter

    logResults = True
    saveReplay = True

    '''if false needs a button press or next step, if true then autodetects'''
    useAutoDetect = False

    randomTargets = True

    ''' show a preview of the motion first'''
    AnimationPreview = True
    AnimationTime = 2 # in s

    '''you can fixate the cursor during the animation preview'''
    enableCursorDuringAnimation = True

    '''phone or colored cross setup?'''
    usePhoneCursor = False

    '''radius of spikes from center in the model file'''
    r_model = 0.10

    '''radius of spikes displayed'''
    r = 0.02

    '''highlight if inside the target'''
    showWhenInTarget = False

    '''software provides feedback if user hits oder misses'''
    provideFeedback = False

    '''show human'''
    showHuman = False

    res_pass = avango.gua.nodes.ResolvePassDescription()

    viewer = avango.gua.nodes.Viewer()
    viewer.DesiredFPS.value = 60
    resolution = avango.gua.Vec2ui(1920, 1080)
    # screenSize = avango.gua.Vec2(1.235, 0.695) # in meters
    window = avango.gua.nodes.GlfwWindow(
        Size=resolution,
        LeftResolution=resolution,
        RightResolution=resolution,
        StereoMode=avango.gua.StereoMode.CHECKERBOARD
    )

    # sound
    soundtraverser = avango.sound.nodes.SoundTraverser()
    soundRenderer = avango.sound.openal.nodes.OpenALSoundRenderer()
    soundRenderer.Device.value = ""
    soundtraverser.Renderers.value = [soundRenderer]

    hitRotateSound = avango.sound.nodes.SoundSource()
    levelUpSound = avango.sound.nodes.SoundSource()
    balloonSound = avango.sound.nodes.SoundSource()
    missSound = avango.sound.nodes.SoundSource()

    loader = avango.gua.nodes.TriMeshLoader()  # Create Loader

    everyObject = avango.gua.nodes.TransformNode(
        Children=[],
        Transform=displayPosition
    )

    timeSensor = avango.nodes.TimeSensor()
    timerField = avango.SFFloat()

    def __init__(self):
        self.super(setupEnvironment).__init__()

    def create(self):
        self.timeTillBlack = 0
        self.permanentBG = False
        # connect time with the timerField
        self.timerField.connect_from(self.timeSensor.Time)
        testConfigNo = -1

        while testConfigNo >= len(self.disableAxisList) or testConfigNo == -1:
            testConfigNo = int(input("Config Number: "))
           
            if testConfigNo >= len(self.disableAxisList) or testConfigNo == -1:
                print("ERROR: Invalid Config Number")
                printHelp()

        self.disableAxis = self.disableAxisList[testConfigNo]
        self.virtualDOFRotate = self.virtualDOFRotateList[testConfigNo]
        self.space3D = self.space3DList[testConfigNo]
        self.taskDOFRotate = self.taskDOFRotateList[testConfigNo]
        self.taskDOFTranslate = self.taskDOFTranslateList[testConfigNo]

        if self.virtualDOFRotate == 1 and self.taskDOFRotate > 1:
            self.taskDOFRotate = 1

        if self.taskDOFRotate == 0:
            self.taskString = str(testConfigNo)+"_pointing"
        else:
            if self.taskDOFTranslate > 0:
                self.taskString = str(testConfigNo)+"_docking"
            else:
                self.taskString = str(testConfigNo)+"_rotation"

        self.created_logfile = False

        return self

    '''Get the degrees of freedom on the translation virtually'''

    def getDOFTranslateVirtual(self):
        return 3 - self.disableAxis[0] - self.disableAxis[1] - self.disableAxis[2]

    def getDOFTranslateReal(self):
        if self.space3D:
            return 3
        else:
            return 1


    def setup(self, graph):
        light = avango.gua.nodes.LightNode(
            Type=avango.gua.LightType.POINT,
            Name="light",
            Color=avango.gua.Color(1.0, 1.0, 1.0),
            Brightness=100.0,
            Transform=(avango.gua.make_trans_mat(1, 1, 5) *
                       avango.gua.make_scale_mat(30, 30, 30))
        )

        avango.gua.register_window("window", self.window)

        self.cam = avango.gua.nodes.CameraNode(
            LeftScreenPath="/screen",
            RightScreenPath="/screen",
            SceneGraph="scenegraph",
            Resolution=self.resolution,
            EyeDistance=0.064,
            EnableStereo=True,
            OutputWindowName="window",
            Transform=avango.gua.make_trans_mat(0.0, 0.0, 3.5)
        )
        screen = avango.gua.nodes.ScreenNode(
            Name="screen",
            Width=1.445,
            Height=0.81,
            Children=[self.cam]
        )

        # Sieht netter aus
        self.res_pass.EnableSSAO.value = True
        self.res_pass.SSAOIntensity.value = 4.0
        self.res_pass.SSAOFalloff.value = 10.0
        self.res_pass.SSAORadius.value = 7.0

        # self.res_pass.EnableScreenSpaceShadow.value = True

        self.res_pass.EnvironmentLightingColor.value = avango.gua.Color(0.1, 0.1, 0.1)
        self.res_pass.ToneMappingMode.value = avango.gua.ToneMappingMode.UNCHARTED
        self.res_pass.Exposure.value = 1.0
        self.res_pass.BackgroundColor.value = avango.gua.Color(0, 0, 0)

        anti_aliasing = avango.gua.nodes.SSAAPassDescription()

        pipeline_description = avango.gua.nodes.PipelineDescription(
            Passes=[
                avango.gua.nodes.TriMeshPassDescription(),
                avango.gua.nodes.LightVisibilityPassDescription(),
                self.res_pass,
                anti_aliasing,
            ]
        )

        self.cam.PipelineDescription.value = pipeline_description
        self.cam.PipelineDescription.value.EnableABuffer.value = True

        # Setup headtracking
        self.head_device_sensor = avango.daemon.nodes.DeviceSensor(DeviceService=avango.daemon.DeviceService())
        self.head_device_sensor.TransmitterOffset.value = self.offsetTracking

        self.head_device_sensor.Station.value = "glasses"

        self.cam.Transform.connect_from(self.head_device_sensor.Matrix)  # headTracking->camera

        graph.Root.value.Children.value = [light, screen]

        # connect camera with soundrenderer
        self.soundtraverser.RootNode.value = graph.Root.value
        self.soundtraverser.Traverse.value = True

        self.soundRenderer.ListenerPosition.connect_from(self.cam.Transform)

        # setup sounds
        self.balloonSound.URL.value = "data/sounds/balloon_pop.ogg"
        self.balloonSound.Loop.value = False
        self.balloonSound.Play.value = True
        graph.Root.value.Children.value.extend([self.balloonSound])

        self.hitRotateSound.URL.value = "data/sounds/hit_rotate.wav"
        self.hitRotateSound.Loop.value = False
        self.hitRotateSound.Play.value = True
        graph.Root.value.Children.value.extend([self.hitRotateSound])

        self.levelUpSound.URL.value = "data/sounds/level_up.wav"
        self.levelUpSound.Loop.value = False
        self.levelUpSound.Play.value = True
        graph.Root.value.Children.value.extend([self.levelUpSound])

        self.missSound.URL.value = "data/sounds/miss.ogg"
        self.missSound.Loop.value = False
        self.missSound.Play.value = True
        graph.Root.value.Children.value.extend([self.missSound])

        # setup viewer
        self.viewer.SceneGraphs.value = [graph]
        self.viewer.Windows.value = [self.window]

        graph.Root.value.Children.value.append(self.everyObject)

    @field_has_changed(timerField)
    def update(self):
        # print("Update: " +str(self.timeTillBlack))
        if (not self.permanentBG) and (self.timerField.value >= self.timeTillBlack):
            # print("back to black: "+str(self.timerField.value) + " >= " + str(self.timeTillBlack))
            self.res_pass.BackgroundColor.value = avango.gua.Color(0, 0, 0)

    def getWindow(self):
        return self.window

    def getPath(self):
        path = "results/" + self.taskString + "_T" + str(self.getDOFTranslateReal()) + "_" + str(
            self.getDOFTranslateVirtual()) + "_R" + str(self.taskDOFRotate) + "/"

        # create dir if not existent
        if not os.path.exists(path):
            os.makedirs(path)

        return path

    def logData(self, logmanager):
        path = self.getPath()

        # fint out which file number
        if not self.created_logfile:  # create File
            self.num_files = len(glob.glob1(path, "*.csv"))
            # if os.path.isfile(os.path.join(path, f)):
            self.created_logfile = True

        logmanager.writeToFile(path + self.taskString + "_trial" + str(self.num_files) + ".csv")

    def launch(self, otherlocals):
        print("Launch")
        guaVE = GuaVE()
        z = globals().copy()
        z.update(otherlocals)
        guaVE.start(locals(), z)

        self.viewer.run()

    def setBackgroundColor(self, color, time=0):
        if time > 0:
            self.timeTillBlack = self.timeSensor.Time.value + time  # aktuelle Zeit plus Zeit
            self.permanentBG = False
        else:
            self.permanentBG = True
        self.res_pass.BackgroundColor.value = color

    def playSound(self, sound):
        if sound == "balloon":
            self.balloonSound.Play.value = True
        else:
            if sound == "miss":
                self.missSound.Play.value = True
            else:
                if sound == "hit_rotate":
                    self.hitRotateSound.Play.value = True
                else:
                    if sound == "levelUp":
                        self.levelUpSound.Play.value = True
