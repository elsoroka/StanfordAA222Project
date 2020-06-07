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
	soft_group = [int(g)-1 for g in row['shouldntOverlap'].split(";") if g != '']
	if [] != soft_group:
		# Don't forget to add this class to the group!
		soft_group.append(int(row['dataNumber'])-1) # convert to 0-based indexing
		soft_overlap_groups.append(soft_group)

	# Retrieve the hard constraint group
	hard_group = [int(g)-1 for g in row['cantOverlap'].split(";") if g != '']
	if [] != hard_group:
		hard_group.append(int(row['dataNumber'])-1)
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

 # Number of classes
J = len(class_lengths)
# Close file
infile.close()



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
	fri_class_p = 0.0; mon_class_p = 0.0
	
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
		
		# penalty for Friday and Monday classes
		# promotes MW and TuTh over WF for 2-days-per-week classes
#		fri_class_p += d_var[j,-1]
#		mon_class_p += d_var[j,:] - d_var[j,:]

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

					# Add the penalty
					# Want 0 >= cvx.max(d1 + d2) - 1
					# if all are violated, e.g. positive
					# we get a penalty
					# Classes DO overlap when:
					#   t1[ ]t2
					# 1[      ]c2
					# and max(d1 + d2) - 2 == 0 or -1
					# min(-d1 + -d2) + 1 = 0 (no violation) or -1 (violation)
					# so c1 - t1 + -10*(max(d1 + d2) - 2) >= 0 for overlap
					# -c1 + t1 + 10*(max(d1 + d2) - 2) <= 0 for overlap
					# Don't question it!
					# It isn't a DCP error!
					overlap_p += \
					cvx.pos(c1_start - c2_start - (cvx.min(-d1 + -d2) + 2)) + \
					cvx.pos(c1_start + class_lengths[j] - c2_start - (cvx.min(-d1 + -d2) + 2))
					
	# Third. Penalize classes occurring at lunchtime.
	# Implemented with:
	# Fourth. Penalize classes "bunched together" in time. e.g. all in the morning.
	# This is necessary to spread the classes throughout the day.
	# Use the idea that each class is slightly "attracted to" a random "good" time.
	# That should spread them out.
	# While we're at it, don't "attract" courses to lunchtime spots.
	BEST_1_5_SPOTS = [1,2,4,5]*((J+3)//4)
	BEST_1_0_SPOTS = [2,3,4,6,7,8]*((J+5)//6)

	cluster_penalty = 0.0
	for j in range(J):
		if 1.5 == class_block_types[j]:
			cluster_penalty += cvx.abs(t_var[j] - np.random.choice(BEST_1_5_SPOTS, replace=False))
		else:
			cluster_penalty += cvx.abs(t_var[j] - np.random.choice(BEST_1_0_SPOTS, replace=False))

	# Fifth. Promote spreading courses out over the week, e.g. not clustered on a single day.
	
	# Averaging term - total number of course meetings / total days
	AVG_MEETINGS_PER_DAY = np.sum(class_day_types)/D
	# spread in days
	day_spread = 0
	for d in range(D):
		day_spread += cvx.pos(cvx.sum(d_var[:,d]) - AVG_MEETINGS_PER_DAY)

	# ADJUST RELATIVE WEIGHTS HERE
	return 1 * time_p + 10 * overlap_p + day_spread*1 + cluster_penalty*2.0

# Set objective
objective = cvx.Minimize(penalty(t_var))


# CONSTRAINTS

for j in range(J):
	# Add constraints on class start/end times
	lb, ub = FIRST_1_0_BLOCK, LAST_1_0_BLOCK
		
	if 1.5 == class_block_types[j]: # class divisible into 1.5 hour blocks
		lb = FIRST_1_5_BLOCK
		ub = LAST_1_5_BLOCK - (class_lengths[j]//1.5 - 1)

	else: # divisble into 1.0 hours
		lb = FIRST_1_0_BLOCK
		ub = LAST_1_0_BLOCK - (class_lengths[j]//1 - 1)
 
	# print("Course {}, lb, {}, ub, {}".format(j, lb, ub))
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


def add_conflict(idx_1, idx_2, bool_idx, constraints):
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
	if 1.5 == class_block_types[idx_1]: # and 1.0 == class_block_types[idx_2]:
		# Convert to 1 hour overlap
		c1_start = c1_start + 1 + (c1_start-1)/2

	if 1.5 == class_block_types[idx_2]: # and 1.0 == class_block_types[idx_1]:
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

	overlap_ij = conflict_booleans[bool_idx,:]

	constraints.append(c1_start - c2_start >= class_lengths[idx_2] + overlap_ij[0]*-100)
	constraints.append(c2_start - c1_start >= class_lengths[idx_1] + overlap_ij[1]*-100)
	constraints.append(cvx.max(d1 + d2) <= 1 + 10*overlap_ij[2])
	constraints.append(cvx.sum(overlap_ij) <= 2) # At least one must hold


# Cont the number of conflicts we have
n_conflicts = 0
for group in hard_overlap_groups:
	for i in group:
		for j in group:
			if j > i:
				print(i,j)
				n_conflicts += 1 if j > 1 else 0

print("There are ", n_conflicts, "conflicts")
# Now we know how many conflicts there are, we can define booleans to control their constraints
conflict_booleans = cvx.Variable((n_conflicts, 3), boolean=True)
# Go over conflicts
bool_idx = 0
for group in hard_overlap_groups:
	for i in group:
		for j in group:
			if j > i: # don't add double constraints, e.g. 1<->2 and 2<->1
				print("Adding conflict:", i, j)
				add_conflict(i, j, bool_idx, constraints)
				bool_idx += 1


problem = cvx.Problem(objective,constraints)
problem.solve(solver = cvx.GLPK_MI)
print("GLPK finished with status", problem.status)
print("Penalty: ", problem.value)

# Interpret the results
hour_class_map = {1:("8:00",0), 2:("9:00",2), 3:("10:00",4), 4:("11:00",6), 5:("12:00",8), \
                  6:("13:00",10), 7:("14:00",12), 8:("15:00",14), 9:("16:00",16), \
                  10:("17:00",18), 11:("18:00",20), 12:("19:00",22)}
hour_5_class_map = {1:("9:00",2), 2:("10:30",5), 3:("12:00",8), 4:("1:30",11), \
                    5:("3:00",14), 6:("4:30",17), 7:("6:00",21), 8:("7:30",24)}


def get_days(d)->str:
	day_names = ["M","Tu","W","Th","F"]
	return "".join([day_names[i] for i in range(D) if 1 == d[i]])

# Print the header and data
print("number,courseName,timeString,dayString,startTime,endTime,dayCode")
for j in range(J):
	hour = ""
	if 1.5 == class_block_types[j]:
		start_hour, start_code = hour_5_class_map[t_var[j].value]
		end_hour, end_code   = hour_5_class_map[t_var[j].value + class_lengths[j]//1.5]
	else:
		start_hour, start_code = hour_class_map[t_var[j].value]
		end_hour, end_code   = hour_class_map[t_var[j].value + class_lengths[j]//1.0]

	print("{},{}, {}-{}, {},{},{},{}".format(j, course_indices_to_names[j], \
		                                   start_hour, end_hour, get_days(d_var[j,:].value), \
		                                   start_code, end_code, "".join([str(int(d)) for d in d_var[j,:].value])))
