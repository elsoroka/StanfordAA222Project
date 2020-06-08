# File created: 06/04/2020
# Tested on   : Python 3.7.4
# Author(s)   : Emiko Soroka,
# Unittests   : None
# Description : Reads a schedule file (like course_heatmap.py)
# and the accompanying data (that the schedule was generated from)
# (to get the penalty groups)
# and computes the penalty on the schedule for easy comparison.

import csv
import numpy as np

def check_overlap(row1, row2)->True or False:
	d1 = np.array([int(d) for d in row1['dayCode']])
	d2 = np.array([int(d) for d in row2['dayCode']])
	
	# Remember the overlap happens if NONE of these hold.
	return not any([
		int(row1['startTime']) - int(row2['endTime']) >= 0,
		int(row2['startTime']) - int(row1['endTime']) >= 0,
		np.max(np.add(d1, d2)) <= 1,
		])


if __name__ == "__main__":

	schedulefile = open(input("Optimal schedule file (csv): "), "r")
	groupsfile   = open(input("Original data (csv): "), "r")

	# Memory inefficient: Read the whole schedule into memory.
	reader = csv.DictReader(schedulefile)
	rows = [row for row in reader]


	# Check for hard overlap violations and soft overlaps
	overlap_count   = 0
	violation_count = 0
	# We want to figure out the groups
	for i,r in enumerate(csv.DictReader(groupsfile)):
		# convert to 0-based indexing
		hard_group = [int(g)-1 for g in r['cantOverlap'].split(";") if g != ""]
		soft_group = [int(g)-1 for g in r['shouldntOverlap'].split(";") if g != ""]

		for other_idx in hard_group:

			# A course overlapping itself doesn't count
			if i != other_idx and check_overlap(rows[i], rows[other_idx]):
				#print("ERROR: ", rows[i], " conflicts with ", rows[other_idx])
				violation_count += 1

		# Check the soft overlap groups
		for other_idx in soft_group:
			if i != other_idx and check_overlap(rows[i], rows[int(other_idx)]):
				#print("WARNING: ", rows[i], " conflicts with ", rows[other_idx])
				overlap_count += 1

	# doesn't really work
	#print("Hard group violations:", violation_count)
	print("Soft group overlaps  :", overlap_count)



	# Check all the courses for outside business hours violations
	odd_hours_count = 0
	lunch_count = 0 # and classes during lunch break
	for j in range(len(rows)):
		#print(rows[j]['courseName'], int(rows[j]['startTime']), int(rows[j]['endTime']))
	 	# 2 = our index for 9am, business hours, 18 = our index for 5pm
		if int(rows[j]['startTime']) < 2 or int(rows[j]['endTime']) > 18:
			odd_hours_count += 1
			
		if int(rows[j]['startTime']) == 10 or int(rows[j]['endTime']) == 11:
			
			lunch_count += 1

	print("Odd hours:", odd_hours_count)
	print("Lunchtime:", lunch_count)



	# Responsibly close our files
	schedulefile.close()
	groupsfile.close()