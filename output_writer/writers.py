class ConsoleWriter:
    outputSegmentDelimiterString = '#########################################'
    outputWarningDelimiterString = '/////////////////////////////////////////'
    outputErrorDelimiterString = '!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!'

    def printOutputSegmentDelimiter(self):
        print(self.outputSegmentDelimiterString)

    def outputWarningDelimiter(self):
        print(self.outputWarningDelimiterString)

    def outputErrorDelimiter(self):
        print(self.outputErrorDelimiterString)

    def writeTextOutput(self, text):
        print(text)

    def newRecord(self):
        print("\n")

    def writeFormatedTextOutput(self, text, width):
        textFormated = ""
        for element in text:
            textFormated = textFormated + element.ljust(width)

        print(textFormated)

class FileWriter:
    outputSegmentDelimiterString = '#########################################'
    outputWarningDelimiterString = '/////////////////////////////////////////'
    outputErrorDelimiterString = '!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!'

    def __init__(self):
        self.file = open("./log.txt", "w")

    def printOutputSegmentDelimiter(self):
        self.file.write(self.outputSegmentDelimiterString)
        self.file.write("\n")
        self.file.flush()

    def outputWarningDelimiter(self):
        self.file.write(self.outputWarningDelimiterString)
        self.file.write("\n")
        self.file.flush()

    def outputErrorDelimiter(self):
        self.file.write(self.outputErrorDelimiterString)
        self.file.write("\n")
        self.file.flush()

    def writeTextOutput(self, text):
        self.file.write(text)
        self.file.write("\n")
        self.file.flush()

    def newRecord(self):
        self.file.write("\n")
        self.file.write("\n")
        self.file.flush()

    def writeFormatedTextOutput(self, text, width):
        textFormated = ""
        for element in text:
            textFormated = textFormated + element.ljust(width)

        self.file.write(textFormated)
        self.file.write("\n")
        self.file.flush()