# coding=utf-8
import avango
import avango.daemon
import avango.gua
import avango.script
import avango.sound
import avango.sound.openal
import config
import math
import os.path
import glob
import LogManager

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
# @param ID the level of difficulty
# @param A the amplitude


def ID_A_to_W(ID, A):
    return (2 * A) / (2 ** ID)

def A_W_to_ID(A, W):
    return math.log(2*A/W)/math.log(2)


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

#returns array with error on each axis
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

    target_x = target2.get_translate()[0]
    target_y = target2.get_translate()[1]

    trans_target_x_square = (trans_x - target_x) * (trans_x - target_x)
    trans_target_y_square = (trans_y - target_y) * (trans_y - target_y)

    return math.sqrt(trans_target_x_square + trans_target_y_square)


def getDistance3D(target1, target2):
    trans_x = target1.get_translate()[0]
    trans_y = target1.get_translate()[1]
    trans_z = target1.get_translate()[2]

    target_x = target2.get_translate()[0]
    target_y = target2.get_translate()[1]
    target_z = target2.get_translate()[2]

    return math.sqrt((trans_x - target_x) ** 2 + (trans_y - target_y) ** 2 + (trans_z - target_z) ** 2)


def print_graph(root_node):
    stack = [(root_node, 0)]
    while stack:
        node, level = stack.pop()
        print("│   " * level + "├── {0} <{1}>".format(node.Name.value, node.__class__.__name__))
        stack.extend([(child, level + 1) for child in reversed(node.Children.value)])

def printHelp():
    environment = setupEnvironment()
    print("Config Numbers (0 - " + str(len(environment.disableAxisList)-1) + "):")

    for i in range(0, len(environment.disableAxisList)):
        print(str(i) + ": "+str(environment.disableAxisList[i]) + " DOF R virtual: "+str(environment.virtualDOFRotateList[i])+" DOF R task: "+str(environment.taskDOFRotateList[i]))



'''Settings'''
class setupEnvironment(avango.script.Script):
    # user id 0 and group 0 is developer flag
    userId = 0
    groupId = 0

    ''' difference from screen center to center of tracking'''
    #offsetTracking = avango.gua.make_trans_mat(-1.0, -(0.58 + 0.975), 0.26 + 3.48) #* avango.gua.make_rot_mat(90.0,0,1,0)
    offsetTracking = avango.gua.make_trans_mat(0.0, -1.28, 1.6);

    '''get the offsets of the pointer.'''
    offsetPointer = avango.gua.make_trans_mat(0.0, 0.1, -0.60)

    '''get the position of the center where the pointer and the target is located.'''
    displayPosition = avango.gua.make_trans_mat(0.0, 0.15, 0.35)

    logResults = True
    saveReplay = True

    snapRotationTargetIfNear = False

    '''radius of spikes from center in the model file'''
    r_model = 0.10

    '''radius of spikes displayed'''
    r = 0.02

    res_pass = avango.gua.nodes.ResolvePassDescription()

    viewer = avango.gua.nodes.Viewer()
    viewer.DesiredFPS.value = 60
    resolution = avango.gua.Vec2ui(1920, 1200)
    # screenSize = avango.gua.Vec2(1.235, 0.695) # in meters
    #window = avango.gua.nodes.GlfwWindow(

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

    logmanager = None

    def __init__(self):
        self.super(setupEnvironment).__init__()

    '''returns itself. pseudo-constructor'''
    def create(self):
        print(
        "\033[32mWelcome to the VR motor movement study application.\033[0m \n"
        +"\033[90mWritten by Benedikt S. Vogler and Marcel Gohsen with the help of Alexander Kulik.\033[0m\n"
        +"User id and group id are set via first two launch parameters. Currently: "+str(self.userId)+"-"+str(self.groupId))
        self.timeTempBGleft = 0
        self.permanentBG = False
        # connect time with the timerField
        self.timerField.connect_from(self.timeSensor.Time)
        testConfigNo = -1

        while testConfigNo >= 10 or testConfigNo == -1:
            testConfigNo = int(input("Config Number: "))
           
            if testConfigNo >= 10 or testConfigNo == -1:
                print("ERROR: invalid config number " + str(testConfigNo))
                printHelp()

        self.config = config.Config()
        self.config.setConfig(testConfigNo)

        self.disableAxis = self.config.disableAxisTranslate
        self.virtualDOFRotate = self.config.virtualDOFRotate
        self.space3D = self.config.space3D
        self.taskDOFRotate = self.config.taskDOFRotate
        self.taskDOFTranslate = self.config.taskDOFTranslate
        self.A_rot = self.config.A_rot  # in degrees
        self.A_trans = self.config.A_trans # in meter
        self.W_rot = self.config.W_rot # in meter
        self.W_trans = self.config.W_trans # in meter
        self.ID_t = self.config.ID_t
        self.ID_r = self.config.ID_r
        self.usePhoneCursor = self.config.usePhoneCursor
        self.showHuman = self.config.showHuman
        self.showWhenInTarget = self.config.showWhenInTarget
        self.animationPreview = self.config.animationPreview
        self.animationTime = self.config.animationTime
        self.randomTargets = self.config.randomTargets
        self.provideFeedback = self.config.provideFeedback
        self.useAutoDetect = self.config.useAutoDetect
        self.logEffectiveForR = self.config.logEffectiveForR
        self.logEffectiveForT = self.config.logEffectiveForT
        self.levelSize = self.config.levelSize
        #self.snapRotationTargetIfNear =

        if self.taskDOFRotate == 0:
            self.taskString = str(testConfigNo)+"_pointing"
        else:
            if self.taskDOFTranslate > 0:
                self.taskString = str(testConfigNo)+"_docking"
            else:
                self.taskString = str(testConfigNo)+"_rotation"

        self.logmanager = LogManager.LogManager(self.taskString)

        return self

    def launch(self, otherlocals):
        print("Launch")
        guaVE = GuaVE()
        z = globals().copy()
        z.update(otherlocals)
        guaVE.start(locals(), z)

        self.viewer.run()

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
            Brightness=10.0,
            Transform=(avango.gua.make_trans_mat(0, 1, 1.0) *
                       avango.gua.make_scale_mat(5.0))
        )

        self.window = avango.gua.nodes.Window(
            Size=avango.gua.Vec2ui(self.resolution.x*2, self.resolution.y),
            LeftPosition=avango.gua.Vec2ui(0, 0),
            LeftResolution=self.resolution,
            RightPosition=avango.gua.Vec2ui(self.resolution.x, 0),
            RightResolution=self.resolution,
            StereoMode=avango.gua.StereoMode.SIDE_BY_SIDE,
            WarpMatrixRedRight="/opt/lcd-warpmatrices/lcd_2_warp_P2.warp",
            WarpMatrixGreenRight="/opt/lcd-warpmatrices/lcd_2_warp_P2.warp",
            WarpMatrixBlueRight="/opt/lcd-warpmatrices/lcd_2_warp_P2.warp",
            WarpMatrixRedLeft="/opt/lcd-warpmatrices/lcd_2_warp_P1.warp",
            WarpMatrixGreenLeft="/opt/lcd-warpmatrices/lcd_2_warp_P1.warp",
            WarpMatrixBlueLeft="/opt/lcd-warpmatrices/lcd_2_warp_P1.warp"
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
            Transform=avango.gua.make_trans_mat(0.0, 0.0, 3.5),
            NearClip = 0.1,
            FarClip = 10.0
        )
        screen = avango.gua.nodes.ScreenNode(
            Name="screen",
            Width=1.46,
            Height=1.09,
            Children=[self.cam]
        )

        # Sieht netter aus
        self.res_pass.EnableSSAO.value = False
        self.res_pass.SSAOIntensity.value = 4.0
        self.res_pass.SSAOFalloff.value = 10.0
        self.res_pass.SSAORadius.value = 7.0

        # self.res_pass.EnableScreenSpaceShadow.value = True
        '''
        self.res_pass.EnvironmentLightingColor.value = avango.gua.Color(0.1, 0.1, 0.1)
        self.res_pass.ToneMappingMode.value = avango.gua.ToneMappingMode.UNCHARTED
        self.res_pass.Exposure.value = 1.0
        self.res_pass.BackgroundColor.value = avango.gua.Color(0, 0, 0)
        '''

        #self.res_pass.BackgroundColor.value = avango.gua.Color(0.4, 0.65, 0.75)
        #self.res_pass.BackgroundMode.value = avango.gua.BackgroundMode.SKYMAP_TEXTURE
        self.res_pass.BackgroundMode.value = avango.gua.BackgroundMode.QUAD_TEXTURE
        #self.res_pass.BackgroundTexture.value = "/opt/guacamole/resources/skymaps/DH203SN.png"
        self.res_pass.BackgroundTexture.value = "/opt/3d_models/textures/FORHUMANUSE_TEXTURES/stone/030_stone_sandy.jpg"

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
        head_device_sensor = avango.daemon.nodes.DeviceSensor(DeviceService=avango.daemon.DeviceService())
        head_device_sensor.TransmitterOffset.value = self.offsetTracking

        head_device_sensor.Station.value = "glasses"

        self.cam.Transform.connect_from(head_device_sensor.Matrix)  # headTracking->camera

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
        # print("Update: " +str(self.timeTempBGleft))
        #apply set background color
        if (not self.permanentBG) and (self.timerField.value >= self.timeTempBGleft):
            # print("back to black: "+str(self.timerField.value) + " >= " + str(self.timeTempBGleft))
            # self.res_pass.BackgroundColor.value = avango.gua.Color(0.5, 0.75, 0.95)
            pass

    def setBackgroundColor(self, color, time=0):
        if time > 0: #temporary color
            self.timeTempBGleft = self.timeSensor.Time.value + time  # aktuelle Zeit plus Zeit
            self.permanentBG = False
        else: #permanent color
            self.permanentBG = True
        self.res_pass.BackgroundColor.value = color

    def getWindow(self):
        return self.window

    def getFolderPath(self):
        path = "results/" + self.taskString + "_T" + str(self.getDOFTranslateReal()) + "_" + str(
            self.getDOFTranslateVirtual()) + "_R" + str(self.taskDOFRotate) + "/"

        # create dir if not existent
        if not os.path.exists(path):
            os.makedirs(path)

        return path

    def playSound(self, sound):
        if sound == "balloon":
            self.balloonSound.Play.value = True
        elif sound == "miss":
            self.missSound.Play.value = True
        elif sound == "hit_rotate":
            self.hitRotateSound.Play.value = True
        elif sound == "levelUp":
            self.levelUpSound.Play.value = True
