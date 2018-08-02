from analyst_tool_objects import csv_operators
import os

class CSVManager:

    customClassifierString = "_imagesClassificationResults"

    def getNewcustomClassifierResultsWriter(self, outputWriter, outputFolder, classifierId, prefix):
        path = outputFolder + os.sep + prefix + self.customClassifierString + "_" + classifierId + '.csv'
        return csv_operators.CustomClassifierResultsWriter(outputWriter, path)

    def getCustomClassifierResultsReader_EnsemblePath(self, outputFolder, classifierId, prefix):
        path = outputFolder + os.sep + prefix + self.customClassifierString + "_" + classifierId + '.csv'
        return self.getCustomClassifierResultsReader(path)

    def getCustomClassifierResultsReader(self, fullpath):
        return csv_operators.CustomClassifierResultsReader(fullpath)

    def geRocStatsWriter(self, outputFolder):
        return csv_operators.RocStatsWriter(outputFolder)

    def getNegativeStatsWriter(self, outputFolder):
        return csv_operators.NegativeClassStatsWriter(outputFolder)

    def geCoincidenceMatrixWriter(self, outputFolder):
        return csv_operators.CoincidenceMatrixWriter(outputFolder)
