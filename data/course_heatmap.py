import csv, argparse
import numpy as np
import matplotlib.pyplot as plt



parser = argparse.ArgumentParser(description='Make course heatmap')
parser.add_argument("--names",
                    action="store_true",
                   help='Show course names on heatmap (for small datasets)')

parser.add_argument("--data",
					type=str,
                   help='Filename to read from ')

args = parser.parse_args()


# Works with output files that have startTime, endTime, dayCode. Ex:
#number,courseName,timeString,dayString,startTime,endTime,dayCode
#0,AA 203, 9:00-10:30, TuTh,2,5,01010

def make_heatmap_from_file(names=False)->None:
	# We want it from 8am - 8pm in 30 minute increments
	# that's 24 spaces x 5 days
	grid = np.zeros((24,5), dtype=int)
	labels = [["" for j in range(5)] for i in range(24)]

	with open(args.data, "r") as infile:
		# Use builtin csv reader
		reader = csv.DictReader(infile)
		for row in reader:
			startTime = int(row['startTime'])
			endTime   = int(row['endTime'])
			dayCode   = row['dayCode']

			for i,d in enumerate(dayCode):
				if '1' == d:
					grid[startTime:endTime,i] += np.ones(endTime-startTime, dtype=int)
					if names:
					# Labels - uncomment for VERY SMALL data sets where you can label individual courses
						for t in range(startTime, endTime):
							if grid[t,i] == 1: # first time
								labels[t][i] += "AA "
							labels[t][i] += (row['courseName'].split(" "))[-1] + ", "# + ("\n" if grid[t,i]>=2 else "")

	for i in range(24):
		print(grid[i,:])

	# Plot
	# Based on https://matplotlib.org/gallery/images_contours_and_fields/image_annotated_heatmap.html?highlight=heatmap

	times = ["8:00am", "8:30am", "9:00am", "9:30am", "10:00am", "10:30am", "11:00am", "11:30am", \
	         "12:00pm", "12:30pm", "1:00pm", "1:30pm", "2:00pm", "2:30pm", "3:00pm", "3:30pm", \
	         "4:00pm", "4:30pm", "5:00pm", "5:30pm", "6:00pm", "6:30pm", "7:00pm", "7:30pm",]
	         #"8:00pm", "8:30pm", "9:00pm", "9:30pm"]
	days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday",]
	fig, ax = plt.subplots()
	im = ax.imshow(grid, aspect='auto')

	# We want to show all ticks...
	ax.set_xticks(np.arange(len(days)))
	ax.set_yticks(np.arange(len(times)))
	# ... and label them with the respective list entries
	ax.set_xticklabels(days)
	ax.set_yticklabels(times)
	
	ax.xaxis.tick_top() # Day labels belong on top of heatmap

	# Labels - uncomment for VERY SMALL data sets where you can label individual courses
	# Loop over data dimensions and create text annotations.
	for i in range(len(times)): # y axis
		for j in range(len(days)): # x axis
		# Label with either course names (small number of courses) or class count.
			if names:
				text = ax.text(j, i, labels[i][j], ha="center", va="center", color="w")
			else:
				text = ax.text(j,i,str(grid[i,j]), ha="center", va="center", color="w")

	#plt.savefig(input("Save file as (include .png): "))
	plt.show()

if __name__ == "__main__":
	make_heatmap_from_file(names=args.names)