import os.path

class LogManager:
    header_printed = False
    path = ""
    taskString = ""
    dictionary = []
    saveTrialNum = -1

    def __init__(self, taskString):
        self.taskString = taskString        

    def set(self, key, value):
        self.dictionary.append((key, value))

    # print(len(self.dictionary))

    def findIndexOf(self, key):
        for item in self.dictionary:
            if item[0] == key:
                return self.dictionary.index(item)

    def writeToFile(self, pathFolder):
        # find out which file number, init
        if self.saveTrialNum < 0:
            while True:
                self.saveTrialNum += 1
                self.path = pathFolder + self.taskString + "_trial" + str(self.saveTrialNum) + ".csv"
                if not os.path.isfile(self.path):
                    break
               
            self.created_logfile = True

        #logging code
        logFile = open(self.path, "a+")

        mt = self.dictionary[self.findIndexOf("MT [s]")][1]
        id_combined = self.dictionary[self.findIndexOf("ID combined [bit]")][1]

        if mt > 0:
            self.dictionary.append(("TP [bit/s]", id_combined / mt))
        else:
            self.dictionary.append(("TP [bit/s]", "ERROR"))

        # print header only once
        if not self.header_printed:
            header = ""
            for item in self.dictionary:
                header = header + str(item[0]) + ", "
            logFile.write(header + "\n")
            self.header_printed = True

        data = ""
        for item in self.dictionary:
            data = data + str(item[1]) + ", "

        logFile.write(data + "\n")
        logFile.close()
        self.dictionary = []
