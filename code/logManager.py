import math

class logManager():
	header_printed=False

	def __init__(self):
		self.dictionary = []

	def set(self, key, value):
		self.dictionary.append((key, value))
		# print(len(self.dictionary))

	def findIndexOf(self, key):
		for item in self.dictionary: 
			if item[0]==key:
				return self.dictionary.index(item)

	def writeToFile(self, path):
		logFile = open(path, "a+")

		MT_index = self.findIndexOf("MOVEMENT_TIME")
		ID_index = self.findIndexOf("ID_COMBINED")

		if(self.dictionary[MT_index][1]>0):
			self.dictionary.append(("THROUGHPUT", self.dictionary[ID_index][1]/self.dictionary[MT_index][1]))
		else:
			self.dictionary.append(("THROUGHPUT", "ERROR"))

		# print header only once
		if(self.header_printed == False):
			header = ""
			for item in self.dictionary:
				header = header + str(item[0]) + ", "
			logFile.write(header + "\n")
			self.header_printed = True

		data = ""
		for item in self.dictionary:
			data = data + str(item[1]) + ", "

		logFile.write(data + "\n")
		logFile.close
		self.dictionary=[]