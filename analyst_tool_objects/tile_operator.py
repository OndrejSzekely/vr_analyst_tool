import os
import shutil
import math
import pickle
import PIL
import copy

class TileOperator:

    def extractXCoordinate (imageName):
        underline = imageName.rfind("_") + 1
        dot = imageName.rfind(".")
        x = imageName[underline:dot]
        return int(x)

    def extractYCoordinate (imageName):
        underline = imageName.rfind("_")
        y = imageName[0:underline]
        return int(y)

    class TilingInfo:

        def __init__(self):
            self.rows = 0
            self.columns = 0
            self.xMargin = 0
            self.yMargin = 0

        def create(self, numberOfRows, numberOfColumns):
            self.rows = numberOfRows
            self.columns = numberOfColumns

        def save(self, path):
            outputFileTilingInfo = open(path + os.sep + 'tilingInfo.pkl', 'wb')
            pickle.dump(self.__dict__, outputFileTilingInfo, pickle.HIGHEST_PROTOCOL)
            outputFileTilingInfo.close()

        def load(self, path):
            filePath = path + os.sep + 'tilingInfo.pkl'
            inputFile = open(filePath, 'rb')
            metaDataAux = pickle.load(inputFile)
            inputFile.close()
            self.__dict__.update(metaDataAux)

    class TilingGeneralInfo:

        def create(self, tileSize, imageSize, maxVariability, numOfSteps, tileTranslations, imageExtension, imageName, scaleList):
            self.maxVariability = maxVariability
            self.numOfSteps = numOfSteps
            self.tileTranslations = tileTranslations
            self.imageExtension = imageExtension
            self.imageName = imageName
            self.scaleList = scaleList
            self.loadedPath = ""
            self.imageSize = imageSize
            self.tileSize = tileSize

        def __init__(self):
            self.maxVariability = 0
            self.numOfSteps = 0
            self.tileTranslations = []
            self.imageExtension = ""
            self.imageName = ""
            self.scaleList = []
            self.loadedPath = ""
            self.imageSize = (0,0)
            self.tileSize = (0,0)

        def save(self, path):
            outputFileTilingInfo = open(path + os.sep + 'tilingGeneralInfo.pkl', 'wb')
            pickle.dump(self.__dict__, outputFileTilingInfo, pickle.HIGHEST_PROTOCOL)
            outputFileTilingInfo.close()

        def load(self, path):
            filePath = path + os.sep + 'tilingGeneralInfo.pkl'
            inputFile = open(filePath, 'rb')
            metaDataAux = pickle.load(inputFile)
            inputFile.close()
            self.__dict__.update(metaDataAux)
            self.loadedPath = path


    #TILE VARIABILITY STEP IN PERCENTAGE
    tileVariabilityStep = 10

    def __init__(self, filesManager):
        self.filesManager = filesManager
        self.tilingGeneralInfo = TileOperator.TilingGeneralInfo()

    def create(self, image, imagePath, imageName, extension, parameters):
        self.imageName = imageName
        self.extension = extension
        self.tileFolder = imagePath + os.sep + imageName

        if self.filesManager.checkPath(self.tileFolder) == True:
            shutil.rmtree(self.tileFolder)
        os.mkdir(self.tileFolder)

        imageWidth = image.width
        imageHeight = image.height
        refTileWidth = parameters["reference_image_tile"]["width"]
        refTileHeight = parameters["reference_image_tile"]["height"]

        if "tile_variability" in parameters:
            maxVariability = parameters["tile_variability"] * 100
            numOfSteps = maxVariability / self.tileVariabilityStep + math.ceil((maxVariability % self.tileVariabilityStep) / self.tileVariabilityStep)
            numOfSteps = int(2 * numOfSteps) + 1
            self.scaleList = []
            for step in range(numOfSteps):
                self.scaleList.append(min(-maxVariability + step * self.tileVariabilityStep, maxVariability) / 100 )
        else:
            self.scaleList = [0]
            maxVariability = 0
            numOfSteps = 1

        if "tile_translations" in parameters:
            self.tileTranslations = copy.deepcopy(parameters["tile_translations"])
            self.tileTranslations.append("none")
        else:
            self.tileTranslations = ["none"]

        for scale in self.scaleList:
            scaleFolder = self.tileFolder + os.sep + str(self.scaleList.index(scale))
            os.mkdir(scaleFolder)

            for tileTranslation in self.tileTranslations:
                translationFolder = scaleFolder + os.sep + tileTranslation
                os.mkdir(translationFolder)

                tileWidth = int(refTileWidth * (1 + scale))
                tileHeight = int(refTileHeight * (1 + scale))

                auxImageWidth = imageWidth
                auxImageHeight = imageHeight

                xMargin = 0
                yMargin = 0

                if tileTranslation == "x":
                    auxImageWidth = auxImageWidth - int(tileWidth / 2)
                    xMargin = int(tileWidth / 2)
                if tileTranslation == "y":
                    auxImageHeight = auxImageHeight - int(tileHeight / 2)
                    yMargin = int(tileWidth / 2)
                if tileTranslation == "xy":
                    auxImageHeight = auxImageHeight - int(tileHeight / 2)
                    auxImageWidth = auxImageWidth - int(tileWidth / 2)
                    xMargin = int(tileWidth / 2)
                    yMargin = int(tileWidth / 2)

                numberOfXTiles = int(auxImageWidth / tileWidth) + math.ceil(
                    (auxImageWidth % tileWidth) / tileWidth)
                numberOfYTiles = int(auxImageHeight / tileHeight) + math.ceil(
                    (auxImageHeight % tileHeight) / tileHeight)

                for row in range(numberOfYTiles):
                    for column in range(numberOfXTiles):
                        leftUpper = (min(column * tileWidth + xMargin, imageWidth - 1), min(row * tileHeight + yMargin, imageHeight - 1))
                        rightLower = (min((column + 1) * tileWidth + xMargin, imageWidth - 1),min((row + 1) * tileHeight + yMargin, imageHeight - 1))
                        box = (leftUpper[0], leftUpper[1], rightLower[0], rightLower[1])
                        tile = image.crop(box)
                        tile.save(translationFolder + os.sep + str(row) + "_" + str(column) + extension)

                tilingInfo = TileOperator.TilingInfo()
                tilingInfo.create(numberOfYTiles, numberOfXTiles)
                tilingInfo.save(translationFolder)

            tileSize = (tileWidth, tileHeight)
            imageSize = (imageWidth, imageHeight)
            tilingGeneralInfo = TileOperator.TilingGeneralInfo()
            tilingGeneralInfo.create(tileSize, imageSize, maxVariability, numOfSteps, self.tileTranslations, self.extension, self.imageName, self.scaleList)
            tilingGeneralInfo.save(self.tileFolder)
            image.save(self.tileFolder + os.sep + imageName + extension)

    def loadOperator(self, imagePath):
        self.tilingGeneralInfo = TileOperator.TilingGeneralInfo()
        self.tilingGeneralInfo.load(imagePath)

    def getAllImages(self):
        images = []
        for scaleIndex in range(len(self.tilingGeneralInfo.scaleList)):
            for translation in self.tilingGeneralInfo.tileTranslations:
                tilingInfo = TileOperator.TilingInfo()
                tilingInfo.load(self.tilingGeneralInfo.loadedPath + os.sep + str(scaleIndex) + os.sep + str(translation))
                for row in range(tilingInfo.rows):
                    for column in range(tilingInfo.columns):
                        images.append(self.tilingGeneralInfo.loadedPath + os.sep + str(scaleIndex) + os.sep + str(translation) + os.sep +
                                      str(row) + "_" + str(column) + self.tilingGeneralInfo.imageExtension)

        return images

    def updateMetadata(self):
        auxImage = PIL.Image.open(self.tilingGeneralInfo.loadedPath + os.sep + str(self.tilingGeneralInfo.scaleList[0]) + os.sep +
                       self.tilingGeneralInfo.tileTranslations[0] + os.sep + "0_0" + self.tilingGeneralInfo.imageExtension)

        newHeight = auxImage.height
        newWidth = auxImage.width

        scaleX = newWidth / self.tilingGeneralInfo.tileSize[0]
        scaleY = newHeight / self.tilingGeneralInfo.tileSize[1]

        self.tilingGeneralInfo.tileSize = (newWidth, newHeight)
        self.tilingGeneralInfo.imageSize = (int(self.tilingGeneralInfo.imageSize[0]*scaleX), int(self.tilingGeneralInfo.imageSize[1]*scaleY))




