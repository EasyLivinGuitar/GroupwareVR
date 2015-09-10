class LogManager:
    header_printed = False

    def __init__(self):
        self.dictionary = []

    def set(self, key, value):
        self.dictionary.append((key, value))

    # print(len(self.dictionary))

    def findIndexOf(self, key):
        for item in self.dictionary:
            if item[0] == key:
                return self.dictionary.index(item)

    def writeToFile(self, path):
        logFile = open(path, "a+")

        mt = self.dictionary[self.findIndexOf("MT")][1]
        id_combined = self.dictionary[self.findIndexOf("ID combined")][1]

        if mt > 0:
            self.dictionary.append(("TP", id_combined / mt))
        else:
            self.dictionary.append(("TP", "ERROR"))

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
