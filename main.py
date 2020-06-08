# File created: 05/25/2020
# Tested on   : Python 3.7.4
# Author(s)   : Emiko Soroka,
# Unittests   : None
# Description :
# Main file for course scheduling problem

from ucsp import Course, Ucsp
import particleswarm
import csv
import copy
import numpy as np
import matplotlib.pyplot as plt
import datetime

if __name__ == "__main__":
	print("Initializing some random schedules:")
	infilename = input("Data file name: ")
	
	file_rows = []
	with open(infilename, "r") as infile:
		# Use builtin csv reader
		reader = csv.DictReader(infile)
		for row in reader:
			file_rows.append(row)

	N_SAMPLES = 20

	samples = []
	in_points = []

	for k in range(N_SAMPLES):
		random_schedule = []	
	
		for row in file_rows:
			# Exclude TBA classes because they have no timing information
			random_schedule.append( \
			Course.init_random(float(row['meetingLengthHours']), 
			               	int(row['numberOfMeetings']),
			               	row['courseNumber'],
			               	int(row['numberEnrolled']),
			               	row['cantOverlap'],
			               	row['shouldntOverlap']))
	
		ucsp = Ucsp(random_schedule)
		if ucsp.check_feasible():
			samples.append(ucsp)
			in_points.append(ucsp.check_desirable())


	# Compare the best schedules
	best_init_idx = np.argmin(in_points)
	print("Best initial (random) schedule: penalty = ", in_points[best_init_idx])


	# Define iteration phase
	def iteration_phase(samples, k_max, w=1, c1=1, c2=1):

		x_best = np.zeros(N_SAMPLES*2)
		y_best = np.Inf
		for sample in samples:
			#print("Random schedule is feasible?", sample.check_feasible())
			penalty =sample.check_desirable()
			if penalty < y_best:
				y_best = penalty
				x_best = sample.get_all_time_vectors()
			#print("Random schedule is good? Penalty:", penalty)
			sample.v = np.ones(len(sample.schedule), dtype=int)
			sample.x_best = sample.get_all_time_vectors()
			#for name in sample.schedule.keys():
				#print(name, sample.schedule[name])


		# Iterate
		n = len(samples[0].schedule)
		for k in range(0, k_max):
			for i, sample in enumerate(samples):
				x = sample.get_all_time_vectors()
				r1, r2 = np.random.randint(0,4,n, dtype=int), \
				         np.random.randint(0,4,n, dtype=int)
				
				x = sample.add_all_time_vectors(sample.v)
				#print("x + v\n", x)
				# OK so we want to kind of "decay" the iinitial velocity
				# and replace it with a better one # this kind of replaces w parameter for now (HACK)
				sample.v = sample.v//2 + c1*np.multiply(r1, (sample.x_best - x)) + \
				                   c2*np.multiply(r2,(x_best - x))
				
				y = sample.check_desirable()
				
				if y < y_best:
					x_best[:], y_best = x, y
				if y < sample.check_desirable():
					sample.x_best[:] = x

				#print(k*k_max+i, y)

		return samples



	# Define local search phase
	def local_search_phase(samples):
		# OK we're done with particles flying around
		for j, sample in enumerate(samples):

			# Let's try to see if there's any local improvements
			x = sample.get_all_time_vectors()
			delta_x = np.zeros(np.shape(x), dtype=int)
			value = sample.check_desirable()
			
			# Attempt to improve on value in each element of x
			for i, xi in enumerate(x):

				delta_x[i] = 1

				# Check in one direction
				sample_copy = Ucsp(copy.deepcopy(sample.schedule))

				xp = sample_copy.add_all_time_vectors(delta_x)
				value_p = sample_copy.check_desirable()

				# Check in the other direction
				sample_copy = Ucsp(copy.deepcopy(sample.schedule))
				
				xm = sample_copy.add_all_time_vectors(-1*delta_x)
				value_m = sample_copy.check_desirable()


				# an improvement in + direction, set it to x+
				if value_p < value_m and value_p < value:
					sample.add_all_time_vectors(delta_x)
				
				# improvement in - direction is better
				elif value_m < value:
					sample.add_all_time_vectors(-delta_x)
				
				value = sample.check_desirable()
				delta_x[i] = 0
				#print("New value:", sample.check_desirable())


			#print(j, value)
		
		return samples


	for i in range(10):
		samples = iteration_phase(samples, 10)
		samples = local_search_phase(samples)
		
	

	print("\nFinal:")

	out_points = np.zeros(len(samples))
	for i, sample in enumerate(samples):
		print("Random schedule is feasible?", sample.check_feasible())
		penalty = sample.check_desirable()
		out_points[i] = penalty
		print("Random schedule is good? Penalty:", penalty)


	# Plot
	
	x_plot = np.linspace(0, len(in_points),len(in_points))
	plt.scatter(x_plot,in_points, label="Initial")
	plt.scatter(x_plot,out_points, label="Final")
	plt.legend()
	plt.ylabel("Penalty")
	plt.xlabel("Sample number")
	plt.savefig("Plot_{}.png".format(datetime.datetime.now()))
	
	# Compare the best schedules
	best_final_idx = np.argmin(out_points)
	print("Best final schedule: penalty = ", out_points[best_final_idx])
	for course in samples[best_final_idx].schedule:
		print(course)

