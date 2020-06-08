# File created: 05/18/2020
# Tested on   : Python 3.7.4
# Author      : Emiko Soroka
# Unittests   : None
# Description :
# Quick hack to ingest JSON data and spit out CSV files, will extend later
# How to use  : Run file. Enter input JSON file when prompted and output CSV file name when prompted.

import json

def parseJsonData(infile, outfile):

		# OK the data we have is kind of in an unwantedly-structured format
		# Division: (grad/undergrad/etc)
		# contains department ("AA")
		# contains list of courses
		# courses have structure (EXAMPLE)
		# {
		#   "division":"Graduate",
		#   "department":"AA",
		#   "courseNumber":"AA 222:",
		#   "courseTitle":"Engineering Design Optimization (CS 361)",
		#   "sections":[{
		#                 "courseType":"LEC",
		#                 "enrolled":83,
		#                 "meetings":[{
		#                               "startTime":900,
		#                               "endTime":980,
		#                               "days":[1,3],
		#                               "timeIsTBA":false,
		#                               "bldg":"Skillaud"
		#                            }]
		#              }],
		#   "term":"2019-2020 Spring",
		#   "university":"Stanford University"
		# },
		
		# This code flattens them to
		# dept, courseNumber, courseType, number of meetings, meeting length in hour blocks
		# (if timeisTBA is true, there will be 0 meetings of 0 length)
		# and number enrolled
		# This makes the header row
		outfile.write("number,courseName,startTime,endTime,dayCode\r\n")
		
		rawData = json.load(infile)
		for divisionName in rawData.keys(): # iterate over division (grad/undergrad etc)
			division = rawData[divisionName]
			for deptName in division: # iterate over departments
				dept = division[deptName]
				# Now dept is a list of Course objects
				for course in dept:
					writeCourseToFile(course, outfile)


def writeCourseToFile(course, outfile):
	# In the JSON file, time is in 10 minute increments
	# It makes more sense for us to use floating-point hours
	# and treat the 10 minute passing period as part of the course time
	# Some courses have multiple sections
	# and we will treat these as separate
	# Some sections have multiple meetings # TODO handle these
	i=0
	for section in course['sections']:
		for meeting in section['meetings']:
		
			# Default if class section is TBA
			timeHours = 0.0; numMeetings = 0
			# If section is not TBA (there is a time and date associated with it)
			if not meeting['timeIsTBA']:

				# Count the DAYS per week this class meets
				daysCode = [0,0,0,0,0]
				for d in meeting['days']:
					daysCode[d] = 1
				daysCode = "".join([str(d) for d in daysCode])

				# Write as a CSV string
				outfile.write(",".join([str(i),
					course['courseNumber'].rstrip(":"),
					str(int(2*(meeting['startTime']/60 - 8))),
					str(int(2*((meeting['endTime']+10)/60- 8))), # add passing period
					daysCode]) + "\r\n")
				i += 1


if __name__ == "__main__":
	infilename = input("Enter a JSON schedule file ")
	with open(infilename, "r") as infile:
		
		outfilename = input("Output file name (add .csv) ")
		with open(outfilename, "w") as outfile:
			parseJsonData(infile, outfile)