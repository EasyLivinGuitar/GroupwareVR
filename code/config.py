# coding=utf-8
import sys
import core


class Config():
    '''disable translation on this axis'''
    disableAxisTranslate = []

    '''if one rotation axis should be locked/disabled. Switches beetween 3 and 1 DOF'''
    virtualDOFRotate = 0

    '''should the task swich between rotation targets using 3  or 1 DOF or disable it =0?'''
    taskDOFRotate = 0

    '''should the task swich between translation targets reachable with 1 DOF or 0?'''
    taskDOFTranslate = 0

    '''is the task above the table or is it on the table?'''
    space3D = False

    A_rot = []

    A_trans = []

    W_rot = []

    W_trans = []

    '''number of repetitions per setting'''
    levelSize = -1

    ID_t = []
    ID_r = []

    '''needs button press'''
    useAutoDetect = False

    '''use random Targets'''
    randomTargets = False

    '''show preview of motion'''
    animationPreview = False
    animationTime = 0  # in s

    '''you can fixate the cursor during the animation preview'''
    fixCursorDuringAnimation = False

    '''phone or colored cross'''
    usePhoneCursor = False

    '''show Human'''
    showHuman = False

    '''highlight if inside the target'''
    showWhenInTarget = False

    '''hit or miss feedback'''
    provideFeedback = True

    '''you can log the effective values per level'''
    logEffectiveForR = False
    logEffectiveForT = False

    '''play level up sound'''
    playLevelUpSound = False

    def getTrialsCount(self):
        a = len(self.W_trans)
        b = len(self.W_rot)
        c = len(self.ID_r)
        d = len(self.ID_t)
        if a > b:
            biggest = a
        else:
            biggest = b

        if c > biggest:
            biggest = c

        if d > biggest:
            biggest = d

        return biggest

    '''checks the content of the configuration and fills needed arrays'''
    def verifyConfig(self):
        if len(self.W_trans) == 0 and len(self.A_trans) == 0 and self.taskDOFTranslate != 0:
            print ("\033[93mConfig Warning\033[0m: No translation information available!")
        else:
            if len(self.A_trans) == 0 and self.taskDOFTranslate > 0:
                if len(self.ID_t) == len(self.W_trans):#has enough ID information
                    for i in range(0, len(self.W_trans) * self.levelSize):
                        self.A_trans.append(2 ** self.ID_t[int(i / self.levelSize)] * self.W_trans[int(i / self.levelSize)] / 2)
                else:
                    print("033[91mConfig ERROR\033[0m: Unequal number of given ID's and target widths!")
            if len(self.W_trans) == 0 and self.taskDOFTranslate > 0:
                if len(self.ID_r) == len(self.A_rot):#has enough ID information
                    for i in range(0, len(self.A_trans) * self.levelSize):
                        self.W_trans.append(core.ID_A_to_W(self.ID_r[int(i / self.levelSize)], self.A_trans[int(i / self.levelSize)]))
                else:
                    print("\033[91mConfig ERROR\033[0m: Unequal number of given ID's and distances!")

        if len(self.W_rot) == 0 and len(self.A_rot) == 0 and self.taskDOFRotate>0:
            print ("\033[93mConfig Warning\033[0m: No rotation available!")
        else:
            if len(self.A_rot) == 0:
                if len(self.ID_r) == len(self.W_rot):
                    for i in range(0, len(self.W_rot) * self.levelSize):
                        self.A_rot[i] = 2 ** self.ID_r[int(i / self.levelSize)] * self.W_rot[int(i / self.levelSize)] / 2
                else:
                    print("Config ERROR: Unequal number of given ID's and rotation target widths!")
            if len(self.W_rot) == 0 and self.taskDOFRotate>0:
                if len(self.ID_r) == len(self.A_rot):
                    for i in range(0, len(self.A_rot) * self.levelSize):
                        self.W_rot.append((core.ID_A_to_W(self.ID_r[int(i / self.levelSize)], self.A_rot[int(i / self.levelSize)])))
                else:
                    print("033[91mConfig ERROR\033[0m: Unequal number of given ID's and rotation distances!")

        #calculate ID if missing
        if len(self.ID_t) == 0:
            for i in range(0, self.getTrialsCount()):
                if len(self.A_trans) > 0 and self.A_trans[i] != 0:#can calculate ID for translation
                    self.ID_t.append(core.A_W_to_ID(self.A_trans[i], self.W_trans[i]))

        if len(self.ID_r) == 0:
            for i in range(0, self.getTrialsCount()):
                if len(self.A_rot) > 0 and self.A_rot[i] != 0:#can calculate ID for rotation
                    self.ID_r.append(core.A_W_to_ID(self.A_rot[i], self.W_rot[i]))

        #fill every list which is not set with zeros
        if len(self.W_trans)==0:
            for i in range(0, self.getTrialsCount()):
                self.W_trans.append(0)
        if len(self.W_rot)==0:
            for i in range(0, self.getTrialsCount()):
                self.W_rot.append(0)
        if len(self.A_trans)==0:
            for i in range(0, self.getTrialsCount()):
                self.A_trans.append(0)
        if len(self.A_rot)==0:
            for i in range(0, self.getTrialsCount()):
                self.A_rot.append(0)
        if len(self.ID_t)==0:
            for i in range(0, self.getTrialsCount()):
                self.ID_t.append(0)
        if len(self.ID_r)==0:
            for i in range(0, self.getTrialsCount()):
                self.ID_r.append(0)

        #wenn levelSize = 1 dann funktioniert die effektive berechnung nicht mehr
        if self.levelSize==1 and (self.logEffectiveForR or self.logEffectiveForT):
            print("033[91mConfig ERROR\033[0m: It is not possible to calculate effective values with one trial per level.")
        if self.levelSize==3 and (self.logEffectiveForR or self.logEffectiveForT):
            print("\033[93mConfig Warning\033[0m: The amount of trials per level is very low to calulcate effective values.")
        if self.taskDOFTranslate > 0 and self.usePhoneCursor:
            print("\033[93mConfig Warning\033[0m: Phone cursor and translation may not work well together.")    



    '''possible to set distances/amplitudes or ID's or target widths, rest gets calculated'''
    def setConfig(self, conf_num):
        # Slot 0
        if conf_num == 0:#berechne max. rotationswinkel
            self.disableAxisTranslate = [1, 1, 1]
            self.virtualDOFRotate = 3
            self.taskDOFRotate = 3
            self.taskDOFTranslate = 0
            self.usePhoneCursor = True
            self.useAutoDetect = False
            self.space3D = True
            self.W_rot = [10, 10, 10, 10,  10,  10,  10,  10,  10,  10,  10,  10,  10]
            self.A_rot = [60, 70, 80, 90, 100, 110, 120, 130, 140, 150, 160, 170, 180]
            self.logEffectiveForR = False
            self.levelSize = 1
        elif conf_num == 1:#max. rot. grnauigkeit
            self.disableAxisTranslate = [1, 1, 1]
            self.virtualDOFRotate = 3
            self.taskDOFRotate = 3
            self.taskDOFTranslate = 0
            self.usePhoneCursor = True
            self.space3D = True
            self.W_rot = [50, 45, 40, 35,  30,  25,  20,  15,  10,  5,  4,  3,  2]
            self.A_rot = [100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100]#muss erst mit 0 raus gefunden werden
            self.levelSize = 1
        elif conf_num == 2:#max. trans Genauigkeit
            self.disableAxisTranslate = [0, 0, 0]
            self.virtualDOFRotate = 0
            self.taskDOFRotate = 0
            self.taskDOFTranslate = 1
            self.usePhoneCursor = True
            self.space3D = True
            self.W_trans = [.05, .010, .020, .024, .022, .020,  .015,  .012,  .08,  .05,  .04,  .03,  .02]
            self.A_trans = [0.20, 0.20,0.20, 0.20, 0.20, 0.20, 0.20, 0.20, 0.20, 0.20, 0.20, 0.20, 0.20]#muss erst mit 0 raus gefunden werden
            self.levelSize = 1
        else:
            print("ERROR: No such configuration\n")
            sys.exit(0)

        self.verifyConfig()



 # '''disable translation on this axis'''
 #    disableAxisList = [
 #        [0, 0, 0],
 #        [0, 1, 1],
 #        [0, 1, 1],
 #       [0, 1, 0],
 #       [0, 1, 0],
 #       [1, 1, 1],
 #       [1, 1, 1],
 #       [1, 1, 1],
 #       [0, 0, 0],
 #       [0, 1, 0],
 #       [0, 0, 0],
 #       [0, 0, 0]
 #    ]  # second dimension is axis x,y,z

 #    '''if one rotation axis should be locked/disabled. Switches beetween 3 and 1 DOF'''
 #    virtualDOFRotateList = [3, 3, 3, 3, 3, 3, 1, 1, 3, 1, 3, 3]

 #    '''should the task swich between rotation targets using 3  or 1 DOF or disable it =0?'''
 #    taskDOFRotateList = [0, 0, 0, 0, 0, 3, 1, 1, 3, 1, 1, 1]

 #    '''should the task swich between translation targets reachable with 1 DOF or 0?'''
 #    taskDOFTranslateList = [
 #        1,
 #        1,
 #        1,
 #        1,
 #        1,
 #        0,
 #        0,
 #        0,
 #        1,
 #        1,
 #        0, # 10
 #        0
 #    ]

 #    '''is the task above the table or is it on the table?'''
 #    space3DList = [
 #        True,
 #        False,
 #        True,
 #        False,
 #        True,
 #        True,
 #        False,
 #        True,
 #        True,
 #        False,
 #        True,
 #        True
 #    ]

 #    D_rot_list = [
 #        [0, 0, 0],
 #        [0, 0, 0],
 #        [0, 0, 0],
 #        [0, 0, 0],
 #        [120, 120, 120],
 #        [120, 120, 120],
 #        [120, 120, 120],
 #        [120, 120, 120],
 #        [120, 120, 120],
 #        [120, 120, 120],
 #        [-1, -1, -1],  # 10 random distance, values are ignored
 #        [120, 120, 120]
 #    ]  # in degrees, [saveslotno][n times each aka 'level']

 #    D_trans_list = [
 #        [0.3, 0.3, 0.3],
 #        [0.3, 0.3, 0.3],
 #        [0.3, 0.3, 0.3],
 #        [0.3, 0.3, 0.3],
 #        [0.3, 0.3, 0.3],
 #        [0.0, 0.0, 0.0],
 #        [0.0, 0.0, 0.0],
 #        [0.0, 0.0, 0.0],
 #        [0.3, 0.3, 0.3],
 #        [0.3, 0.3, 0.3],
 #        [0.0, 0.0, 0.0],  # 10 random distance
 #        [0.0, 0.0, 0.0]
 #    ]  # in meter, [saveslotno][n times each aka 'level']

 #    # the amount of repitions per ID
 #    levelSize = 8

 #    # setup
 #    ID_list = [
 #        [4, 5, 6],
 #        [4, 5, 6],
 #        [4, 5, 6],
 #        [4, 5, 6],
 #        [4, 5, 6],
 #        [4, 5, 6],
 #        [4, 5, 6],
 #        [4, 5, 6],
 #        [4, 5, 6],
 #        [4, 5, 6],
 #        [0, 0, 0],  # 10
 #        [0, 0, 0]
 #    ] # fitt's law, [saveslotno][level]






