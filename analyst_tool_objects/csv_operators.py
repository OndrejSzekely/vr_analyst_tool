import csv
import os

class CustomClassifierResultsWriter:
    formattingWidth = 35

    def __init__(self, outputWriter , path):
        self.filePath = path
        self.csvResults = open(self.filePath, 'w', newline='')
        self.spamwriter = csv.writer(self.csvResults, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        self.classesList = None
        self.outputInfoWriter = outputWriter

    def writeHeader(self, classesList):
        header = ['IMAGE', ]
        for classRec in classesList:
            header.append(classRec.upper())
        header.append('ID_OF_WINNING_CLASS')
        header.append('SCORE')
        self.spamwriter.writerow(header)
        self.classesList = classesList
        self.outputInfoWriter.writeFormatedTextOutput(header, self.formattingWidth)

    def pasteHeader(self, header):
        self.spamwriter.writerow(header)

    def writeResults(self, imagesPath, results):
        for imageIndex in range(len(results["images"])):
            imageName = os.path.basename(results["images"][imageIndex]["image"])
            imagePath = imagesPath + os.sep + imageName
            rowData = [imageName]
            id = 1
            aux = 0
            aux2 = 1
            for className in self.classesList:
                for classResult in results["images"][imageIndex]["classifiers"][0]["classes"]:
                    if classResult["class"] == className:
                        rowData.append(classResult["score"])
                        if classResult["score"] >= aux:
                            id = aux2
                            aux = classResult["score"]
                        aux2 = aux2 + 1
            rowData.append(id)
            rowData.append(aux)
            self.spamwriter.writerow(rowData)
            rowData = [str(x) for x in rowData]
            self.outputInfoWriter.writeFormatedTextOutput(rowData, self.formattingWidth)

    def pasteResult(self, row):
        self.spamwriter.writerow(row)

    def close(self):
        self.csvResults.close()

class CustomClassifierResultsReader:

    def __init__(self, filePath):
        self.resultsFile = open(filePath, 'r')
        self.csvreader = csv.reader(self.resultsFile, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)

    def getHeader(self):
        return next(self.csvreader, None)

    def hasNextRow(self):
        try:
            self.row = next(self.csvreader)
            return True
        except Exception:
            return False

    def getRow(self):
        return self.row

    def close(self):
        self.resultsFile.close()


class RocStatsWriter:

    def __init__(self, outputFolder):
        self.rocStatsCsv = open(outputFolder + os.sep + 'ROCStats.csv', 'w', newline='')
        self.writer = csv.writer(self.rocStatsCsv, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        self.writer.writerow(['AUC', 'EER threshold', 'EER', 'Optimal TPR (Optimal recall/sensitivity)', 'Optimal FPR',
                         'Optimal nearest distance threshold'])

    def writeStats(self, auc, eerTreshold, eer, optimalSensitivity, optimalFPR, optimalNearDistThresh):
       self.writer.writerow([auc, eerTreshold, eer, optimalSensitivity, optimalFPR, optimalNearDistThresh])

    def close(self):
        self.rocStatsCsv.close()

class NegativeClassStatsWriter:

    def __init__(self, outputFolder):
        self.rocStatsCsv = open(outputFolder + os.sep + 'negativeClassStatistics.csv', 'w', newline='')
        self.writer = csv.writer(self.rocStatsCsv, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        self.writer.writerow(["MEAN_SCORE", "STD_DEV_SCORE", "MAX_SCORE"])

    def writeRow(self, row):
       self.writer.writerow(row)

    def close(self):
        self.rocStatsCsv.close()

class CoincidenceMatrixWriter:

    def __init__(self, outputFodler):
        self.outputCsv = open(outputFodler + os.sep + 'CoincidenceMatrixWithNegative.csv', 'w', newline='')
        self.spamwriter = csv.writer(self.outputCsv, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)

    def writeHeader(self, header):
        self.spamwriter.writerow(header)

    def writeRow(self, row):
        self.spamwriter.writerow(row)

    def close(self):
        self.outputCsv.close()