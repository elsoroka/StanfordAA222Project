# File created: 05/25/2020
# Tested on   : Python 3.7.4
# Author(s)   : Emiko Soroka,
# Unittests   : None
# Description :
# Main file for course scheduling problem

from ucsp import Course, Ucsp
import particleswarm
import csv

if __name__ == "__main__":
	print("Initializing some random schedules:")
	infilename = "data/spring_csv_data.csv"# input("Data file name: ")
	
	file_rows = []
	with open(infilename, "r") as infile:
		# Use builtin csv reader
		reader = csv.DictReader(infile)
		for row in reader:
			file_rows.append(row)

	N_SAMPLES = 20

	samples = []
	for k in range(N_SAMPLES):
		random_schedule = dict()	
	
		for row in file_rows:
			# Exclude TBA classes because they have no timing information
			random_schedule[row['courseNumber']] = \
			Course.init_random(float(row['meetingLengthHours']), 
			               	int(row['numberOfMeetings']),
			               	row['courseType'],
			               	int(row['numberEnrolled']),
			               	row['cantOverlap'],
			               	row['shouldntOverlap'])
	
		ucsp = Ucsp(random_schedule)
		if ucsp.check_feasible():
			samples.append(ucsp)

	for sample in samples:
		print("Random schedule is feasible?", sample.check_feasible())
		print("Random schedule is good? Penalty:", sample.check_desirable())
		#for name in sample.schedule.keys():
			#print(name, sample.schedule[name])