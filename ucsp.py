# File created: 05/21/2020
# Tested on   : Python 3.7.4
# Author(s)   : Emiko Soroka,
# Unittests   : None
# Description : Course scheduling problem implementation.

import numpy as np
import typing, csv

# We have two types of timeslots: hour and 1.5-hour.
# A course consists of one or more indices [i:j] into this schedule

#0 : 0 0 0 0 0  9:00a - 10:00a
#1 : 0 0 0 0 0 10:00a - 11:00a
#2 : 0 0 0 0 0 11:00a - 12:00p
#3 : 0 0 0 0 0 12:00p - 1:00p
#4 : 0 0 0 0 0  1:00p - 2:00p
#5 : 0 0 0 0 0  2:00p - 3:00p
#6 : 0 0 0 0 0  3:00p - 4:00p
#7 : 0 0 0 0 0  4:00p - 5:00p
#8 : 0 0 0 0 0  5:00p - 6:00p
#9 : 0 0 0 0 0  6:00p - 7:00p
#10: 0 0 0 0 0  7:00p - 8:00p
#11: 0 0 0 0 0  9:00a - 10:30a
#12: 0 0 0 0 0 10:30a - 12:00p
#13: 0 0 0 0 0 12:00p - 1:30p
#14: 0 0 0 0 0  1:30p - 3:00p
#15: 0 0 0 0 0  3:00p - 4:30p
#16: 0 0 0 0 0  4:30p - 6:00p
#17: 0 0 0 0 0  6:00p - 7:30p

# and a vector r in R5 with some amount of 1's.

# Examples:
#     A 9am - 10:30am TuTh class: [i:j] = [11:11], r = [0 1 0 1 0]
#     A 10a - 12p M lab         : [i:j] = [2:3]  , r = [1 0 0 0 0]
#     A 3p - 4:30p MW class     : [i:j] = [15:15], r = [0 1 0 1 0]

# How to perturb these class timings:
# Add / subtract 1 to indices within range
# Change pattern of r
# r-pattern is only valid if r is spaced out
# we can swap by "pushing" or "popping" as long as sum(r) stays the same
# [0 1 0 1 0] -> [1 0 1 0 0]
#             -> [0 0 1 0 1] can't be [0 0 0 1 0]

# A row r1 overlaps r if: r (xor) r1 != r
# So a population member has i:j, r
# Then the course state is two vectors:
# t in R2, d in R5.


class Course:

	@staticmethod
	def init_random(meetingLength, nMeetings, *args):
		'''Initialize a course "randomly" within constraints.
 Guaranteed to produce a feasible sample: e.g. one within acceptable time range
 and with acceptable days (MW, not MTu, etc.).
'''
		time_range  = [0,]
		base_length = 0.0

		# These two ranges are to select from hour timeslots (0 - 11) or 1.5 hour (11 - 18).
		time_ranges = [range(0, 11 - int(meetingLength/1.0-1)), \
		               range(11,18 - int(meetingLength/1.5-1))]

		# If length is ambiguous - ex. could be 2x 1.5 or 3x 1.0
		if (0.0 == meetingLength % 1.5) and (0.0 == meetingLength % 1.0):
			# Pick randomly
			idx = np.random.choice([0, 1])
			time_range = time_ranges[idx]
			base_length = [1.0, 1.5][idx]

		# The meetingLength is only a multiple of 1.0
		elif (0.0 == meetingLength % 1.0):
			time_range = time_ranges[0]
			base_length = 1.0
		
		# The meetingLength is only a multiple of 1.5
		else:
			time_range = time_ranges[1]
			base_length = 1.5

		# Choose the class start time randomly from the valid range
		t1 = np.random.choice(time_range)
		# Choose the end time using the length of the meeting
		t2 = t1 + meetingLength/base_length - 1

		# Set up the days
		d = np.zeros(5, dtype=int)
		if 1 == nMeetings:
			d[np.random.choice(range(0,5))] = 1
		elif 2 == nMeetings:
			idx = np.random.choice(range(0,3))
			d[idx] = 1; d[idx + 2] = 1
		elif 3 == nMeetings:
			d = np.array([1,0,1,0,1], dtype=int)

		return Course(np.array([t1,t2], dtype=int), d, *args)

	
	# Some static data to help with pretty-printing.
	
	TIME_NAMES = [
	[" 9:00a","10:00a",],
	["10:00a","11:00a",],
	["11:00a","12:00p",],
	["12:00p"," 1:00p",],
	[" 1:00p"," 2:00p",],
	[" 2:00p"," 3:00p",],
	[" 3:00p"," 4:00p",],
	[" 4:00p"," 5:00p",],
	[" 5:00p"," 6:00p",],
	[" 6:00p"," 7:00p",],
	[" 7:00p"," 8:00p",],
	[" 9:00a","10:30a",],
	["10:30a","12:00p",],
	["12:00p","1:30p",],
	[" 1:30p","3:00p",],
	[" 3:00p","4:30p",],
	[" 4:30p","6:00p",],
	[" 6:00p","7:30p",],
	]
	DAY_NAMES = ["M", "Tu", "W", "Th", "F"]
	N_HOUR_SLOTS = 11
	N_80MIN_SLOTS = 7


	# Course methods
	
	def __init__(self, new_t:np.array, new_d:np.array, courseName, numberEnrolled, cantOverlap, shouldntOverlap):
		'''Initialize from given data.
new_t: Start and end time as array in R2.
new_d: Days as array in R5.
courseName: human-readable string such as "AA 222".
numberEnrolled: integer enrollment count. (Not used but maybe later, if we have time?)
cantOverlap: string (we'll process it here!) of sorted overlap indices: e.g. "5;6"
means this class can't overlap with courses at indices 5 or 6.
shouldntOverlap: same as cantOverlap but for soft overlap constraint (not hard).
'''
		self.courseName      = courseName
		self.numberEnrolled  = numberEnrolled
		self.cantOverlap     = [] if cantOverlap == "" else [int(idx)-1 for idx in cantOverlap.split(";") if idx != '']
		self.shouldntOverlap = [] if shouldntOverlap == "" else [int(idx)-1 for idx in shouldntOverlap.split(";") if idx != '']
		self.td = np.hstack([new_t, new_d])

		if new_t[0] < self.N_HOUR_SLOTS: # t is in the 1.0 hour slots
			self.t_range = range(0, self.N_HOUR_SLOTS - (self.td[1] - self.td[0]))
		else:
			self.t_range = range(self.N_HOUR_SLOTS, self.N_80MIN_SLOTS - (self.td[1] - self.td[0]))



	def is_valid(self, t):
		'''Check if a course has a valid time range.
Example: if the valid times are 8am - 7pm and the course is at 8pm, is_valid returns False.
Does not check for overlaps.
'''
		return self.td[0] + t in self.t_range and self.td[1] + t in self.t_range


	def perturb(self, d=0, t=0):
		'''Perturb this course.
If d != 0, attempt to perturb the course days.
(This won't have any effect if the course is 3 days per week, since
the only option for those courses is MWF.
If t != 0, attempt to perturb the course time.
This won't push the course time outside the allowable range.
(e.g. if the last allowable time is 7pm, t=1 won't push it to 8pm.)
'''
		if t != 0:
			
			if self.is_valid(t):
				self.td[0:2] += t
				
				
		if d != 0:
			n_days = sum(self.td[2:])
			if n_days == 1:
				self.td[2:] = np.zeros(5, dtype=int)
				self.td[2+np.random.choice(range(0,5))] = 1
			if n_days == 2:
				choices = np.array([[1,0,1,0,0],[0,1,0,1,0],
					      [0,1,0,1,0], [0,0,1,0,1]], dtype=int)
				self.td[2:] = choices[np.random.choice(range(0,4))]
			

	def make_feasible(self, schedule):
		'''Attempt to make the placement of this course within a schedule
(list of other courses) feasible. If we find an overlap,
we try to fix it by randomly perturbing one of the overlapping classes.
This method can silently fail to make the schedule feasible.
You should check_feasible() after running it..
'''
		# No overlap constraints on this 
		if self.cantOverlap == []:
			return

		# Figure out if we are in conflict
		for idx in self.cantOverlap:
			i = 0 # safety limit
			
			is_conflict = self.check_conflict(schedule[idx])
			
			while is_conflict and i < 10:
				
				self.perturb(np.random.choice([-1, 1]), np.random.choice([-1.1]))
				i += 1


	def check_conflict(self, otherCourse):
		'''Check whether another course conflicts with self.
To conflict means otherCourse has at least overlapping day AND time.
'''
		t1, t2 = self.td[0], self.td[1]
		o1, o2 = otherCourse.td[0], otherCourse.td[1]
		
		if max(self.td[2:] + otherCourse.td[2:]) > 1: # days overlap

			if t1 >= self.N_HOUR_SLOTS: # it's an 80min slot
				# remap it
				t1, t2 = self.CONFLICT_MAP[t1][0], self.CONFLICT_MAP[t2][1]
			
			if o1 >= self.N_HOUR_SLOTS: # it's an 80min slot
				# remap it
				o1, o2 = self.CONFLICT_MAP[o1][0], self.CONFLICT_MAP[o2][1]

			# now check for conflicts
			# Conflict doesn't occur if:
			#      t1[   ]t2     t1 - o2 >= 0.0
			# o1[   ]o2      or: t2 - o1 >= 0.0
			# 
			if not (o1 - t2 >= 0 or t1 - o2 >= 0):
				return True
		# No conflicts found
		return False

	# Make print(course) output a nice human-readable string.
	def __str__(self) ->str:

		return "{}: {} {} - {}".format( \
			   self.courseName,
			   "".join([self.DAY_NAMES[i] for i in range(5) if self.td[2+i] > 0]), \
			   self.TIME_NAMES[self.td[0]][0], self.TIME_NAMES[self.td[1]][1]   \
			   )

	# Map conflicts from 1.5 hour indices (11 - 17) to 1 hour indices (0 - 10)
	CONFLICT_MAP = {
	11:[0,1],
	12:[1,2],
	13:[3,4],
	14:[4,5],
	15:[6,7],
	16:[7,8],
	17:[9,10],
	}



# The UCSP consists of a list of Courses which make up a Schedule.
# It has methods to check whether the Schedule is feasible
# and to perturb the courses in the hopes of making an infeasible Schedule feasible.
class Ucsp:
	# Define what counts as non-business hours.
	ODD_HOURS_INDICES = [8, 9, 10, 17]
	LUNCH_HOUR_1_0    = 3
	LUNCH_HOUR_1_5    = 13

	def __init__(self, schedule:[Course]):
		'''Initialize a new problem'''
		self.schedule = schedule

	def add_overlap_constraint(self, c1, c2, enforce=True):
		'''Add a constraint that courses c1 and c2 cannot overlap/
		If enforce=True this is a hard constraint, e.g. c1 and c2
		are coreqs and must NEVER overlap
		If enforce=False this is a soft constraint, e.g. c1 and c2
		are commonly taken together and SHOULDN'T overlap'''
		pass

	def check_feasible(self)->True or False:
		'''Check whether a schedule is feasible (all hard constraints met)'''
		for course in self.schedule:
			for idx in course.cantOverlap:
				i=0
				is_conflict = course.check_conflict(self.schedule[idx])
				
				# Try to make feasible
				while is_conflict and i < 10:
					course.perturb(np.random.choice([-1,1]), np.random.choice([-1,1]))
					is_conflict = course.check_conflict(self.schedule[idx])
					i += 1
				if is_conflict:
					return False

		# None found
		return True

	def check_desirable(self)->float:
		'''Compute a measure of schedule goodness: count soft constraints met.'''
		softOverlapPenalty = 0.0
		oddHoursPenalty    = 0.0
		lunchHoursPenalty  = 0.0
		daysCount = np.zeros(5)

		for course in self.schedule:
			# Check for odd (non-business) hours
			if course.td[0] in self.ODD_HOURS_INDICES or course.td[1] in self.ODD_HOURS_INDICES:
				oddHoursPenalty += 1
			# Check for soft overlap constraint
			for idx in course.shouldntOverlap:
				if course.check_conflict(self.schedule[idx]):
					softOverlapPenalty += 1.0
			# Penalize courses at lunchtime
			if course.td[0] == self.LUNCH_HOUR_1_0 or course.td[0] == self.LUNCH_HOUR_1_5:
				lunchHoursPenalty += 1.0

			daysCount += course.td[2:]


		# It really wants to put all the classes MW and this is a hack to fix it
		spreading = daysCount[0] + daysCount[2]
		
		return softOverlapPenalty*10.0 + spreading*0.0+ oddHoursPenalty*2.0 + lunchHoursPenalty*1.0


	def get_all_time_vectors(self)->np.array:
		result = np.empty(len(self.schedule))
		for i, course in enumerate(self.schedule):
			result[i:(i+1)] = course.td[0]
		return result


	def add_all_time_vectors(self, v:np.array)->np.array:
		result = np.empty(len(self.schedule))
		for i, course in enumerate(self.schedule):
			if course.is_valid(v[i]):
				#it has to be an integer
				course.perturb(0, int(v[i]))
			else:
				course.perturb(np.random.choice([-1,0,1]), 0)

			result[i:i+1] = course.td[0]
		return result


# TEST CODE

if __name__ == "__main__":
	
	print("Generate a sample (random) schedule from data:")
	infilename = "data/spring_csv_data.csv"# input("Data file name: ")

	random_schedule = []

	with open(infilename, "r") as infile:
		# Use builtin csv reader
		reader = csv.DictReader(infile)
		for row in reader:
			# Exclude TBA classes because they have no timing information
			random_schedule.append( \
			Course.init_random(float(row['meetingLengthHours']), 
				               int(row['numberOfMeetings']),
				               row['courseNumber'],
				               int(row['numberEnrolled']),
				               row['cantOverlap'],
				               row['shouldntOverlap']))
	
	ucsp = Ucsp(random_schedule)
	print("Random schedule is feasible?", ucsp.check_feasible())
	print("Random schedule is good? Penalty:", ucsp.check_desirable())
	for course in random_schedule:
		print(course.courseName, course)

