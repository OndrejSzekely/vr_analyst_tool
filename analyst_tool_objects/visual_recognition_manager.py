from analyst_tool_objects import csv_manager
import datetime
import os
import simplejson
from time import sleep
from analyst_tool_objects import visual_recognition

class VisualRecognitionManager:
    def __init__(self, apiKey, apiVersion, outputWriter, filesManager):
        self.vr = visual_recognition.VisualRecognition(apiKey, apiVersion)
        self.filesManager = filesManager
        self.outputWriter = outputWriter
        self.csvManager = csv_manager.CSVManager()

    def listCustomClassifiers(self):
        self.outputWriter.printOutputSegmentDelimiter()
        self.outputWriter.writeTextOutput("Listing all custom classifiers ... ")
        classifiersList = self.vr.getCustomClassifiers()

        formatedStringLength = 25
        for classifier in classifiersList["classifiers"]:
            self.outputWriter.setNewRecord()
            self.outputWriter.writeTextOutput(classifier["name"])
            self.outputWriter.writeFormatedTextOutput(["- classifier ID:", classifier["classifier_id"]],
                                                      formatedStringLength)
            self.outputWriter.writeFormatedTextOutput(["- status:", classifier["status"]], formatedStringLength)
            self.outputWriter.writeFormatedTextOutput(["- date created:", classifier["created"]], formatedStringLength)
            self.outputWriter.writeFormatedTextOutput(["- classes:", ""], formatedStringLength)
            for clasClass in classifier["classes"]:
                self.outputWriter.writeFormatedTextOutput(["", clasClass["class"]], formatedStringLength)
            self.outputWriter.setNewRecord()

        self.outputWriter.printOutputSegmentDelimiter()

    def checkTrainingStatus(self, classifierId):

        loopContinue = True

        while loopContinue:
            sleep(7)
            _, queryAnswer = self.vr.getClassifiersDetails(classifierId=classifierId)
            if "status" in queryAnswer:
                if queryAnswer['status'] == 'failed':
                    raise Exception('TRAINING FAILED!!!! ' + simplejson.dumps(queryAnswer))
                    loopContinue = False
                if queryAnswer['status'] == 'training':
                    self.outputWriter.writeTextOutput('training ...')
                if queryAnswer['status'] == 'ready':
                    self.outputWriter.writeTextOutput('Custom classifier is trained!')
                    loopContinue = False

    def trainNewClassifier(self, jsonConfig):
        self.outputWriter.setNewRecord()
        self.outputWriter.writeTextOutput("Creating and training a new classifier ...")
        self.outputWriter.setNewRecord()
        kwargs = {}

        paths = []
        for classInfo in jsonConfig["classes"]:
            className = classInfo["class_name"]
            paths.append(classInfo["batch_paths"][0])
            kwargs[className + '_positive_examples'] = open(classInfo["batch_paths"][0], 'rb')
            del classInfo["batch_paths"][0]

        if "negative_class" in jsonConfig:
            paths.append(jsonConfig["negative_class"]["batch_paths"][0])
            kwargs['negative_examples'] = open(jsonConfig["negative_class"]["batch_paths"][0], 'rb')
            del jsonConfig["negative_class"]["batch_paths"][0]

        status, info = self.vr.createClassifier(jsonConfig["classifier_name"], kwargs)

        for file in kwargs:
            kwargs[file].close()

        if status == False:
            raise Exception(info)

        self.outputWriter.writeTextOutput("New classifier was created! ID of the classifier: " + info["classifier_id"])
        self.outputWriter.setNewRecord()

        self.outputWriter.writeTextOutput("Training status:")
        self.checkTrainingStatus(info["classifier_id"])

        for path in paths:
            os.remove(path)

        jsonConfig["classifier_id"] = info["classifier_id"]
        self.updateCustomClassifierRoutine(jsonConfig)

    def updateCustomClassifierRoutine(self, jsonConfig):

        self.outputWriter.setNewRecord()
        self.outputWriter.writeTextOutput('Updating classifier\'s classes with additional image batches:')

        if "classifier_id" not in jsonConfig:
            details = self.getClassifierDetails(classifierName=jsonConfig["classifier_name"])
            jsonConfig["classifier_id"] = details[1]["classifier_id"]

        for classInfo in jsonConfig["classes"]:
            self.outputWriter.setNewRecord()
            classImagePaths = classInfo["batch_paths"]
            className = classInfo["class_name"]
            for path in classImagePaths:
                self.outputWriter.writeTextOutput("Updating class: " + className + ':')
                path = self.filesManager.removeLastSlashInFolderPath(path)
                self.outputWriter.writeTextOutput(' batch: ' + path)
                kwargs = {}
                kwargs[className + '_positive_examples'] = open(path, 'rb')
                self.updateCustomClassifier(jsonConfig["classifier_id"], kwargs)
                os.remove(path)

        self.outputWriter.setNewRecord()
        if "negative_class" in jsonConfig:
            self.outputWriter.writeTextOutput('Updating classifier\'s negative class:')
            negativePaths = jsonConfig["negative_class"]["batch_paths"]
            for negativePath in negativePaths:
                self.outputWriter.writeTextOutput(' batch: ' + negativePath)
                negativePath = self.filesManager.removeLastSlashInFolderPath(negativePath)
                kwargs = {}
                kwargs['negative_examples'] = open(negativePath, 'rb')
                self.updateCustomClassifier(jsonConfig["classifier_id"], kwargs)
                os.remove(negativePath)

    def updateCustomClassifier(self, classifierId, kwargs):
        self.vr.updateClassifier(classifierId, kwargs)

        loopContinue = True
        self.outputWriter.writeTextOutput('  Updating status:')
        while loopContinue:
            sleep(7)
            _, queryAnswer = self.vr.getClassifiersDetails(classifierId=classifierId)
            if "status" in queryAnswer:
                if queryAnswer['status'] == 'failed':
                    self.outputWriter.writeTextOutput('   TRAINING FAILED!!!! ' + simplejson.dumps(queryAnswer))
                    loopContinue = False
                if queryAnswer['status'] == 'retraining':
                    self.outputWriter.writeTextOutput('   training ...')
                if queryAnswer['status'] == 'ready':
                    self.outputWriter.writeTextOutput('   Custom classifier was successfully updated.')
                    loopContinue = False

    def checkClassifierExistance(self, classifierName=None, classifierId=None):
        return self.vr.existsClassifier(classifierName, classifierId)

    def deleteCustomClassifier(self, jsonConfig):
        classifierId = None
        classifierName = None
        if "classifier_id" in jsonConfig:
            classifierId = jsonConfig["classifier_id"]
        if "classifier_name" in jsonConfig:
            classifierName = jsonConfig["classifier_name"]
        exists, classifierName, classifierId = self.checkClassifierExistance(classifierName=classifierName, classifierId=classifierId)
        if self.vr.deleteClassifier(classifierName, classifierId) == False:
            raise Exception("ERROR: Classifier could not be deleted.")

    def classify(self, classifierName, classifierId, file):
        return self.vr.classifyImage(classifierName, classifierId, file)

    def getBatchClassification(self, classifierId, zipFile):
        allScored = None
        scoreResult = None
        while allScored is None:
            try:
                auxFile = open(zipFile, "rb")
                scoreResult = self.classify(None, classifierId, auxFile)
                for res in scoreResult["images"]:
                    if not "classifiers" in res:
                        allScored = None
                        self.outputWriter.printWarning("Warning: Error during scoring the batch file, scoring performed again. Error: " + simplejson.dumps(res))
            except Exception:
                auxFile.close()
                pass
            return scoreResult

    def getClassifierDetails(self, classifierId = None, classifierName = None):
        return self.vr.getClassifiersDetails(classifierName=classifierName, classifierId=classifierId)

    def getClasifierId(self, classifierName):
        return self.vr.getCla

    def getClassifierClasses(self, classifierId = None, classifierName = None):
        _, info = self.vr.getClassifiersDetails(classifierName=classifierName, classifierId=classifierId)
        classes = [x['class'] for x in info["classes"]]
        classes.sort()
        return classes

    def classifyImages(self, jsonConfig):
        imagesFolder = jsonConfig["input_folder"]
        outputFolder = jsonConfig["output_folder"]

        if "classifier_id" not in jsonConfig:
            details = self.getClassifierDetails(classifierName=jsonConfig["classifier_name"])
            jsonConfig["classifier_id"] = details[1]["classifier_id"]

        classifierId = jsonConfig["classifier_id"]
        prefix = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        if "file_prefix" in jsonConfig:
            prefix = jsonConfig["file_prefix"]
        imagesFolder = self.filesManager.removeLastSlashInFolderPath(imagesFolder)
        self.outputWriter.setNewRecord()
        self.outputWriter.writeTextOutput("Classifing images from folder: " + imagesFolder)
        self.outputWriter.setNewRecord()
        imagesFolder = self.filesManager.removeLastSlashInFolderPath(imagesFolder)
        classesList = self.getClassifierClasses(classifierId=classifierId)
        self.outputWriter.writeTextOutput('Preparing images batches:')
        batchesPaths = self.filesManager.zipImagesForClassification(imagesFolder)
        self.outputWriter.setNewRecord()
        self.outputWriter.writeTextOutput('Results:')
        resultsWriter = self.csvManager.getNewcustomClassifierResultsWriter(self.outputWriter, outputFolder, classifierId,
                                                                          prefix)
        resultsWriter.writeHeader(classesList)

        for batchInd in range(len(batchesPaths)):
            classificationRes = self.getBatchClassification(classifierId, batchesPaths[batchInd])
            resultsWriter.writeResults(imagesFolder, classificationRes)
            os.remove(batchesPaths[batchInd])
        resultsWriter.close()

    def classifySelectedImages(self, jsonConfig):
        imagesList = jsonConfig["images_list"]
        imagesFolder = jsonConfig["images_folder"]
        outputFolder = jsonConfig["output_folder"]
        classifierId = jsonConfig["classifier_id"]
        prefix = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        if "file_prefix" in jsonConfig:
            prefix = jsonConfig["file_prefix"]
        imagesFolder = self.filesManager.removeLastSlashInFolderPath(imagesFolder)
        self.outputWriter.setNewRecord()
        self.outputWriter.writeTextOutput("Classifing images from folder: " + imagesFolder)
        self.outputWriter.setNewRecord()
        imagesFolder = self.filesManager.removeLastSlashInFolderPath(imagesFolder)
        classesList = self.getClassifierClasses(classifierId=classifierId)
        self.outputWriter.writeTextOutput('Preparing images batches:')
        batchesPaths = self.filesManager.zipSelectedImagesForClassification(imagesFolder, imagesList)
        self.outputWriter.setNewRecord()
        self.outputWriter.writeTextOutput('Results:')
        resultsWriter = self.csvManager.getNewcustomClassifierResultsWriter(self.outputWriter, outputFolder, classifierId,
                                                                          prefix)
        resultsWriter.writeHeader(classesList)

        for batchInd in range(len(batchesPaths)):
            classificationRes = self.getBatchClassification(classifierId, batchesPaths[batchInd])
            resultsWriter.writeResults(imagesFolder, classificationRes)
            os.remove(batchesPaths[batchInd])
        resultsWriter.close()

    def classifyImagesPerformanceMeasurement(self, jsonConfig):

        self.outputWriter.writeTextOutput("Scoring all images needed for performance measurement")

        classes = jsonConfig["classes"]
        outputFolder = jsonConfig["output_folder"]
        classifierId = jsonConfig["classifier_id"]

        for classInfo in classes:
            classPath = self.filesManager.removeLastSlashInFolderPath(classInfo["path"])
            className = classInfo["class_name"]
            jsonAux = {"input_folder": classPath,
                        "output_folder": outputFolder,
                        "classifier_id": classifierId,
                       "file_prefix": className
                       }
            self.classifyImages(jsonAux)

        if "negative_class" in jsonConfig:
            jsonAux = {"input_folder": jsonConfig["negative_class"]["path"],
                       "output_folder": outputFolder,
                       "classifier_id": classifierId,
                       "file_prefix": "negative"
                       }
            self.classifyImages(jsonAux)