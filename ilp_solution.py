import numpy as np
import cvxpy as cvx

# Test data setup
# Length of each class in multiples of 1 hour.
class_lengths     = [2, 1, 2, 2] # 1.5 hours, 1.0 hours, 1.5 hours, 2
class_block_types = [1.5, 1, 1.5, 1] # class is in 1.5 hour or 1 hour blocks

# Type of each class
class_day_types   = [2, 3, 2, 1]

J = len(class_lengths) # Number of classes
print("J", J)
hard_overlap_groups = [[0,2,3],]


# Solver setup

D = 5 # length of day vector
# Represent the times in half-hour blocks so the 1.5 hour classes
# can be represented by integer variables
# Range for 1.5 hour multiple classes: 10, 13, 16, 19, 22 25
FIRST_1_5_BLOCK = 1  # represents 9.00
LAST_1_5_BLOCK  = 7 # represents 18:00
# Range for 1 hour multiple classes
FIRST_1_0_BLOCK = 1  # represents 8:00 
LAST_1_0_BLOCK  = 12 # represents 19:00
#                1  2  3   4   5   6   7   8   9   10  11  12 
# 1.0 blocks are 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19
#                1   2     3    4    5   6    7
# 1.5 blocks are 9, 10:30, 12, 1:30, 3, 4:30, 6
CONVERT_1_5_TO_1_OVERLAP = {1:[2,3], 2:[3,4], 3:[5,6], 4:[6,7], 5:[8,9], 6:[9,10], 7:[11,12]}
# 1 2 3 4 5 6 7 
# 2 3 5 6 8 9 11
# x + 1 + (x-1)//2
# x + 1 + (x-1)//2


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

objective = cvx.Minimize(0.0) # feasibility problem

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


for j in range(J):
	print("Class {} : time {}".format(j, t_var[j].value))
	for d in range(D):
		print(d_var[j,d].value)
