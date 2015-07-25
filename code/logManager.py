import math

class logManager():
	header_printed=False

	def __init__(self):
		self.dictionary = {}

	def set(self, key, value):
		self.dictionary[key] = value

	def writeToFile(self, path):
		logFile = open(path, "a+")

		#update
		if( self.dictionary["MovementTime"] >0):
			self.dictionary["throughput"] = self.dictionary["ID_COMBINED"]/self.dictionary["MovementTime"]

		#print header only once
		if(self.header_printed==False):
			header = ""
			for key in self.dictionary.keys():
				header = header + str(key) + ","
			header = header+"\n\n" 
			logFile.write(header)
			self.header_printed = True

		line = ""
		for value in self.dictionary.values():
			line = line + str(value) + ","
		line = line + "\n"
		logFile.write(line)	
		logFile.close()