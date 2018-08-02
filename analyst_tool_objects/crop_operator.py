import os
import shutil
import pickle


class CropOperator:

    class CroppingInfo:

        def __init__(self):
            self.positionX = 0
            self.positionY = 0
            self.width = 0
            self.height = 0

        def create(self, positionX, positionY, width, height):
            self.positionX = positionX
            self.positionY = positionY
            self.width = width
            self.height = height

        def save(self, path):
            outputFileCroppingInfo = open(path + os.sep + 'croppingInfo.pkl', 'wb')
            pickle.dump(self.__dict__, outputFileCroppingInfo, pickle.HIGHEST_PROTOCOL)
            outputFileCroppingInfo.close()

        def load(self, path):
            filePath = path + os.sep + 'croppingInfo.pkl'
            inputFile = open(filePath, 'rb')
            metaDataAux = pickle.load(inputFile)
            inputFile.close()
            self.__dict__.update(metaDataAux)

    class CroppingGeneralInfo:

        def create(self, listOfCropNames, imageSize, imageExtension, imageName):
            self.listOfCropNames = listOfCropNames
            self.imageExtension = imageExtension
            self.imageName = imageName
            self.loadedPath = ""
            self.imageSize = imageSize

        def __init__(self):
            self.listOfCropNames = []
            self.imageExtension = ""
            self.imageName = ""
            self.loadedPath = ""
            self.imageSize = (0,0)

        def save(self, path):
            outputFileTilingInfo = open(path + os.sep + 'croppingGeneralInfo.pkl', 'wb')
            pickle.dump(self.__dict__, outputFileTilingInfo, pickle.HIGHEST_PROTOCOL)
            outputFileTilingInfo.close()

        def load(self, path):
            filePath = path + os.sep + 'croppingGeneralInfo.pkl'
            inputFile = open(filePath, 'rb')
            metaDataAux = pickle.load(inputFile)
            inputFile.close()
            self.__dict__.update(metaDataAux)
            self.loadedPath = path

    def __init__(self):
        self.croppingGeneralInfo = CropOperator.CroppingGeneralInfo()

    def create(self, image, imagePath, imageName, extension, parameters, filesManager):
        self.imageName = imageName
        self.extension = extension
        self.cropFolder = imagePath + os.sep + imageName

        if filesManager.checkPath(self.cropFolder) == True:
            shutil.rmtree(self.cropFolder)
        os.mkdir(self.cropFolder)

        imageWidth = image.width
        imageHeight = image.height

        crops = parameters["crops"]
        listOfCropNames = []
        for crop in crops:
            particularCropFolder = self.cropFolder + os.sep + crop["name"]
            os.mkdir(particularCropFolder)

            positionX = crop["position"][0]
            positionY = crop["position"][1]
            width = crop["position"][2]
            height = crop["position"][3]

            box = (positionX, positionY, positionX + width, positionY + height)
            tile = image.crop(box)
            tile.save(particularCropFolder + os.sep + crop["name"] + extension)

            croppingInfo = CropOperator.CroppingInfo()
            croppingInfo.create(positionX, positionY, width, height)
            croppingInfo.save(particularCropFolder)

            listOfCropNames.append(crop["name"])

        imageSize = (imageWidth, imageHeight)
        croppingGeneralInfo = CropOperator.CroppingGeneralInfo()
        croppingGeneralInfo.create(listOfCropNames, imageSize, self.extension, self.imageName)
        croppingGeneralInfo.save(self.cropFolder)
        image.save(self.cropFolder + os.sep + imageName + extension)

    def loadOperator(self, imagePath):
        self.croppingGeneralInfo = CropOperator.CroppingGeneralInfo()
        self.croppingGeneralInfo.load(imagePath)

    def getAllImages(self):
        images = []
        for name in self.croppingGeneralInfo.listOfCropNames:
            croppingInfo = CropOperator.CroppingInfo()
            croppingInfo.load(self.croppingGeneralInfo.loadedPath + os.sep  + name)
            images.append(self.croppingGeneralInfo.loadedPath + os.sep + name + os.sep + name + os.sep + self.tilingGeneralInfo.imageExtension)

        return images

    def updateMetadata(self):
        #TODO
        foo = "foo"




