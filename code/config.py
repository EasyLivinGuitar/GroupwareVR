# coding=utf-8
import avango
import avango.daemon
import avango.gua
import avango.script
import avango.sound
import avango.sound.openal
import core
import sys

class Config():
	'''disable translation on this axis'''
	disableAxisTranslate = []

	'''if one rotation axis should be locked/disabled. Switches beetween 3 and 1 DOF'''
	virtualDOFRotate = 0

	'''should the task swich between rotation aims using 3  or 1 DOF or disable it =0?'''
	taskDOFRotate = 0

	'''should the task swich between translation aims reachable with 1 DOF or 0?'''
	taskDOFTranslate = 0

	'''is the task above the table or is it on the table?'''
	space3D = False

	D_rot = []

	D_trans = []

	W_rot = []

	W_trans = []

	'''number of repetitions per setting'''
	N = -1

	ID = []

	'''needs button press'''
	useAutoDetect = False

	'''use random Targets'''
	randomTargets = False

	'''show preview of motion'''
	animationPreview = False
	animationTime = 0 #in s

	'''you can fixate the cursor during the animation preview'''
	fixCursorDuringAnimation = False

	'''phone of colored cross'''
	usePhoneCursor = False

	'''show Human'''
	showHuman = False

	'''highlight if inside the target'''
	showWhenInTarget = False

	'''hit or miss feedback'''
	provideFeedback = False

	'''possible to set distances or ID's or widths, rest gets calculated'''
	def setConfig(self, conf_num):
		#Slot 0
		if(conf_num==0):
			self.disableAxisTranslate = [0, 0, 0]
			self.virtualDOFRotate = 3
			self.taskDOFRotate = 0
			self.taskDOFTranslate = 1
			self.space3D = True
			self.D_trans = [0.3, 0.3, 0.3]
			self.D_rot = [30, 30, 30]
			self.ID = [4, 5, 6]
			self.N = 5
		elif(conf_num==1):
			pass #add configs
		else:
			print("ERROR: No such configuration\n \n")
			sys.exit(0)

		self.verifyValues()


	def verifyValues(self):
		if(len(self.W_trans) == 0 and len(self.D_trans) == 0):
			print ("WARNING: No translation available!")
		else:
			if(len(self.D_trans) == 0):
				if(len(self.ID) == len(self.W_trans)):
					for i in range(0, len(self.W_trans) * self.N):
						self.D_trans.append(2 ** self.ID[int(i / self.N)] * self.W_trans[int(i / self.N)] / 2)
				else:
					print("ERROR: Unequal number of given ID's and target widths!")
			if(len(self.W_trans) == 0):
				if(len(self.ID) == len(self.D_rot)):
					for i in range(0, len(self.D_trans) * self.N):
						self.W_trans.append(core.IDtoW(self.ID[int(i / self.N)], self.D_trans[int(i / self.N)]))
				else:
					print("ERROR: Unequal number of given ID's and distances!")

		if(len(self.W_rot) == 0 and len(self.D_rot) == 0):
			print ("WARNING: No rotation available!")
		else:
			if(len(self.D_rot) == 0):
				if(len(self.ID) == len(self.W_rot)):
					for i in range(0, len(self.W_rot) * self.N):
						self.D_rot[i] = 2 ** self.ID[int(i / self.N)] * self.W_rot[int(i / self.N)] / 2
				else:
					print("ERROR: Unequal number of given ID's and target widths!")
			if(len(self.W_rot) == 0):
				if(len(self.ID) == len(self.D_rot)):
					for i in range(0, len(self.D_rot) * self.N):
						self.W_rot.append((core.IDtoW(self.ID[int(i / self.N)], self.D_rot[int(i / self.N)])))
				else:
					print("ERROR: Unequal number of given ID's and distances!")



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

 #    '''should the task swich between rotation aims using 3  or 1 DOF or disable it =0?'''
 #    taskDOFRotateList = [0, 0, 0, 0, 0, 3, 1, 1, 3, 1, 1, 1]

 #    '''should the task swich between translation aims reachable with 1 DOF or 0?'''
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
 #    N = 8

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






