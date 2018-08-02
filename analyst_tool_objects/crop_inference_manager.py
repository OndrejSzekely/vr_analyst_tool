from analyst_tool_objects import crop_operator
from analyst_tool_objects import csv_manager
from PIL import Image
import numpy
import os
import shutil

class CropInferenceManager:

    def __init__(self, outputWriter, filesManager, vrManager):
        self.outputWriter = outputWriter
        self.filesManager = filesManager
        self.vrManager = vrManager
        self.csvManager = csv_manager.CSVManager()

    def classifyCrops(self, classifierId, crops, imagesFolder, outputFolder):
        for crop in crops:
            imageFolder = imagesFolder + os.sep + self.cropOperator.croppingGeneralInfo.imageName + os.sep + crop

            if self.filesManager.checkPath(imageFolder + os.sep + "scoredImage") == False:
                os.mkdir(imageFolder + os.sep + "scoredImage")
            else:
                #self.filesManager.removeAllFilesInFolder(imageFolder + os.sep + "scoredImage")
                foo = 7


        jsonConfig = {"input_folder": imageFolder,
                      "output_folder": imageFolder + os.sep + "scoredImage",
                      "classifier_id": classifierId,
                      "file_prefix": ""}
        self.vrManager.classifyImages(jsonConfig)

    def getColor(self, color):
        if color == "red":
            return (255, 0, 0, 255)
        if color == "green":
            return (0, 255, 0, 255)
        if color == "blue":
            return (0, 0, 255, 255)
        if color == "fuchsia":
            return (255, 0, 255, 255)

    def processResults(self, classifierId, parameters, imagesFolder, filter):
        #FILTER HAS NO FUNCTION YET, COULD BE LEVERAGED IN FUTURE
        threshold = None
        colors = None
        if "threshold" in parameters:
            threshold = parameters["threshold"]
        if "colors" in parameters:
            colors = parameters["colors"]

        for crop in parameters["crops"]:
            resultsFolder = imagesFolder + os.sep + crop + os.sep + "scoredImage" + os.sep

            resultsCsvReader = self.csvManager.getCustomClassifierResultsReader_EnsemblePath(resultsFolder, classifierId, "")
            resultsCsvReader.getHeader()

            filteredResultsWriter = self.csvManager.getNewcustomClassifierResultsWriter(self.outputWriter, resultsFolder,
                                                                                        classifierId, "filtered")
            header = ["TILE_ID", "CLASS_ID", "SCORE"]
            if colors:
                header.append("COLOR")
            filteredResultsWriter.pasteHeader(header)

            while resultsCsvReader.hasNextRow():
                row = resultsCsvReader.getRow()
                rowData = []
                if float(row[-1]) >= threshold:
                    rowData.append(row[0])
                    rowData.append(row[-2])
                    rowData.append(row[-1])

                    if colors:
                        rowData.append(colors[int(row[-2]) - 1])

                    filteredResultsWriter.pasteResult(rowData)

            filteredResultsWriter.close()
            resultsCsvReader.close()

    def generateImage(self, imagesFolder, computationFolder, layers, resultFolder):

        image = Image.open(imagesFolder + os.sep + self.filesManager.getFolderNameFromPath(
            imagesFolder) + self.cropOperator.croppingGeneralInfo.imageExtension)
        resultMatrix = numpy.load(computationFolder + os.sep + "resultMatrix.npy")
        maskImage = Image.new('RGBA', (resultMatrix.shape[1], resultMatrix.shape[0]), (0, 0, 0, 0))
        maskImagePixels = maskImage.load()

        for x in range(resultMatrix.shape[1]):
            for y in range(resultMatrix.shape[0]):
                maskImagePixels[x, y] = (
                int(resultMatrix[y, x, 0]), int(resultMatrix[y, x, 1]), int(resultMatrix[y, x, 2]),
                int(resultMatrix[y, x, 3]))

        rgbaImage = image.convert("RGBA")
        mixedImage = Image.alpha_composite(rgbaImage, maskImage)
        mixedImage.save(
            resultFolder + os.sep + self.cropOperator.croppingGeneralInfo.imageName + self.cropOperator.croppingGeneralInfo.imageExtension)
        image.close()

    def generateMaximumMatrix(self, imagesFolder, resultFolder, layers):

        imageWidth = self.cropOperator.croppingGeneralInfo.imageSize[0]
        imageHeight = self.cropOperator.croppingGeneralInfo.imageSize[1]

        resultsMatrix = numpy.zeros((imageHeight, imageWidth, 4))

        for layer in layers:
            for crop in layer["crops"]:


                scoredFileReader = self.csvManager.getCustomClassifierResultsReader_EnsemblePath(imagesFolder + os.sep + crop + os.sep + "scoredImage",
                                                                                                 layer["classifier_id"], "filtered")
                scoredFileReader.getHeader()

                croppingOperator = crop_operator.CropOperator.CroppingInfo()
                croppingOperator.load(imagesFolder + os.sep + crop + os.sep)

                while scoredFileReader.hasNextRow():
                    row = scoredFileReader.getRow()
                    positionX = croppingOperator.positionX
                    positionY = croppingOperator.positionY

                    for x in range(positionX, min(positionX + croppingOperator.width, imageWidth)):
                        for y in range(positionY, min(positionY + croppingOperator.height, imageHeight)):
                            score = int(float(row[-2]) * 200)
                            if score > resultsMatrix[y, x][3]:
                                color = self.getColor(row[-1])
                                color = (color[0], color[1], color[2], score)
                                resultsMatrix[y, x, :] = color

                scoredFileReader.close()

        numpy.save(resultFolder + os.sep + "resultMatrix", resultsMatrix)

    def clearAuXFolders(self, imagesFolder):
        shutil.rmtree(imagesFolder + os.sep + "computationFolder")

        croppingOperator = crop_operator.CropOperator.CroppingGeneralInfo()
        croppingOperator.load(imagesFolder + os.sep)

        for crop in croppingOperator.listOfCropNames:
            shutil.rmtree(imagesFolder + os.sep + crop + os.sep + "scoredImage")

    def generateImageResultFromCroppedImages(self, imagesFolder, resultFolder, layers):

        computationFolder = imagesFolder + os.sep + "computationFolder"

        if self.filesManager.checkPath(computationFolder) == False:
            os.mkdir(computationFolder)
        else:
            self.filesManager.removeAllFilesInFolder(computationFolder)

        self.generateMaximumMatrix(imagesFolder, computationFolder, layers)
        self.generateImage(imagesFolder, computationFolder, layers, resultFolder)
        self.clearAuXFolders(imagesFolder)

    def classifyCroppedImages(self, jsonConfig):

        for layer in jsonConfig["layers"]:
            if not "classifier_id" in layer:
                details = self.vrManager.getClassifierDetails(classifierName=layer["classifier_name"])
                layer["classifier_id"] = details[1]["classifier_id"]

        imagesFolder = jsonConfig["input_folder"]
        outputFolder = jsonConfig["output_folder"]
        classifiersLayers = jsonConfig["layers"]
        self.outputWriter.setNewRecord()
        self.outputWriter.writeTextOutput(
            "Classifing images from folder: " + self.filesManager.getFolderNameFromPath(imagesFolder))
        self.outputWriter.setNewRecord()

        imagesFolder = self.filesManager.removeLastSlashInFolderPath(imagesFolder)
        resultFolder = self.filesManager.removeLastSlashInFolderPath(outputFolder)

        dirAnalysis = self.filesManager.analyzeDir(imagesFolder, verbose=False)
        for croppedImage in dirAnalysis["listOfFoldersWithImageCrops"]:
            self.cropOperator = crop_operator.CropOperator()
            self.cropOperator.loadOperator(imagesFolder + os.sep + croppedImage)
            for layerIndex in range(len(classifiersLayers)):
                classifierId = classifiersLayers[layerIndex]["classifier_id"]
                cropsInfo = classifiersLayers[layerIndex]["crops"]
                classesList = self.vrManager.getClassifierClasses(classifierId=classifierId)
                self.classifyCrops(classifierId, cropsInfo, imagesFolder, resultFolder)

                filter = ""
                if "filter" in classifiersLayers[layerIndex]:
                    filter = classifiersLayers[layerIndex]["filter"]

                self.processResults(classifierId, classifiersLayers[layerIndex], imagesFolder + os.sep + croppedImage, filter)

            self.generateImageResultFromCroppedImages(imagesFolder + os.sep + croppedImage, resultFolder,
                                                      classifiersLayers)