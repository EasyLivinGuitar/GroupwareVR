import avango
import avango.daemon
import avango.gua
import avango.script
import avango.sound
import avango.sound.openal
import math

from examples_common.GuaVE import GuaVE
from avango.script import field_has_changed

class logManager(avango.script.Script):
	userID=0
	group=0
	condition=None
	DOF_T=0
	DOF_R=0
	movement_direction=None
	target_distance_t=0
	target_width_t=0
	rotation_axis=None
	target_distance_r=0
	target_width_r=0
	ID_t=0
	ID_r=0
	ID_combined=0
	repetition=0
	trial=0
	button_clicks=0
	succesful_clicks=0
	success=None
	hit_type=None
	hit_time=0
	hit_error_t=0
	hit_error_r=0
	overshoots=0
	throughput=0
	peak_speed=0
	peak_acceleration=0
	movement_continuity_t=0
	first_reversal_point=0
	num_reversal_points=0

	header_printed=False

	def setUserID(self, ID):
		self.userID=ID

	def setGroup(self, grp):
		self.group=grp

	def setCondition(self, task):
		self.condition = task

	def setDOF(self, DOFt, DOFr):
		self.DOF_T=DOFt
		self.DOF_R=DOFr

	def setMovementDirection(self, direction):
		self.movement_direction=direction

	def setTargetDistance_t(self, distance):
		self.target_distance_t=distance

	def setTargetWidth_t(self, width):
		self.target_width_t=width

	def setRotationAxis(self, axis):
		self.rotation_axis=axis

	def setTargetDistance_r(self, distance):
		self.target_distance_r=distance

	def setTargetWidth_r(self, width):
		self.target_width_t=width

	def setID_combined(self, idt, idr):
		self.ID_t=idt
		self.ID_r=idr
		self.ID_combined=self.ID_t+self.ID_r

	def setRepetition(self, rep):
		self.repetition=rep

	def setTrial(self, tria):
		self.trial=tria

	def setClicks(self, clicks, clicks_s):
		self.button_clicks=clicks
		self.succesful_clicks=clicks_s

	def setSuccess(self, suc):
		self.success=suc

	def setHit(self, h_type, h_time, error_t, error_r):
		self.hit_type=h_type
		self.hit_time=h_time
		self.hit_error_t=error_t
		self.hit_error_r=error_r
		self.setThroughput()

	def setOvershoots(self, shoots):
		self.overshoots=shoots

	def setThroughput(self):
		if(self.hit_time>0):
			self.throughput=self.ID_combined/self.hit_time

	def setPeakSpeed(self, peak):
		self.peak_speed=peak

	def setMovementContinuity(self, peak_acc, first_point_acc):
		self.peak_acceleration=peak_acc
		if(peak_acc>0):
			self.movement_continuity_t=first_point_acc/peak_acc

	def setReversalPoints(self, first, num):
		self.first_reversal_point=first
		self.num_reversal_points=num

	def log(self, result_file):
		if(self.header_printed==False):
			result_file.write(
				"USERID | "+
				"GROUP | "+
				"CONDITION | "+
				"DOF_T | "+
				"DOF_R | "+
				"MOVEMENT_DIRECTION | "+ 
				"TARGET_DISTANCE_T | "+
				"TARGET_WIDTH_T | "+
				"ROTATION_AXIS | "+
				"TARGET_DISTANCE_R | "+
				"TARGET_WIDTH_R | "+
				"ID_T | "+
				"ID_R | "+
				"ID_COMBINED | "+
				"REPETITION | "+
				"TRIAL | "+
				"BUTTON CLICKS | "+
				"SUCCESFULL CLICKS | " +
				"SUCCESS | "+
				"HIT_TYPE | "+
				"HIT_TIME | "+
				"HIT_ERROR_T | "+
				"HIT_ERROR_R | "+
				"OVERSHOOTS | "+
				"THROUGHPUT | "+
				"PEAK_SPEED | "+
				"PEAK_ACCELERATION | "+
				"MOVEMENT_CONTINUITY_T | "+
				"FIRST_REVERSAL_POINT | "+
				"NUM_REVERSAL_POINTS | "+
				"\n \n")
			self.header_printed=True

		result_file.write(
			str(self.userID)+ " | "+
			str(self.group)+" | "+
			str(self.condition)+" | "+
			str(self.DOF_T)+" | "+
			str(self.DOF_R)+" | "+
			str(self.movement_direction)+" | "+
			str(self.target_distance_t)+" | "+
			str(self.target_width_t)+" | "+
			str(self.rotation_axis)+" | "+
			str(self.target_distance_r)+" | "+
			str(self.target_width_r)+" | "+
			str(self.ID_t)+" | "+
			str(self.ID_r)+" | "+
			str(self.ID_combined)+" | "+
			str(self.repetition)+" | "+
			str(self.trial)+" | "+
			str(self.button_clicks)+" | "+
			str(self.succesful_clicks)+" | "+
			str(self.success)+" | "+
			str(self.hit_type)+" | "+
			str(self.hit_time)+" | "+
			str(self.hit_error_t)+" | "+
			str(self.hit_error_r)+" | "+
			str(self.overshoots)+" | "+
			str(self.throughput)+" | "+
			str(self.peak_speed)+" | "+
			str(self.peak_acceleration)+" | "+
			str(self.movement_continuity_t)+" | "+
			str(self.first_reversal_point)+" | "+
			str(self.num_reversal_points)+" | "+
			"\n"
		)