from analyst_tool_objects import crop_inference_manager
from analyst_tool_objects import files_manager
from analyst_tool_objects import images_downloader
from analyst_tool_objects import image_processor
import json
import os
from output_writer import output_writer
import pickle
import shutil
from analyst_tool_objects import statistics_manager
import sys
from analyst_tool_objects import tiling_inference_manager
import traceback
from analyst_tool_objects import recursive_classifier
from analyst_tool_objects import visual_recognition_manager

class AnalystTool:
    analystToolFolderVariable = 'VRAnalystToolFolder'
    analystToolFilesystemObject = "analystTool.json"
    analystToolSetupInfo = None
    urlChecker = None

    def __init__(self, setupAnalystToolObj = None, outputWriterType = "console"):
        try:
            if outputWriterType == "console":
                self.outputWriter = output_writer.OutputWriter("console")
            if outputWriterType == "file":
                self.outputWriter = output_writer.OutputWriter("file")
            self.outputWriter.printOutputSegmentDelimiter()
            self.outputWriter.writeTextOutput("Setting VR Analyst Tool ...")
            if (setupAnalystToolObj == None):
                self.loadAnalystToolObject()
            else:
                self.analystToolSetupInfo = setupAnalystToolObj
            self.filesManager = files_manager.FilesManager(self.outputWriter)
            self.imagesDownloader = images_downloader.ImagesDownloader(self.outputWriter, self.filesManager)
            self.statisticsManager = statistics_manager.StatisticsManager(self.outputWriter, self.filesManager)
            self.imageProcessor = image_processor.ImageProcessor(self.outputWriter, self.filesManager)
            self.vrManager = visual_recognition_manager.VisualRecognitionManager(self.analystToolSetupInfo["api_key"],
                                                           self.analystToolSetupInfo["api_version"],
                                                           self.outputWriter, self.filesManager)
            self.tileInferenceManager = tiling_inference_manager.TileInferenceManager(self.outputWriter,
                                                                                      self.filesManager, self.vrManager)
            self.cropInferenceManager = crop_inference_manager.CropInferenceManager(self.outputWriter, self.filesManager,
                                                                                    self.vrManager)
            self.recursiveClassifier = recursive_classifier.RecursiveClassifier(self.outputWriter, self.filesManager,
                                                                                    self.vrManager)
            self.outputWriter.writeTextOutput("VR Analyst Tool was successfully set.")
            if (setupAnalystToolObj != None):
                self.setupAnalystToolFolder()
                self.saveAnalystToolObject()
            self.outputWriter.printOutputSegmentDelimiter()
        except Exception:
            self.outputWriter.printErrorText("ERROR: \n" + traceback.format_exc())
            self.outputWriter.writeTextOutput("ANALYST TOOL WAS NOT SET UP! PLEASE CHECK THE ERROR AND REPEAT THE ACTION!")
            self.outputWriter.printOutputSegmentDelimiter()
            sys.exit(1)
        except KeyboardInterrupt:
            self.outputWriter.riseError("ERROR: PROGRAM WAS INTERRUPTED!")

    def setupAnalystToolFolder(self):
        metaDataFolderPath = self.getAnalystToolFolderPath()
        if os.path.exists(metaDataFolderPath):
            shutil.rmtree(metaDataFolderPath)
        os.mkdir(metaDataFolderPath)

    def getAnalystToolFolderPath(self):
        metaDataFolderPath = os.getcwd() + os.sep + self.analystToolFolderVariable
        return metaDataFolderPath

    def loadAnalystToolObject(self):
        objectPath = self.getAnalystToolFolderPath() + os.sep + self.analystToolFilesystemObject
        try:
            objectFile = open(objectPath, "r")
            loadedObject = json.load(objectFile)
            objectFile.close()
            self.analystToolSetupInfo = loadedObject
        except IOError:
            self.outputWriter.printErrorText("ERROR: CAN NOT OPEN \"" + self.analystToolFilesystemObject +
                                             "\" FILE. Detailed error: " + IOError)
            sys.exit(1)
        except pickle.PickleError:
            self.outputWriter.printErrorText("ERROR: CAN NOT LOAD OBJECT FROM \"" + self.analystToolFilesystemObject +
                                             "\" FILE. Detailed error: " + pickle.PickleError)
            sys.exit(1)

    def checkAnalystToolSetupInfo(self):
        if ("api_key" not in self.analystToolSetupInfo):
            raise Exception("Missing key \"api_key\" in analyst tool setup info.")
        if ("api_version" not in self.analystToolSetupInfo):
            raise Exception("Missing key \"api_version\" in analyst tool setup info.")

    def saveAnalystToolObject(self):
        self.checkAnalystToolSetupInfo()
        metaDataFolderPath = self.getAnalystToolFolderPath()
        outputFile = open(metaDataFolderPath + os.sep + self.analystToolFilesystemObject, 'w')
        json.dump(self.analystToolSetupInfo, outputFile)
        outputFile.close()

    def listClassifiers(self):
        try:
            self.outputWriter.printOutputSegmentDelimiter()
            self.vrManager.listCustomClassifiers()
        except Exception:
            self.outputWriter.printErrorText("ERROR: \n" + traceback.format_exc())
            self.outputWriter.printOutputSegmentDelimiter()
            sys.exit(1)
        except KeyboardInterrupt:
            self.outputWriter.riseError("ERROR: PROGRAM WAS INTERRUPTED!")

    def setsCreation(self, jsonConfig):
        try:
            self.outputWriter.printOutputSegmentDelimiter()
            if ("output_path" not in jsonConfig):
                raise Exception("Missing key \"output_path\" in conf file.")
            if ("negative_class" not in jsonConfig) and (len(jsonConfig["classes"]) == 1):
                raise Exception("\"classes\" array has to contain at least 2 classes or one class and \"negative_class\" class key")
            self.filesManager.createDatasetForCustomClassifier(jsonConfig)
            self.outputWriter.printOutputSegmentDelimiter()
        except Exception:
            self.outputWriter.printErrorText("ERROR: \n" + traceback.format_exc())
            self.outputWriter.printOutputSegmentDelimiter()
            sys.exit(1)
        except KeyboardInterrupt:
            self.outputWriter.riseError("ERROR: PROGRAM WAS INTERRUPTED!")

    def trainClassifier(self, jsonConfig):
        try:
            self.outputWriter.printOutputSegmentDelimiter()
            if ("classifier_id" not in jsonConfig and "classifier_name" not in jsonConfig):
                raise Exception("\"classifier_id\" or \"classifier_name\" has to be set")
            if ("negative_class" not in jsonConfig) and (len(jsonConfig["classes"]) == 1):
                raise Exception("\"classes\" array has to contain at least 2 classes or one class and \"negative_class\" class key")

            jsonConfigEnriched = self.filesManager.prepareZipBatchesForCustomClassifierTraining(jsonConfig)
            self.vrManager.trainNewClassifier(jsonConfigEnriched)
            self.outputWriter.printOutputSegmentDelimiter()
        except Exception:
            self.outputWriter.printErrorText("ERROR: \n" + traceback.format_exc())
            self.outputWriter.printOutputSegmentDelimiter()
            sys.exit(1)
        except KeyboardInterrupt:
            self.outputWriter.riseError("ERROR: PROGRAM WAS INTERRUPTED!")

    def updateClassifier(self, jsonConfig):
        try:
            self.outputWriter.printOutputSegmentDelimiter()
            if ("classifier_id" not in jsonConfig and "classifier_name" not in jsonConfig):
                raise Exception("\"classifier_id\" or \"classifier_name\" has to be set")
            jsonConfigEnriched = self.filesManager.prepareZipBatchesForCustomClassifierTraining(jsonConfig)
            self.vrManager.updateCustomClassifierRoutine(jsonConfigEnriched)
            self.outputWriter.printOutputSegmentDelimiter()
        except Exception:
            self.outputWriter.printErrorText("ERROR: \n" + traceback.format_exc())
            self.outputWriter.printOutputSegmentDelimiter()
            sys.exit(1)
        except KeyboardInterrupt:
            self.outputWriter.riseError("ERROR: PROGRAM WAS INTERRUPTED!")

    def deleteClassifier(self, jsonConfig):
        try:
            self.outputWriter.printOutputSegmentDelimiter()
            if ("classifier_id" not in jsonConfig and "classifier_name" not in jsonConfig):
                raise Exception("\"classifier_id\" or \"classifier_name\" has to be set")
            self.outputWriter.writeTextOutput("Deleting VR classifier ... ")
            self.vrManager.deleteCustomClassifier(jsonConfig)
            self.outputWriter.writeTextOutput("Classifier was succesfully deleted!")
            self.outputWriter.printOutputSegmentDelimiter()
        except Exception:
            self.outputWriter.printErrorText("ERROR: \n" + traceback.format_exc())
            self.outputWriter.printOutputSegmentDelimiter()
            sys.exit(1)
        except KeyboardInterrupt:
            self.outputWriter.riseError("ERROR: PROGRAM WAS INTERRUPTED!")

    def classifyImages(self, jsonConfig):
        try:
            self.outputWriter.printOutputSegmentDelimiter()
            if ("input_folder" not in jsonConfig):
                raise Exception("\"input_folder\" has to be set")
            if ("output_folder" not in jsonConfig):
                raise Exception("\"output_folder\" has to be set")
            if ("classifier_id" not in jsonConfig and "classifier_name" not in jsonConfig):
                raise Exception("\"classifier_id\" or \"classifier_name\" has to be set")
            self.vrManager.classifyImages(jsonConfig)
            self.outputWriter.printOutputSegmentDelimiter()
        except Exception:
            self.outputWriter.printErrorText("ERROR: \n" + traceback.format_exc())
            self.outputWriter.printOutputSegmentDelimiter()
            sys.exit(1)
        except KeyboardInterrupt:
            self.outputWriter.riseError("ERROR: PROGRAM WAS INTERRUPTED!")

    def checkDirectory(self, jsonConfig):
        try:
            self.outputWriter.printOutputSegmentDelimiter()
            self.filesManager.analyzeDir(jsonConfig["path"], True)
            self.outputWriter.printOutputSegmentDelimiter()
        except Exception:
            self.outputWriter.printErrorText("ERROR: \n" + traceback.format_exc())
            self.outputWriter.printOutputSegmentDelimiter()
            sys.exit(1)
        except KeyboardInterrupt:
            self.outputWriter.riseError("ERROR: PROGRAM WAS INTERRUPTED!")

    def downloadImages(self, jsonConfig):
        try:
            self.outputWriter.printOutputSegmentDelimiter()
            if ("output_folder" not in jsonConfig):
                raise Exception("\"output_folder\" has to be set")
            if ("url_file_path" not in jsonConfig):
                raise Exception("\"url_file_path\" has to be set")
            if ("new_start" not in jsonConfig):
                raise Exception("\"new_start\" has to be set")
            if ("image_prefix" not in jsonConfig):
                raise Exception("\"image_prefix\" has to be set")
            self.imagesDownloader.downloadImages(jsonConfig)
            self.outputWriter.printOutputSegmentDelimiter()
        except Exception:
            self.outputWriter.printErrorText("ERROR: \n" + traceback.format_exc())
            self.outputWriter.printOutputSegmentDelimiter()
            sys.exit(1)
        except KeyboardInterrupt:
            self.outputWriter.riseError("ERROR: PROGRAM WAS INTERRUPTED!")

    def sortImagesBasedOnClassification(self, jsonConfig):
        try:
            self.outputWriter.printOutputSegmentDelimiter()
            if "scored_images_csv" not in jsonConfig and ("file_prefix" not in jsonConfig and "csv_path" not in jsonConfig
            and "classifier_name" not in jsonConfig):
                raise Exception("\"scored_images_csv\" has to be set or \"file_prefix\" and \"csv_path\" and \"classifier_name\" has to be set")
            if ("output_folder" not in jsonConfig):
                raise Exception("\"output_folder\" has to be set")
            if ("images_folder" not in jsonConfig):
                raise Exception("\"images_folder\" has to be set")
            if ("threshold" not in jsonConfig):
                raise Exception("\"threshold\" has to be set")
            if not "scored_images_csv" in jsonConfig:
                classifierInfo = self.vrManager.getClassifierDetails(classifierName=jsonConfig["classifier_name"])
                jsonConfig["classifier_id"] = classifierInfo[1]["classifier_id"]
            self.statisticsManager.sortClassifiedImages(jsonConfig)
            self.outputWriter.printOutputSegmentDelimiter()
        except Exception:
            self.outputWriter.printErrorText("ERROR: \n" + traceback.format_exc())
            self.outputWriter.printOutputSegmentDelimiter()
            sys.exit(1)
        except KeyboardInterrupt:
            self.outputWriter.riseError("ERROR: PROGRAM WAS INTERRUPTED!")

    def measurePerformance(self, jsonConfig):
        try:
            self.outputWriter.printOutputSegmentDelimiter()
            if ("negative_class" not in jsonConfig) and (len(jsonConfig["classes"]) == 1):
                raise Exception(
                    "\"classes\" array has to contain at least 2 classes or one class and \"negative_class\" class key")
            if ("classifier_id" not in jsonConfig and "classifier_name" not in jsonConfig):
                raise Exception("\"classifier_id\" or \"classifier_name\" has to be set")
            if ("output_folder" not in jsonConfig):
                raise Exception("\"output_folder\" has to be set")
            if("classifier_id"  not in jsonConfig):
                details = self.vrManager.getClassifierDetails(classifierName=jsonConfig["classifier_name"])
                jsonConfig["classifier_id"] = details[1]["classifier_id"]
            self.vrManager.classifyImagesPerformanceMeasurement(jsonConfig)
            classesList = self.vrManager.getClassifierClasses(jsonConfig["classifier_id"])
            self.statisticsManager.measurePerformance(jsonConfig, classesList)
            self.outputWriter.printOutputSegmentDelimiter()
        except Exception:
            self.outputWriter.printErrorText("ERROR: \n" + traceback.format_exc())
            self.outputWriter.printOutputSegmentDelimiter()
            sys.exit(1)
        except KeyboardInterrupt:
            self.outputWriter.riseError("ERROR: PROGRAM WAS INTERRUPTED!")

    def processImages(self, jsonConfig):
        try:
            self.outputWriter.printOutputSegmentDelimiter()
            if ("input_folder" not in jsonConfig):
                raise Exception("\"input_folder\" has to be set")
            if ("processing_tasks" not in jsonConfig):
                raise Exception("\"processing_tasks\" has to be set")
            self.imageProcessor.processImagesRoutine(jsonConfig)
            self.outputWriter.printOutputSegmentDelimiter()
        except Exception:
            self.outputWriter.printErrorText("ERROR: \n" + traceback.format_exc())
            self.outputWriter.printOutputSegmentDelimiter()
            sys.exit(1)
        except KeyboardInterrupt:
            self.outputWriter.riseError("ERROR: PROGRAM WAS INTERRUPTED!")

    def generateNegativeImagesTiles(self, jsonConfig):
        try:
            if ("input_folder" not in jsonConfig):
                raise Exception("\"input_folder\" has to be set")
            if ("output_folder" not in jsonConfig):
                raise Exception("\"output_folder\" has to be set")
            if ("tiling_conf" not in jsonConfig):
                raise Exception("\"tiling_conf\" has to be set")
            self.outputWriter.printOutputSegmentDelimiter()
            self.imageProcessor.generateNegativeImagesTiles(jsonConfig)
            self.outputWriter.printOutputSegmentDelimiter()
        except Exception:
            self.outputWriter.printErrorText("ERROR: \n" + traceback.format_exc())
            self.outputWriter.printOutputSegmentDelimiter()
            sys.exit(1)
        except KeyboardInterrupt:
            self.outputWriter.riseError("ERROR: PROGRAM WAS INTERRUPTED!")

    def classifyTiledImages(self, jsonConfig):
        try:
            self.outputWriter.printOutputSegmentDelimiter()
            self.tileInferenceManager.classifyTiledImages(jsonConfig)
            self.outputWriter.printOutputSegmentDelimiter()
        except Exception:
            self.outputWriter.printErrorText("ERROR: \n" + traceback.format_exc())
            self.outputWriter.printOutputSegmentDelimiter()
            sys.exit(1)
        except KeyboardInterrupt:
            self.outputWriter.riseError("ERROR: PROGRAM WAS INTERRUPTED!")

    def classifyCroppedImages(self, jsonConfig):
        try:
            self.outputWriter.printOutputSegmentDelimiter()
            self.cropInferenceManager.classifyCroppedImages(jsonConfig)
            self.outputWriter.printOutputSegmentDelimiter()
        except Exception:
            self.outputWriter.printErrorText("ERROR: \n" + traceback.format_exc())
            self.outputWriter.printOutputSegmentDelimiter()
            sys.exit(1)
        except KeyboardInterrupt:
            self.outputWriter.riseError("ERROR: PROGRAM WAS INTERRUPTED!")


    def recursiveClassifier(self, jsonConfig):
        try:
            self.outputWriter.printOutputSegmentDelimiter()
            self.cropInferenceManager.classifyImages(jsonConfig)
            self.outputWriter.printOutputSegmentDelimiter()
        except Exception:
            self.outputWriter.printErrorText("ERROR: \n" + traceback.format_exc())
            self.outputWriter.printOutputSegmentDelimiter()
            sys.exit(1)
        except KeyboardInterrupt:
            self.outputWriter.riseError("ERROR: PROGRAM WAS INTERRUPTED!")

    # def newMethod(self, jsonConfig):
    #     try:
    #         ####VALIDATION IF KEYS ARE PRESENTED IN JSON
    #         if ("KEY" not in jsonConfig):
    #           raise Exception("\"KEY\" has to be set")
    #         self.outputWriter.printOutputSegmentDelimiter()
    #         self.particularOperator.particularMethod(jsonConfig)
    #         self.outputWriter.printOutputSegmentDelimiter()
    #     except Exception:
    #         self.outputWriter.printErrorText("ERROR: \n" + traceback.format_exc())
    #         self.outputWriter.printOutputSegmentDelimiter()
    #         sys.exit(1)
    #     except KeyboardInterrupt:
    #         self.outputWriter.riseError("ERROR: PROGRAM WAS INTERRUPTED!")