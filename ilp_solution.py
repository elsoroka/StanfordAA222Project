# File created: 06/04/2020
# Tested on   : Python 3.7.4
# Author(s)   : Emiko Soroka,
# Unittests   : None
# Description : Integer linear program solution to UCSP

import numpy as np
import cvxpy as cvx
import csv


#  #  #  #  #  #  #  #  #
#    Test data setup    #
#  #  #  #  #  #  #  #  #

infilename = input("Data file name: ")


class_lengths       = []
class_block_types   = []
class_day_types     = []
hard_overlap_groups = []
soft_overlap_groups = []

# We need the order of course names to enable nice printing at the end
course_indices_to_names = {}

infile = open(infilename, "r")

# Use builtin csv reader
reader = csv.DictReader(infile)
for i, row in enumerate(reader):
	class_day_types.append(int(row['numberOfMeetings']))
	
	# Retrieve the soft constraint group
	soft_group = [int(g) for g in row['shouldntOverlap'].split(";") if g != "" and g]
	if [] != soft_group:
		# Don't forget to add this class to the group!
		soft_group.append(int(row['dataNumber']))
		soft_overlap_groups.append(soft_group)

	# Retrieve the hard constraint group
	hard_group = [int(g) for g in row['cantOverlap'].split(";") if g != ""]
	if [] != hard_group:
		hard_group.append(int(row['dataNumber']))
		hard_overlap_groups.append(hard_group)

	# Handle the meetingLength
	meetingLength = float(row['meetingLengthHours'])
	block_type = 0
	# Handle 1.5 hour blocks vs 1 hour blocks
	if 0 == meetingLength % 1.5: # divisible by 1.5
		block_type = 1.5
		meetingLength += 0.5 # round up
	else: # divisible by 1.0
		block_type = 1.0
	class_block_types.append(block_type)
	class_lengths.append(int(meetingLength))

	# Save the course name
	course_indices_to_names[i] = row['courseNumber']

# Close file
infile.close()



# Length of each class in multiples of 1 hour.
#class_lengths     = [2, 1, 2, 2] # 1.5 hours, 1.0 hours, 1.5 hours, 2
#class_block_types = [1.5, 1, 1.5, 1] # class is in 1.5 hour or 1 hour blocks

# Type of each class
#class_day_types   = [2, 3, 2, 1]

J = len(class_lengths) # Number of classes

#hard_overlap_groups = [[0,2,3],]

#soft_overlap_groups = [[1,2,],]


#  #  #  #  #  #  #  #  #
#      Solver setup     #
#  #  #  #  #  #  #  #  #

D = 5 # length of day vector
# Represent the times in half-hour blocks so the 1.5 hour classes
# can be represented by integer variables
# Range for 1.5 hour multiple classes: 10, 13, 16, 19, 22 25
FIRST_1_5_BLOCK = 1  # represents 9.00
LAST_1_5_BLOCK  = 7 # represents 18:00
# Range for 1 hour multiple classes
FIRST_1_0_BLOCK = 1  # represents 8:00 
LAST_1_0_BLOCK  = 12 # represents 19:00

BUSINESS_HOURS_START_1_0 = 2 # 9am
BUSINESS_HOURS_START_1_5 = 1 # 9am
BUSINESS_HOURS_END_1_0   = 10 # 5 - 6pm
BUSINESS_HOURS_END_1_5   = 6  # 4:30 - 6pm
#                1  2  3   4   5   6   7   8   9   10  11  12 
# 1.0 blocks are 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19
#                1   2     3    4    5   6    7
# 1.5 blocks are 9, 10:30, 12, 1:30, 3, 4:30, 6
# The function x + 1 + (x-1)/2 converts 1.5 hour indices to 1.0 hour indices.


# Compliance matrix for 2 day classes: if A_2 * d <= 1 it is valid.
A_2 = np.array([[1, 1, 0, 0, 0],
				[1, 0, 0, 1, 0],
				[1, 0, 0, 0, 1],
				[0, 1, 1, 0, 0],
				[0, 1, 0, 0, 1],
				[0, 0, 1, 1, 0],
				[0, 0, 0, 1, 1]], dtype=bool)


d_var = cvx.Variable((J, D), boolean=True)
t_var = cvx.Variable(J, integer=True)
constraints = []


# OBJECTIVE - Penalty function

def penalty(t_var):
	time_p = 0.0; overlap_p = 0.0; lunchtime_p = 0.0
	
	# First: Penalize classes at bad times
	for j in range(J):
		if 1.5 == class_block_types[j]:
			# 0 if time is before end of business hours
			# ex: if time is 7 (6pm - 7:30pm) and, (7-c)_+ = 1
			time_p += cvx.pos(t_var[j] - BUSINESS_HOURS_END_1_5)
			# 0 if time is after start of business hours
			# example: if time is 1 (8am) and (2-1)
			time_p += cvx.pos(BUSINESS_HOURS_START_1_5 - t_var[j])
		else: 
			time_p += cvx.pos(t_var[j] - BUSINESS_HOURS_END_1_5)
			time_p += cvx.pos(BUSINESS_HOURS_START_1_0 - t_var[j])
	
	# Second, Penalize classes overlapping in soft groups
	for group in soft_overlap_groups:
		for i in group:
			for j in group:
				if j > i: # avoid double penalty, e.g. 1<->2, 2<->1
					print("Penalizing {}, {}".format(course_indices_to_names[i], course_indices_to_names[j]))
					idx_1 = i; idx_2 = j;
					# code reuse, beware
					c1_start = t_var[idx_1]
					c2_start = t_var[idx_2]
					d1 = d_var[idx_1,:]
					d2 = d_var[idx_2,:]

					# handle the constraint between a 1.5 hour and 1 hour class
					if 1.5 == class_block_types[idx_1] and 1.0 == class_block_types[idx_2]:
						# Convert to 1 hour overlap
						c1_start = c1_start + 1 + (c1_start-1)/2

					elif 1.5 == class_block_types[idx_2] and 1.0 == class_block_types[idx_1]:
						# Convert to 1 hour overlap
						c2_start = c2_start + 1 + (c2_start-1)/2

					# Something wrong with this penalty.
					# Add the penalty
					overlap_p += -cvx.minimum(c2_start - c1_start + class_lengths[idx_2], \
										 c1_start - c2_start + class_lengths[idx_1], \
										 -cvx.max(d1 + d2) + 1)

	# Third. Penalize classes occurring at lunchtime.
	# TODO. (lower priority)

	# ADJUST RELATIVE WEIGHTS HERE
	return 1 * time_p + 1 * lunchtime_p + 10 * overlap_p

# Set objective
objective = cvx.Minimize(penalty(t_var))


# CONSTRAINTS

for j in range(J):
	# Add constraints on class start/end times
	lb, ub = 0, 0	
	if 0 == class_lengths[j] % 2: # class divisible into hours
		lb = FIRST_1_0_BLOCK
		ub = LAST_1_0_BLOCK - (class_lengths[j]//2 - 1)

	else: # divisble into 1.5 hours
		lb = FIRST_1_5_BLOCK
		ub = LAST_1_5_BLOCK - (class_lengths[j]//3 - 1)
	print("j: {}, lb={}, ub={}".format(j, lb, ub))

	constraints.append(t_var[j] <= ub)
	constraints.append(t_var[j] >= lb)

	# Add constraints on days
	if 1 == class_day_types[j]:
		constraints.append(cvx.sum(d_var[j,:]) == 1)
	elif 2 == class_day_types[j]:
		constraints.append(A_2 @ (d_var[j,:]).T <= 1)
		constraints.append(cvx.sum(d_var[j,:]) == 2)
	else:
		constraints.append(d_var[j,:] == [True, False, True, False, True])


def add_conflict(idx_1, idx_2, constraints):
	# Conflict: c1 vs c2
	# Either c1_start after c2_end or c2_end before c1_start
	#     or c2_start after c1_end or c1_end before c2_start
	# For each of these, define a binary variable in R4
	# that selects which constraint is active
	# Add hard overlap constraints between course 1 and 3

	c1_start = t_var[idx_1]
	c2_start = t_var[idx_2]
	d1 = d_var[idx_1,:]
	d2 = d_var[idx_2,:]

	# handle the constraint between a 1.5 hour and 1 hour class
	if 1.5 == class_block_types[idx_1] and 1.0 == class_block_types[idx_2]:
		# Convert to 1 hour overlap
		c1_start = c1_start + 1 + (c1_start-1)/2

	elif 1.5 == class_block_types[idx_2] and 1.0 == class_block_types[idx_1]:
		# Convert to 1 hour overlap
		c2_start = c2_start + 1 + (c2_start-1)/2

	# Overlap constraint math:
	# c1_start - c2_end >= 0 -> c1_start - c2_start >= c2_length
	# c2_start - c1_end >= 0 -> c2_start - c1_start >= c1_length
	#c1[   ]c1
	#        c2[ ]c2
	# c2_start - c1_start - c1_length >= 0.0 OR
	# c1_start - c2_start - c2_length >= 0.0
	# If this happens:
	# [1 0 1 0 0]
	# [0 0 1 0 1] -> sum = [1 0 2 0 1]
	# max(d1 + d2) <= 1 for the constraint to hold
	# So the constraints are:
	# max(d1 + d2) <= 1 (no day overlap) OR (one of the time overlap checks)

	overlap_ij = cvx.Variable(3, boolean=True)
	constraints.append(c1_start - c2_start >= class_lengths[idx_2] + overlap_ij[0]*-10)
	constraints.append(c2_start - c1_start >= class_lengths[idx_1] + overlap_ij[1]*-10)
	constraints.append(cvx.max(d1 + d2) <= 1 + 5*overlap_ij[2])
	constraints.append(cvx.sum(overlap_ij) <= 1) # At least one must hold


# Go over conflicts
for group in hard_overlap_groups:
	for i in group:
		for j in group:
			if j > i: # don't add double constraints, e.g. 1<->2 and 2<->1
				add_conflict(i, j, constraints)

problem = cvx.Problem(objective,constraints)
problem.solve(solver = cvx.GLPK_MI)
print("GLPK finished with status", problem.status)
print("Penalty: ", problem.value)

# Interpret the results
hour_class_map = {1:"8:00", 2:"9:00", 3:"10:00", 4:"11:00", 5:"12:00", \
                  6:"13:00", 7:"14:00", 8:"15:00", 9:"16:00", 10:"17:00", \
                  11:"18:00", 12:"19:00"}
hour_5_class_map = {1:"9:00", 2:"10:30", 3:"12:00", 4:"1:30", \
                    5:"3:00", 6:"4:30", 7:"6:00"}

def get_days(d)->str:
	day_names = ["M","Tu","W","Th","F"]
	return "".join([day_names[i] for i in range(D) if 1 == d[i]])

for j in range(J):
	hour = ""
	if 1.5 == class_block_types[j]:
		start_hour = hour_5_class_map[t_var[j].value]
		end_hour   = hour_5_class_map[t_var[j].value + class_lengths[j]//1.5]
	else:
		start_hour = hour_class_map[t_var[j].value]
		end_hour   = hour_class_map[t_var[j].value + class_lengths[j]//1.0]

	print("{} {}: {}-{}, {}".format(j, course_indices_to_names[j], start_hour, end_hour, get_days(d_var[j,:].value)))

