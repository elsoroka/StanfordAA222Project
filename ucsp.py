# File created: 05/21/2020
# Tested on   : Python 3.7.4
# Author(s)   : Emiko Soroka,
# Unittests   : None
# Description :
# Course scheduling problem implementation

import numpy as np

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
#     A 9am - 10:30am TuTh class: [i:j] = [11:12], r = [0 1 0 1 0]
#     A 10a - 12p M lab         : [i:j] = [2:4]  , r = [1 0 0 0 0]
#     A 3p - 4:30p MW class     : [i:j] = [15:16], r = [0 1 0 1 0]
# How to perturb these class timings:
# Add / subtract 2 to indices within range
# Change pattern of r
# r-pattern is only valid if r is spaced out
# we can swap by "pushing" or "popping" as long as sum(r) stays the same
# [0 1 0 1 0] -> [1 0 1 0 0]
#             -> [0 0 1 0 1] can't be [0 0 0 1 0]

# A row r1 overlaps r if: r (xor) r1 != r
# So a population member has i:j, r
# Then the course state is two vectors:
# t in R2, d in R5. We'll define a vector in R8 for computational reasons


class Course:

	# Initialize a course "randomly" within constraints
	# Guaranteed to produce a feasible sample
	@staticmethod
	def init_random(meetingLength, nMeetings):

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
			base_length = [1.0, 1,5][idx]

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
		t2 = t1 + meetingLength/base_length

		# Set up the days
		d = np.zeros(5, dtype=int)
		if 1 == nMeetings:
			d[np.random.choice(range(0,5))] = 1
		elif 2 == nMeetings:
			idx = np.random.choice(range(0,3))
			d[idx] = 1; d[idx + 2] = 1
		elif 3 == nMeetings:
			d = np.array([1,0,1,0,1], dtype=int)

		return Course(np.array([t1,t2], dtype=int), d)

	# Some static data
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


	# Course methods
	# Initialize from given time/date
	def __init__(self, new_t:np.array, new_d:np.array):
		self.t = new_t
		self.d = new_d

	# Easily read what the course is
	def pretty_print(self):
		print("d", self.d, "t", self.t)
		print("".join([self.DAY_NAMES[i] for i in range(5) if self.d[i] > 0]), \
			  self.TIME_NAMES[self.t[0]][0], " - ", self.TIME_NAMES[self.t[1]-1][1])


# Conflict matrix A:
# [1 0 0 0 0 0 0 0 0 0 0 1 0 0 0 0 0 0] # 9a 1.0 conflicts with 9a 1.5
# [0 1 0 0 0 0 0 0 0 0 0 1 0 0 0 0 0 0] # 10a 1.0 conflicts with 9a 1.5
# [0 1 0 0 0 0 0 0 0 0 0 0 1 0 0 0 0 0] # 10a 1.0 conflicts with 10:30a 1.5
# [0 0 1 0 0 0 0 0 0 0 0 0 1 0 0 0 0 0] # 11a 1.0 conflicts with 10:30a 1.5
# [0 0 0 1 0 0 0 0 0 0 0 0 0 1 0 0 0 0] # 12p 1.0 conflicts with 12p 1.5
# [0 0 0 0 1 0 0 0 0 0 0 0 0 1 0 0 0 0] # 1p 1.0 conflicts with 12p 1.5
# [0 0 0 0 1 0 0 0 0 0 0 0 0 0 1 0 0 0] # 1p 1.0 conflicts with 1:30p 1.5
# [0 0 0 0 0 1 0 0 0 0 0 0 0 0 1 0 0 0] # 2p 1.0 conflicts with 1:30p 1.5
# [0 0 0 0 0 0 1 0 0 0 0 0 0 0 0 1 0 0] # 3p 1.0 conflicts with 3p 1.5
# [0 0 0 0 0 0 0 1 0 0 0 0 0 0 0 1 0 0] # 4p 1.0 conflicts with 3p 1.5
# [0 0 0 0 0 0 0 1 0 0 0 0 0 0 0 0 1 0] # 4p 1.0 conflicts with 4:30p 1.5
# [0 0 0 0 0 0 0 0 1 0 0 0 0 0 0 0 1 0] # 5p 1.0 conflicts with 4:30p 1.5
# [0 0 0 0 0 0 0 0 0 1 0 0 0 0 0 0 0 1] # 6p 1.0 conflicts with 6p 1.5
# [0 0 0 0 0 0 0 0 0 0 1 0 0 0 0 0 0 1] # 7p 1.0 conflicts with 6p 1.5
class Ucsp:
	pass


if __name__ == "__main__":
	print("TODO. Please yell at the lazy programmer.")
	
	c1 = Course.init_random(1.5, 2)
	c1.pretty_print()
	c2 = Course.init_random(3.0, 1)
	c2.pretty_print()
	c3 = Course.init_random(1.0, 3)
	c3.pretty_print()