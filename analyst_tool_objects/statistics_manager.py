from analyst_tool_objects import csv_manager
import os
import math
import numpy
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import shutil
import statistics

class StatisticsManager:

    def __init__(self, outputWriter, filesManager):
        self.outputWriter = outputWriter
        self.filesManager = filesManager
        self.csvManger = csv_manager.CSVManager()

    def checkIfClassDirectoryExists(self, classLabel, outputFolder):
        if self.filesManager.checkPath(outputFolder + os.sep + classLabel) == False:
            os.mkdir(outputFolder + os.sep + classLabel)

    def sortClassifiedImages(self, jsonConfig):

        if not "scored_images_csv" in jsonConfig:
            jsonConfig["scored_images_csv"] = jsonConfig["csv_path"] + os.sep + jsonConfig["file_prefix"] + \
                                              self.csvManger.customClassifierString + "_" + jsonConfig["classifier_id"] + ".csv"


        scoredImagesCsv = jsonConfig["scored_images_csv"]
        outputFolder = jsonConfig["output_folder"]
        imagesFolder = jsonConfig["images_folder"]
        threshold = jsonConfig["threshold"]


        self.outputWriter.setNewRecord()
        self.outputWriter.writeTextOutput("Sorting images based on vr results ...")
        self.outputWriter.setNewRecord()

        if self.filesManager.checkFile(scoredImagesCsv) == False:
            raise Exception("ERROR: VISUAL RECOGNITION RESULTS FILE PATH IS NOT VALID.")

        outputFolder = self.filesManager.removeLastSlashInFolderPath(outputFolder)
        imagesFolder = self.filesManager.removeLastSlashInFolderPath(imagesFolder)


        if self.filesManager.checkPath(imagesFolder) == False:
            raise Exception("ERROR: PATH TO IMAGES FOLDER IS NOT VALID.")

        if self.filesManager.checkPath(outputFolder) == False:
            raise Exception("ERROR: OUTPUT FOLDER IS NOT VALID.")

        vrResultsReader = self.csvManger.getCustomClassifierResultsReader(scoredImagesCsv)
        labels = vrResultsReader.getHeader()

        while vrResultsReader.hasNextRow():
            row = vrResultsReader.getRow()
            classLabel = "negative"
            if float(row[-1]) >= threshold:
                classLabel = labels[int(row[-2])].lower()
            self.checkIfClassDirectoryExists(classLabel, outputFolder)
            shutil.copy(imagesFolder + os.sep + row[0], outputFolder + os.sep + classLabel + os.sep + row[0])

    def computeBinaryClassifierStatistics(self, classesInfo, negativeClassInfo, outputFolder, classifierId):

        performanceTresholdStep = 0.02

        className = classesInfo[0]
        classResultsReader = self.csvManger.getCustomClassifierResultsReader_EnsemblePath(outputFolder, classifierId, className)
        classResultsReader.getHeader()

        negativeClassResultsReader = self.csvManger.getCustomClassifierResultsReader_EnsemblePath(outputFolder, classifierId, "negative")
        negativeClassResultsReader.getHeader()

        valuesClass = []
        valuesNegative = []

        while classResultsReader.hasNextRow():
            valuesClass.append(float(classResultsReader.getRow()[3]))

        while negativeClassResultsReader.hasNextRow():
            valuesNegative.append(float(negativeClassResultsReader.getRow()[3]))

        negativeClassResultsReader.close()
        classResultsReader.close()

        TPList = []
        TNList = []
        FPList = []
        FNList = []
        accuracy = []
        precision = []
        recall = []
        tresholdList = []
        treshold = 0.0

        while treshold < 1:
            tresholdList.append(treshold)
            TP = len([x for x in valuesClass if x > treshold])
            TN = len([x for x in valuesNegative if x <= treshold])
            FP = len([x for x in valuesNegative if x > treshold])
            FN = len([x for x in valuesClass if x <= treshold])
            TPList.append(TP)
            TNList.append(TN)
            FPList.append(FP)
            FNList.append(FN)
            accuracy.append(float(TP + TN)/float(TP + TN + FP + FN))
            if TP + FP == 0:
                precision.append(0)
            else:
                precision.append(TP / float(TP + FP))
            recall.append(TP / float(TP + FN))

            treshold = min(1, treshold + performanceTresholdStep)

        TPListNorm = [(TPList[i] / (TPList[i] + FNList[i])) for i in range(0, len(FNList))]
        TPListNorm = TPListNorm[::-1]

        FPListNorm = [(FPList[i] / (FPList[i] + TNList[i])) for i in range(0, len(FNList))]
        FPListNorm = FPListNorm[::-1]

        FNListNorm = [(FNList[i] / (FNList[i] + TPList[i])) for i in range(0, len(FNList))]
        FNListNorm = FNListNorm[::-1]

        tresholdListReversed = tresholdList[::-1]

        auc = numpy.trapz(TPListNorm, x=FPListNorm)
        eer = math.inf
        minDif = math.inf
        eerThreshold = 0
        optimalSensitivity = math.inf
        optimalFPR = math.inf
        optimalNearDistThresh = 0
        minDist = math.inf
        epsilon = 0.001

        listlen = len(FPListNorm)

        for i in range(listlen):
            fnr = FNListNorm[i]
            fpr = FPListNorm[i]

            diff = abs(fnr - fpr)
            if diff < minDif and fnr != 0 and fpr != 0:
                minDif = diff
                eer = fpr
                eerThreshold = tresholdListReversed[i]

        for i in range(listlen):
            p1 = (0, 1)
            p2 = (FPListNorm[i], TPListNorm[i])

            distance = math.sqrt((p2[0] - p1[0])*(p2[0] - p1[0]) + (p2[1] - p1[1])* (p2[1] - p1[1]))
            if distance < minDist:
                minDist = distance
                optimalSensitivity = TPListNorm[i]
                optimalFPR = FPListNorm[i]
                optimalNearDistThresh = tresholdListReversed[i]

        rocStatsWriter = self.csvManger.geRocStatsWriter(outputFolder)
        rocStatsWriter.writeStats(auc, eerThreshold, eer, optimalSensitivity, optimalFPR, optimalNearDistThresh)
        rocStatsWriter.close()

        plt.plot(FPListNorm, TPListNorm)
        plt.xlabel('False positive rate')
        plt.ylabel('True positive rate')
        plt.title('ROC curve')
        plt.savefig(outputFolder + os.sep + 'roc.png')
        plt.clf()

        plt.plot(tresholdList, accuracy)
        plt.xlabel('Confidence Treshold')
        plt.ylabel('Accuracy')
        plt.title('Accuracy of classifier')
        plt.savefig(outputFolder + os.sep + 'accuracy.png')
        plt.clf()

        plt.plot(tresholdList, precision)
        plt.xlabel('Confidence Treshold')
        plt.ylabel('Precision')
        plt.title('Precision of classifier')
        plt.savefig(outputFolder + os.sep + 'precision.png')
        plt.clf()

        plt.plot(tresholdList, recall)
        plt.xlabel('Confidence Treshold')
        plt.ylabel('Recall')
        plt.title('Recall of classifier')
        plt.savefig(outputFolder + os.sep + 'recall.png')
        plt.clf()

        plt.plot(tresholdList, TPList, label='TP')
        plt.plot(tresholdList, FPList, label='FP')
        plt.plot(tresholdList, FNList, label='FN')
        plt.legend(loc='upper right')
        plt.xlabel('Confidence Treshold')
        plt.ylabel('Number of images')
        plt.title('Counts')
        plt.savefig(outputFolder + os.sep + 'counts.png')

        returnStatsJson = {
            "eerThreshold": eerThreshold
        }

        return returnStatsJson

    def computeCoincidenceMatrixWithNegative(self, classesInfo, negativeClassInfo, outputFolder, classifierId, treshold):

        csvWriter = self.csvManger.geCoincidenceMatrixWriter(outputFolder)

        classes = classesInfo

        header = ['CLASS_ID']
        for className in classes:
            header.append(className.upper() + "_COUNT")
            header.append(className.upper() + "_PERCENTAGE")
        header.append("NEGATIVE")
        header.append("NEGATIVE_PERCENTAGE")
        csvWriter.writeHeader(header)

        for className in classes:
            classResultsReader = self.csvManger.getCustomClassifierResultsReader_EnsemblePath(outputFolder, classifierId, className)
            classResultsReader.getHeader()
            count = []
            rowData = [className.upper()]
            classId = len(classes) + 1
            lastIndex = classId - 1
            for v in range(0, len(classes) + 1):
                count.append(0)
            while classResultsReader.hasNextRow():
                row = classResultsReader.getRow()
                ind = int(row[classId])
                if float(row[classId + 1]) > treshold:
                    count[ind - 1] = count[ind - 1] + 1
                else:
                    count[lastIndex] = count[lastIndex] + 1
            sumClass = sum(count)
            for classCount in count:
                rowData.append(classCount)
                if sumClass == 0:
                    rowData.append(0)
                else:
                    rowData.append(float(classCount) / float(sumClass))
            csvWriter.writeRow(rowData)
            classResultsReader.close()

        negativeClassResultsReader = self.csvManger.getCustomClassifierResultsReader_EnsemblePath(outputFolder, classifierId, "negative")
        negativeClassResultsReader.getHeader()
        count = []
        rowData = ["NEGATIVE"]
        classId = len(classes) + 1
        lastIndex = classId - 1
        for v in range(0, len(classes) + 1):
            count.append(0)
        while negativeClassResultsReader.hasNextRow():
            row = negativeClassResultsReader.getRow()
            ind = int(row[classId])
            if float(row[classId + 1]) > treshold:
                count[ind - 1] = count[ind - 1] + 1
            else:
                count[lastIndex] = count[lastIndex] + 1
        sumClass = sum(count)
        for classCount in count:
            rowData.append(classCount)
            rowData.append(float(classCount) / float(sumClass))
        csvWriter.writeRow(rowData)
        negativeClassResultsReader.close()
        csvWriter.close()

    def createMissclassificationFolders(self, classesInfo, negativeClassInfo, outputFolder, classifierId, treshold):

        for classInfo1 in classesInfo:
            for classInfo2 in classesInfo:
                if classInfo1["class_name"] != classInfo2["class_name"]:
                    os.mkdir(outputFolder + os.sep + classInfo1["class_name"] + "_as_" + classInfo2["class_name"])
            if negativeClassInfo != None:
                os.mkdir(outputFolder + os.sep + "negativeClass" + "_as_" + classInfo1["class_name"])
                os.mkdir(outputFolder + os.sep + classInfo1["class_name"] + "_as_" + "negativeClass")

        currentInd = 1
        for classInfo in classesInfo:
            classResultsReader = self.csvManger.getCustomClassifierResultsReader_EnsemblePath(outputFolder, classifierId, classInfo["class_name"])
            classResultsReader.getHeader()

            classId = len(classesInfo) + 1
            while classResultsReader.hasNextRow():
                row = classResultsReader.getRow()
                ind = int(row[classId])
                if negativeClassInfo == None:
                    if ind != currentInd:
                        auxPath = classInfo["path"]
                        auxName = classesInfo[ind - 1]["class_name"]
                        shutil.copyfile(auxPath + os.sep + row[0],
                                 outputFolder + os.sep + classInfo["class_name"] + "_as_" + auxName + '/' + row[0])
                else:
                    if float(row[classId + 1]) < treshold:
                        shutil.copyfile(classInfo["path"] + os.sep + os.sep + row[0],
                                        outputFolder + os.sep + classInfo["class_name"] + "_as_" + "negativeClass" + os.sep + row[0])
                    elif ind != currentInd:
                        auxName = classesInfo[ind - 1]["class_name"]
                        shutil.copyfile(classInfo["path"] + os.sep + row[0],
                                        outputFolder + os.sep + classInfo["class_name"] + "_as_" + auxName + os.sep + row[0])

            classResultsReader.close()
            currentInd += 1

        if negativeClassInfo != None:
            negativeClassResultsReader = self.csvManger.getCustomClassifierResultsReader_EnsemblePath(outputFolder, classifierId,
                                                                                 "negative")
            negativeClassResultsReader.getHeader()
            classId = len(classesInfo) + 1
            while negativeClassResultsReader.hasNextRow():
                row = negativeClassResultsReader.getRow()
                ind = int(row[classId])
                if float(row[classId + 1]) > treshold:
                    shutil.copyfile(negativeClassInfo["path"] + os.sep + row[0],
                                    outputFolder + os.sep + "negativeClass" + "_as_" + classesInfo[ind - 1]["class_name"] + os.sep + row[0])
            negativeClassResultsReader.close()

        for classInfo1 in classesInfo:
            for classInfo2 in classesInfo:
                if classInfo1["class_name"] != classInfo2["class_name"]:
                    if len(os.listdir(outputFolder + os.sep + classInfo1["class_name"] + "_as_" + classInfo2["class_name"] + os.sep)) == 0:
                        shutil.rmtree(outputFolder + os.sep + classInfo1["class_name"] + "_as_" + classInfo2["class_name"] + os.sep)
            if negativeClassInfo != None:
                if len(os.listdir(outputFolder + os.sep + "negativeClass" + "_as_" + classInfo1["class_name"] + os.sep)) == 0:
                    shutil.rmtree(outputFolder + os.sep + "negativeClass" + "_as_" + classInfo1["class_name"] + os.sep)
                if len(os.listdir(outputFolder + os.sep + classInfo1["class_name"] + "_as_" + "negativeClass" + os.sep)) == 0:
                    shutil.rmtree(outputFolder + os.sep + classInfo1["class_name"] + "_as_" + "negativeClass" + os.sep)

    def computeMultiClassStatistics(self, classesInfo, negativeClassInfo, outputFolder, classifierId):

        csvWriter = self.csvManger.geCoincidenceMatrixWriter(outputFolder)

        classes = classesInfo

        header = ['CLASS_ID']
        for classAux in classes:
            header.append(classAux.upper() + "_COUNT")
            header.append(classAux.upper() + "_PERCENTAGE")
        csvWriter.writeHeader(header)

        for className in classes:
            classResultsReader = self.csvManger.getCustomClassifierResultsReader_EnsemblePath(outputFolder, classifierId, className)
            classResultsReader.getHeader()
            count = []
            rowData = [className.upper()]
            classId = len(classes) + 1
            for v in range(len(classes)):
                count.append(0)
            while classResultsReader.hasNextRow():
                row = classResultsReader.getRow()
                ind = int(row[classId])
                count[ind - 1] = count[ind - 1] + 1
            sumClass = sum(count)
            for classCount in count:
                rowData.append(classCount)
                rowData.append(classCount / sumClass)
            csvWriter.writeRow(rowData)
        csvWriter.close()

    def computeNegativeStatistics(self, classes, negativeClassInfo, outputFolder, classifierId):

        negative_treshold_scale = 2.5

        negativeClassResReader = self.csvManger.getCustomClassifierResultsReader_EnsemblePath(outputFolder, classifierId, "negative")
        negativeClassResReader.getHeader()

        values = []
        idMax = len(classes) + 2
        while negativeClassResReader.hasNextRow():
            row = negativeClassResReader.getRow()
            values.append(float(row[idMax]))
        negativeClassResReader.close()

        negativeStatsWriter = self.csvManger.getNegativeStatsWriter(outputFolder)

        rowData = []
        rowData.append(statistics.mean(values))
        rowData.append(statistics.stdev(values))
        rowData.append(max(values))
        negativeStatsWriter.writeRow(rowData)
        negativeStatsWriter.close()

        treshold = rowData[0] + negative_treshold_scale * rowData[1]

        stats = {"treshold": treshold}
        return stats

    def measurePerformance(self, jsonConfig, classesList):
        self.outputWriter.setNewRecord()
        self.outputWriter.writeTextOutput("Computing performance statistics ... ")
        self.outputWriter.setNewRecord()

        classes = classesList
        outputFolder = jsonConfig["output_folder"]
        classifierId = jsonConfig["classifier_id"]

        numberOfClasses = len(classes)
        negativeClassInfo = None
        if "negative_class" in jsonConfig:
            negativeClassInfo = jsonConfig["negative_class"]

        classesInfo = jsonConfig["classes"]
        classesInfo.sort(key=lambda x: x["class_name"])

        if numberOfClasses == 1:
            stats = self.computeBinaryClassifierStatistics(classes, negativeClassInfo, outputFolder, classifierId)
            self.computeNegativeStatistics(classes, negativeClassInfo, outputFolder, classifierId)
            self.computeCoincidenceMatrixWithNegative(classes, negativeClassInfo, outputFolder, classifierId, stats["eerThreshold"])
            self.createMissclassificationFolders(classesInfo, negativeClassInfo, outputFolder, classifierId, stats["eerThreshold"])
        else:
            self.computeMultiClassStatistics(classes, negativeClassInfo, outputFolder, classifierId)
            if negativeClassInfo != None:
                stats = self.computeNegativeStatistics(classes, negativeClassInfo, outputFolder, classifierId)
                self.computeCoincidenceMatrixWithNegative(classes, negativeClassInfo, outputFolder, classifierId, 0)
            self.createMissclassificationFolders(classesInfo, negativeClassInfo, outputFolder, classifierId, 0)
