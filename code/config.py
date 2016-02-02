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
            print ("\033[93mConfig Warning\033[0m: No translation information in config found!")
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
            print ("\033[93mConfig Warning\033[0m: No rotation information in config found!")
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

        if self.taskDOFRotate > self.virtualDOFRotate:
            print("\033[93mConfig Warning\033[0m: You can not fullfill the rotation tasks with this config. Set to possible task.")
            self.taskDOFRotate = virtualDOFRotate

        #wenn levelSize = 1 dann funktioniert die effektive berechnung nicht mehr
        if self.levelSize==1 and (self.logEffectiveForR or self.logEffectiveForT):
            print("033[91mConfig ERROR\033[0m: It is not possible to calculate effective values with one trial per level.")
        if self.levelSize==3 and (self.logEffectiveForR or self.logEffectiveForT):
            print("\033[93mConfig Warning\033[0m: The amount of trials per level is very low to calulcate effective values.")

    '''possible to set distances/amplitudes or ID's or target widths, rest gets calculated'''
    def setConfig(self, conf_num):
        # Slot 0
        if conf_num == 0:#max. rotationswinkel bestimmen
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
            self.levelSize = 3
        elif conf_num == 1:#min. rot. Zielgröße bestimmen
            self.disableAxisTranslate = [1, 1, 1]
            self.virtualDOFRotate = 3
            self.taskDOFRotate = 3
            self.taskDOFTranslate = 0
            self.usePhoneCursor = True
            self.space3D = True
            self.W_rot = [50, 45, 40, 35,  30,  25,  20,  15,  10,  5,  4,  3,  2]
            self.A_rot = [100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100]#muss erst mit config 0 raus gefunden werden
            self.levelSize = 3
        elif conf_num == 2:#max. trans Genauigkeit bestimmen
            self.disableAxisTranslate = [0, 0, 0]
            self.virtualDOFRotate = 0
            self.taskDOFRotate = 0
            self.taskDOFTranslate = 1
            self.usePhoneCursor = True
            self.space3D = True
            self.W_trans = [.035, .030, .028, .024, .022, .020,  .015,  .012,  .008,  .005,  .004,  .003,  .002]
            self.A_trans = [0.20, 0.20,0.20, 0.20, 0.20, 0.20, 0.20, 0.20, 0.20, 0.20, 0.20, 0.20, 0.20]#muss erst mit config 0 raus gefunden werden
            self.levelSize = 3
        elif conf_num == 3:#6DOF docking task test
            self.disableAxisTranslate = [0, 0, 0]
            self.virtualDOFRotate = 3
            self.virtualDOFTranslate = 3
            self.taskDOFRotate = 3
            self.taskDOFTranslate = 1
            self.usePhoneCursor = True
            self.space3D = True
            self.W_trans = [.035, .030, .028, .024, .022, .020,  .015,  .012,  .008,  .005,  .004,  .003,  .002]
            self.A_trans = [0.20, 0.20,0.20, 0.20, 0.20, 0.20, 0.20, 0.20, 0.20, 0.20, 0.20, 0.20, 0.20]
            self.W_rot = [50, 45, 40, 35,  30,  25,  20,  15,  10,  5,  4,  3,  2]#not rendered with phone cursor
            self.A_rot = [100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100]
            self.levelSize = 1
            #TODO
            #1.remove bounds container if T task
            #2. add bounds to target
            #3. add rotation to target
        else:
            print("ERROR: No such configuration\n")
            sys.exit(0)

        self.verifyConfig()