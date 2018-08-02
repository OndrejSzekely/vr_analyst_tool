from analyst_tool_objects import csv_manager
from PIL import Image
import numpy
import os
import shutil
from analyst_tool_objects import tile_operator

class TileInferenceManager:

    resFolder = "scoredImage"

    def __init__(self, outputWriter, filesManager, vrManager):
        self.outputWriter = outputWriter
        self.filesManager = filesManager
        self.vrManager = vrManager
        self.csvManager = csv_manager.CSVManager()

    def getColor(self, color):
        if color == "red":
            return (255, 0, 0, 255)
        if color == "green":
            return (0, 255, 0, 255)
        if color == "blue":
            return (0, 0, 255, 255)
        if color == "fuchsia":
            return (255, 0, 255, 255)

    def checkBeginningNode(self, layers, layerIndex):
        if layerIndex == 0:
            return True
        return False

    def classifyAllTiles(self, classifierId, image):
        for scale in range(len(self.tileOperator.tilingGeneralInfo.scaleList)):
            for translation in self.tileOperator.tilingGeneralInfo.tileTranslations:
                imageFolder = self.imagesFolder + os.sep + image + os.sep + str(scale) + os.sep + translation

                path = imageFolder + os.sep + self.resFolder
                if self.filesManager.checkPath(path) == False:
                    os.mkdir(path)
                else:
                    self.filesManager.removeAllFilesInFolder(path)

                classificationJson = {"input_folder": imageFolder,
                                      "output_folder": path,
                                      "classifier_id": classifierId,
                                      "file_prefix": "all"}
                self.vrManager.classifyImages(classificationJson)

    def classifyFilteredTiles(self, classifierId, previousClassifierId, tiledImage):
        for scale in range(len(self.tileOperator.tilingGeneralInfo.scaleList)):
            for translation in self.tileOperator.tilingGeneralInfo.tileTranslations:
                imageFolder = self.imagesFolder + os.sep + tiledImage + os.sep + str(scale) + os.sep + translation

                imageList = []

                resultsReader = self.csvManager.getCustomClassifierResultsReader_EnsemblePath(imageFolder + os.sep + self.resFolder,
                                                                                              previousClassifierId, "filtered")
                resultsReader.getHeader()

                while resultsReader.hasNextRow():
                    row = resultsReader.getRow()
                    imageList.append(row[0])

                classificationJson = {"images_folder": imageFolder,
                                      "images_list": imageList,
                                      "output_folder": imageFolder + os.sep + self.resFolder,
                                      "classifier_id": classifierId,
                                      "file_prefix": "all"}

                self.vrManager.classifySelectedImages(classificationJson)

    def processResults(self, outputWriter, classifierId, parameters, classes, filter, imagesFolder, tiledImage):
        treshold = None
        colors = None
        if "threshold" in parameters:
            treshold = parameters["threshold"]
        if "colors" in parameters:
            colors = parameters["colors"]

        for scale in range(len(self.tileOperator.tilingGeneralInfo.scaleList)):
            for translation in self.tileOperator.tilingGeneralInfo.tileTranslations:
                resultsFolder = imagesFolder + os.sep + tiledImage + os.sep + str(
                    scale) + os.sep + translation + os.sep + self.resFolder + os.sep

                resultsReader = self.csvManager.getCustomClassifierResultsReader_EnsemblePath(resultsFolder, classifierId, "all")
                resultsReader.getHeader()

                filteredResultsWriter = self.csvManager.getNewcustomClassifierResultsWriter(outputWriter, resultsFolder, classifierId, "filtered")
                header = ["TILE_ID", "CLASS_ID", "SCORE"]
                if colors:
                    header.append("COLOR")
                filteredResultsWriter.pasteHeader(header)

                while resultsReader.hasNextRow():
                    row = resultsReader.getRow()
                    rowData = []
                    if float(row[-1]) >= treshold:
                        rowData.append(row[0])
                        rowData.append(row[-2])
                        rowData.append(row[-1])

                        if colors:
                            rowData.append(colors[int(row[-2]) - 1])

                        filteredResultsWriter.pasteResult(rowData)

                filteredResultsWriter.close()
                resultsReader.close()

            if filter == "maximum":
                self.keepMaximumBinary(classifierId, parameters, classes, imagesFolder, tiledImage)

    def keepMaximumBinary(self, classifierId, parameters, classes, imagesFolder, tiledImage):
        index = -1
        if "colors" in parameters:
            index = -2

        for scale in range(len(self.tileOperator.tilingGeneralInfo.scaleList)):
            for translation in self.tileOperator.tilingGeneralInfo.tileTranslations:
                maxScore = 0
                maxRow = []

                resultsFolder = imagesFolder + os.sep + tiledImage + os.sep + str(scale) + os.sep + translation + os.sep + self.resFolder + os.sep

                filteredResReader = self.csvManager.getCustomClassifierResultsReader_EnsemblePath(resultsFolder, classifierId, "filtered")
                header = filteredResReader.getHeader()

                while filteredResReader.hasNextRow():
                    row = filteredResReader.getRow()
                    if float(row[index]) > maxScore:
                        maxScore = float(row[index])
                        maxRow = row
                filteredResReader.close()

                filteredResWriter = self.csvManager.getNewcustomClassifierResultsWriter(self.outputWriter, resultsFolder,
                                                                                                  classifierId,
                                                                                                  "filtered")
                filteredResWriter.pasteHeader(header)
                filteredResWriter.pasteResult(maxRow)
                filteredResWriter.close()

    def generateMaximumMatrix(self, imagesFolder, resultFolder, classifierId):

        imageWidth = self.tileOperator.tilingGeneralInfo.imageSize[0]
        imageHeight = self.tileOperator.tilingGeneralInfo.imageSize[1]
        tileWidth = self.tileOperator.tilingGeneralInfo.tileSize[0]
        tileHeight = self.tileOperator.tilingGeneralInfo.tileSize[1]

        resultsMatrix = numpy.zeros((imageHeight, imageWidth, 4))

        for scale in range(len(self.tileOperator.tilingGeneralInfo.scaleList)):
            for translation in self.tileOperator.tilingGeneralInfo.tileTranslations:
                folder = imagesFolder + os.sep + str(scale) + os.sep + translation + os.sep + self.resFolder

                scoredFileReader = self.csvManager.getCustomClassifierResultsReader_EnsemblePath(folder, classifierId, "filtered")
                scoredFileReader.getHeader()

                translationX = 0
                translationY = 0

                if translation == "x":
                    translationX = int(tileWidth / 2)
                if translation == "y":
                    translationY = int(tileHeight / 2)
                if translation == "xy":
                    translationX = int(tileWidth / 2)
                    translationY = int(tileHeight / 2)

                tilingOperator = tile_operator.TileOperator.TilingInfo()
                tilingOperator.load(imagesFolder + os.sep + str(scale) + os.sep + translation + os.sep)

                while scoredFileReader.hasNextRow():
                    row = scoredFileReader.getRow()
                    if len(row) != 0:
                        xCo = tile_operator.TileOperator.extractXCoordinate(row[0])
                        yCo = tile_operator.TileOperator.extractYCoordinate(row[0])

                        positionX = translationX + tileWidth * xCo
                        positionY = translationY + tileHeight * yCo

                        for x in range(positionX, min(positionX + tileWidth, imageWidth)):
                            for y in range(positionY, min(positionY + tileHeight, imageHeight)):
                                score = int(float(row[-2]) * 200)
                                if score > resultsMatrix[y, x][3]:
                                    color = self.getColor(row[-1])
                                    color = (color[0], color[1], color[2], score)
                                    resultsMatrix[y, x, :] = color

                scoredFileReader.close()

        numpy.save(resultFolder + os.sep + "resultMatrix", resultsMatrix)

    def generateImage(self, imagesFolder, computationFolder, lastClassifierLayer, resultFolder):

        image = Image.open(imagesFolder + os.sep + self.filesManager.getFolderNameFromPath(
            imagesFolder) + self.tileOperator.tilingGeneralInfo.imageExtension)
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
            resultFolder + os.sep + self.tileOperator.tilingGeneralInfo.imageName + self.tileOperator.tilingGeneralInfo.imageExtension)
        image.close()

    def clearAuXFolders(self, imagesFolder):
        shutil.rmtree(imagesFolder + os.sep + "computationFolder")

        for scale in range(len(self.tileOperator.tilingGeneralInfo.scaleList)):
            for translation in self.tileOperator.tilingGeneralInfo.tileTranslations:
                shutil.rmtree(imagesFolder + os.sep + str(scale) + os.sep + translation + os.sep + "scoredImage")

    def generateImageResultFromTiledImages(self, imagesFolder, resultFolder, lastClassifierLayer):

        computationFolder = imagesFolder + os.sep + "computationFolder"

        if self.filesManager.checkPath(computationFolder) == False:
            os.mkdir(computationFolder)
        else:
            self.filesManager.removeAllFilesInFolder(computationFolder)

        self.generateMaximumMatrix(imagesFolder, computationFolder, lastClassifierLayer["classifier_id"])
        self.generateImage(imagesFolder, computationFolder, lastClassifierLayer, resultFolder)
        self.clearAuXFolders(imagesFolder)

    def classifyTiledImages(self, jsonConfig):

        for layer in jsonConfig["layers"]:
            if not "classifier_id" in layer:
                details = self.vrManager.getClassifierDetails(classifierName=layer["classifier_name"])
                layer["classifier_id"] = details[1]["classifier_id"]

        inputFolder = jsonConfig["input_folder"]
        classificationLayers = jsonConfig["layers"]
        inputFolder = self.filesManager.removeLastSlashInFolderPath(inputFolder)
        self.outputWriter.setNewRecord()
        self.outputWriter.writeTextOutput("Classifing images from folder: " + inputFolder)
        self.outputWriter.setNewRecord()

        outputFolder = jsonConfig["output_folder"]
        outputFolder = self.filesManager.removeLastSlashInFolderPath(outputFolder)
        self.imagesFolder = inputFolder

        dirAnalysis = self.filesManager.analyzeDir(inputFolder, verbose=False)
        for tiledImage in dirAnalysis["listOfFoldersWithImageTiles"]:
            self.tileOperator = tile_operator.TileOperator(self.filesManager)
            self.tileOperator.loadOperator(inputFolder + os.sep + tiledImage)
            for layerIndex in range(len(classificationLayers)):
                classifierId = classificationLayers[layerIndex]["classifier_id"]
                classesList = self.vrManager.getClassifierClasses(classifierId)

                if self.checkBeginningNode(classificationLayers, layerIndex) == True:
                    self.classifyAllTiles(classifierId, tiledImage)
                else:
                     self.classifyFilteredTiles(classifierId, classificationLayers[layerIndex-1]["classifier_id"], tiledImage)

                filter = ""
                if "filter" in classificationLayers[layerIndex]:
                    filter = classificationLayers[layerIndex]["filter"]

                self.processResults(self.outputWriter, classifierId, classificationLayers[layerIndex], classesList, filter,
                                    inputFolder,tiledImage)

            self.generateImageResultFromTiledImages(inputFolder + os.sep + tiledImage, outputFolder, classificationLayers[-1])
