from output_writer import writers

class OutputWriter:
    def __init__(self,typeOfOutputInfo):
        if typeOfOutputInfo == "console":
            self.writer = writers.ConsoleWriter()
        if typeOfOutputInfo == "file":
            self.writer = writers.FileWriter()

    def printOutputSegmentDelimiter(self):
        self.writer.printOutputSegmentDelimiter()

    def outputWarningDelimiter(self):
        self.writer.outputWarningDelimiter()

    def outputErrorDelimiter(self):
        self.writer.outputErrorDelimiter()

    def printErrorText(self, text):
        self.writer.outputErrorDelimiter()
        self.writer.writeTextOutput(text)
        self.writer.outputErrorDelimiter()

    def printWarning(self, warningText):
        self.writer.outputWarningDelimiter()
        self.writer.writeTextOutput(warningText)
        self.writer.outputWarningDelimiter()

    def writeTextOutput(self, text):
        self.writer.writeTextOutput(text)

    def setNewRecord(self):
        self.writer.newRecord()

    def writeFormatedTextOutput(self, text, width):
        self.writer.writeFormatedTextOutput(text, width)
