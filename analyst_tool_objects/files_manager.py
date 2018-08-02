from PIL import Image
import math
import os
import pickle
import re
import random
import shutil
from tqdm import tqdm
from analyst_tool_objects import url_checker
import zipfile

class FilesManager:

    MAX_VR_IMAGE_SIZE = 1.99
    supportedVRImageFormats = [".jpg", ".jpeg", ".png"]
    supportedVideoFormats = []
    supportedImageFormats = [".jpg", ".jpeg", ".png", ".tiff", ".tif", ".bmp"]
    maxNumOfFilesPerZip = 1000
    maxZipSize = 100
    maxZipSizeImageClassification = 9.8
    maxZipedImagesImageClassification = 10

    def __init__(self, outputWriter):
        self.outputWriter = outputWriter

    def createZipFilesFromFiles(self, path, filesPrefix, files):
        numberOfFiles = len(files)
        totalBatchFiles = 0
        totalBatchSize = 0
        fromIndex = 0
        toIndex = 0
        batchIndex = 0
        pathPrefix, folderName = self.splitPath(path)
        batchPaths = []

        for i in range(numberOfFiles):
            if totalBatchFiles + 1 <= self.maxNumOfFilesPerZip and totalBatchSize + \
                    (os.path.getsize(path + os.sep + files[i]) / (1024.0 * 1024.0)) <= self.maxZipSize \
                    and i != numberOfFiles - 1:
                toIndex = toIndex + 1
                totalBatchFiles += 1
                totalBatchSize += (
                        os.path.getsize(path + os.sep + files[i]) / (1024.0 * 1024.0))
            else:
                batchIndex = batchIndex + 1
                batchZip = zipfile.ZipFile(pathPrefix + os.sep + filesPrefix + '_train_' + str(batchIndex) + '.zip', 'w',
                                           zipfile.ZIP_DEFLATED)
                batchPaths.append(pathPrefix + os.sep + filesPrefix + '_train_' + str(batchIndex) + '.zip')
                if i == numberOfFiles - 1:
                    toIndex = toIndex + 1
                    totalBatchFiles += 1
                    totalBatchSize += (
                            os.path.getsize(path + os.sep + files[i]) / (1024.0 * 1024.0))
                for j in range(fromIndex, toIndex):
                    batchZip.write(path + os.sep + files[j], files[j])
                batchZip.close()
                self.outputWriter.writeTextOutput(
                    'Batch ' + str(batchIndex) + ':   ' + str(totalBatchFiles) + ' images    ' + str(
                        totalBatchSize) + ' MB')
                fromIndex = i
                toIndex = i + 1
                totalBatchSize = (os.path.getsize(path + os.sep + files[i]) / (1024.0 * 1024.0))
                totalBatchFiles = 1
        return batchPaths

    def removeLastSlashInFolderPath(self, path):
        pathSep = os.sep
        if pathSep == "\\":
            pathSep = "\\\\"
        return re.sub(pathSep + "$", "", path)

    def containsImageCropps(self, folderPath, verbose):
        try:
            aux = pickle.load(open(folderPath + os.sep + "croppingGeneralInfo.pkl", "rb"))
            return True
        except (OSError, IOError):
           return False

    def checkPath(self, path):
        if os.path.isdir(path) and os.path.exists(path):
            return True
        else:
            return False

    def getExtension(self, file):
        extension = file[file.rfind("."):]
        # REMOVE GET QUERY PARAMETERS FROM URL
        index = extension.rfind("?")
        if index == -1:
            index = len(extension)
        extension = extension[0:index]
        return extension

    def tryToOpenImage(self, image):
        try:
            image = Image.open(image)
            image.close()
            return True
        except IOError:
            self.outputWriter.printWarning("WARNING: Image can not be opened!")
            return False

    def checkImageFileExtension(self, imageName, verbose = True):
        return self.checkGivenExtensionOfImage(self.getExtension(imageName), verbose)

    def checkGivenExtensionOfVideo(self, extension, verbose):
        status = extension.lower() in self.supportedVideoFormats
        if status == False and verbose == True:
            self.outputWriter.printWarning("WARNING: File extension is not valid for supported video formats.")
        return status

    def checkGivenExtensionOfImage(self, extension, verbose):
        status = extension.lower() in self.supportedImageFormats
        if status == False and verbose == True:
            self.outputWriter.printWarning("WARNING: File extension is not valid for supported image formats.")
        return status

    def checkGivenExtensionOfVRImage(self, extension, verbose = True):
        status = extension.lower() in self.supportedVRImageFormats
        if status == False and verbose == True:
            self.outputWriter.printWarning("WARNING: File extension is not valid for supported VR image formats.")
        return status

    def checkVideo(self, videoPath, verbose = True):
        #TODO
        return False

    def containsImageTiles(self, folderPath, verbose):
        try:
            aux = pickle.load(open(folderPath + os.sep + "tilingGeneralInfo.pkl", "rb"))
            return True
        except (OSError, IOError):
           return False

    def checkFolderImageTiles(self, folderPath, verbose = False):
        if self.checkPath(folderPath) and ( self.containsImageTiles(folderPath, verbose)):
            return True
        else:
            return False

    def checkFolderImageCrops(self, folderPath, verbose = False):
        if self.containsImageCropps(folderPath, verbose):
            return True
        else:
            return False

    def containsVRImages(self, folderPath, verbose):
        exists = self.checkPath(folderPath)
        if exists == True:
            listOfFilesInDirectory = os.listdir(folderPath)
            for file in listOfFilesInDirectory:
                if self.checkVRImage(folderPath + os.sep + file, False):
                    return True
        return False

    def checkFolderWithVRImages(self, folderPath, verbose = True):
        if self.containsVRImages(folderPath, verbose):
            return True
        else:
            return False

    def checkVRImageFileExtension(self, imageName, verbose = True):
        return self.checkGivenExtensionOfVRImage(self.getExtension(imageName), verbose)

    def getFileSize(self, filePath):
        return os.path.getsize(filePath) / (1024.0 * 1024.0)

    def checkVRImageSize(self, imagePath, verbose = True):
        if self.getFileSize(imagePath) > self.MAX_VR_IMAGE_SIZE:
            if verbose == True:
                self.outputWriter.printWarning("WARNING: Maximum size of VR image is exceeded.")
            return False
        else:
            return True

    def checkImage(self, path, verbose = True):
        if self.checkImageFileExtension(path, verbose) == True and self.tryToOpenImage(path):
            return True
        else:
            return False

    def checkVRImage(self, imagePath, verbose = True):
        if self.checkVRImageFileExtension(imagePath, verbose) == True and self.tryToOpenImage(imagePath) and self.checkVRImageSize(imagePath, verbose):
            return True
        else:
            return False

    # RETURNS JSON {"listOfRecognizedImages", "listOfRecognizedVRImages", "listOfRecognizedVideos",
    # "listOfFoldersWithVRImages", "listOfImageTilesImages"}
    def analyzeDir(self, folderPath, verbose = False):
        if verbose == True:
            self.outputWriter.printOutputSegmentDelimiter()
            self.outputWriter.setNewRecord()
        if verbose == True:
            self.outputWriter.writeTextOutput("Analyzing given folder ...")
            folderPath = self.removeLastSlashInFolderPath(folderPath)
        if self.checkPath(folderPath) == False:
            self.outputWriter.riseError("ERROR: Given path is not folder.")
        listOfFiles = os.listdir(folderPath)
        numberOfFiles = len(listOfFiles)
        numberOfRecognizedImages = 0
        numberOfRecognizedVRImages = 0
        numberOfRecognizedVideos = 0
        numberOfFoldersWithVRImages = 0
        numberOfFoldersWithImageTiles = 0
        numberOfFoldersWithImageCrops = 0
        listOfRecognizedImages = []
        listOfRecognizedVRImages = []
        listOfRecognizedVideos = []
        listOfFoldersWithVRImages = []
        listOfFoldersWithImageTiles = []
        listOfFoldersWithImageCrops = []

        if verbose == True:
            self.outputWriter.setNewRecord()
        for file in listOfFiles:
            if verbose == True:
                self.outputWriter.writeTextOutput("Checking file \"" + file + "\" ...")
            filePath = folderPath + os.sep + file
            recognized = False
            if self.checkImage(filePath, False) == True:
                numberOfRecognizedImages = numberOfRecognizedImages + 1
                listOfRecognizedImages.append(file)
                recognized = True
            if self.checkVRImage(filePath, False) == True:
                numberOfRecognizedVRImages = numberOfRecognizedVRImages + 1
                listOfRecognizedVRImages.append(file)
                recognized = True
            if self.checkVideo(filePath, False) == True:
                numberOfRecognizedVideos = numberOfRecognizedVideos + 1
                listOfRecognizedVideos.append(file)
                recognized = True
            if self.checkFolderWithVRImages(filePath, False) == True:
                numberOfFoldersWithVRImages = numberOfFoldersWithVRImages + 1
                listOfFoldersWithVRImages.append(file)
                recognized = True
            if self.checkFolderImageTiles(filePath, False) == True:
                numberOfFoldersWithImageTiles = numberOfFoldersWithImageTiles + 1
                listOfFoldersWithImageTiles.append(file)
                recognized = True
            if self.checkFolderImageCrops(filePath, False) == True:
                numberOfFoldersWithImageCrops = numberOfFoldersWithImageCrops + 1
                listOfFoldersWithImageCrops.append(file)
                recognized = True
            if recognized == False:
                if verbose == True:
                    self.outputWriter.printWarning("WARNING: Unrecognized file.")
            if verbose == True:
                self.outputWriter.setNewRecord()

        if verbose == True:
            length = 45
            self.outputWriter.setNewRecord()
            self.outputWriter.writeTextOutput("FOLDER STATISTICS:")
            self.outputWriter.writeFormatedTextOutput([" - Number of files: ", str(numberOfFiles)], length)
            self.outputWriter.writeFormatedTextOutput([" - Number of recognized images: ", str(numberOfRecognizedImages)], length)
            self.outputWriter.writeFormatedTextOutput([" - Number of recognized VR images: ", str(numberOfRecognizedVRImages)], length)
            self.outputWriter.writeFormatedTextOutput([" - Number of recognized videos: ", str(numberOfRecognizedVideos)], length)
            self.outputWriter.writeFormatedTextOutput([" - Number of folders with VR images: ", str(numberOfFoldersWithVRImages)], length)
            self.outputWriter.writeFormatedTextOutput([" - Number of image tiles: ", str(numberOfFoldersWithImageTiles)], length)
            self.outputWriter.writeFormatedTextOutput(
                [" - Number of image crops: ", str(numberOfFoldersWithImageCrops)], length)

        return {"listOfRecognizedImages": listOfRecognizedImages, "listOfRecognizedVRImages": listOfRecognizedVRImages,
                "listOfRecognizedVideos": listOfRecognizedVideos, "listOfFoldersWithVRImages": listOfFoldersWithVRImages,
                "listOfFoldersWithImageTiles": listOfFoldersWithImageTiles, "listOfFoldersWithImageCrops": listOfFoldersWithImageCrops}

    def createDatasets(self, outputPath, configJson):
        path = configJson["path"]
        folderName = os.path.basename(os.path.normpath(path))
        percentages = configJson["percentages"]

        dirAnalysis = self.analyzeDir(path, verbose=True)

        path = self.removeLastSlashInFolderPath(path)
        status = self.checkPath(path)
        if status == False:
            raise Exception("ERROR: Path to class images folder is not valid!")

        if sum(percentages) < 0.998:
            raise Exception("ERROR: Percentages must have sum equal to 1!")

        if percentages[0] == 0:
            raise Exception("ERROR: Training percentage must be greater than 0!")


        if self.checkPath(outputPath + os.sep + folderName + os.sep + "Train") == True:
            shutil.rmtree(outputPath + os.sep + folderName + os.sep + "Train")
        os.makedirs(outputPath + os.sep + folderName + os.sep + "Train")

        if percentages[1] > 0:
            if self.checkPath(outputPath + os.sep + folderName + os.sep + "Test") == True:
                shutil.rmtree(outputPath + os.sep + folderName + os.sep + "Test")
            os.makedirs(outputPath + os.sep + folderName + os.sep + "Test")

        if percentages[2] > 0:
            if self.checkPath(outputPath + os.sep + folderName + os.sep + "Validation") == True:
                shutil.rmtree(outputPath + os.sep + folderName + os.sep + "Validation")
            os.makedirs(outputPath + os.sep + folderName + os.sep + "Validation")

        listOfVRImages = dirAnalysis["listOfRecognizedVRImages"]
        numberOfPictures = len(listOfVRImages)
        numberOfTrainingImages = int(math.floor(percentages[0] * numberOfPictures))
        numberOfTestingImages = int(math.floor(percentages[1] * numberOfPictures))
        numberOfValidationImages = int(math.floor(percentages[2] * numberOfPictures))
        random.shuffle(listOfVRImages)

        for i in range(numberOfTrainingImages):
            shutil.copy(path + os.sep + listOfVRImages[i], outputPath + os.sep + folderName + os.sep + 'Train' + os.sep + listOfVRImages[i])

        for i in range(numberOfTrainingImages, numberOfTrainingImages + numberOfTestingImages):
            shutil.copy(path + os.sep + listOfVRImages[i], outputPath + os.sep + folderName + os.sep + 'Test' + os.sep + listOfVRImages[i])

        for i in range(numberOfTrainingImages + numberOfTestingImages, numberOfTrainingImages + numberOfTestingImages + numberOfValidationImages):
            shutil.copy(path + os.sep + listOfVRImages[i], outputPath + os.sep + folderName + os.sep + 'Validation' + os.sep + listOfVRImages[i])

    def createDatasetForCustomClassifier(self, jsonConfig):
        classes = jsonConfig["classes"]
        outputPath = jsonConfig["output_path"]

        self.outputWriter.printOutputSegmentDelimiter()
        self.outputWriter.setNewRecord()
        self.outputWriter.writeTextOutput("Creating data sets for a new classifier ...")
        self.outputWriter.setNewRecord()

        self.outputWriter.writeTextOutput("Creating classes sets ...")

        for classJson in tqdm(classes):
            self.createDatasets(outputPath, classJson)

        if "negative_class" in jsonConfig:
            negativeClass = jsonConfig["negative_class"]
            self.outputWriter.setNewRecord()
            self.outputWriter.writeTextOutput("Creating negative data sets ...")
            self.createDatasets(outputPath, negativeClass)

        self.outputWriter.setNewRecord()
        self.outputWriter.writeTextOutput("All sets were created succesfully ...")

    def splitPath(self, path):
        return (os.path.split(path)[0], os.path.split(path)[1])

    def prepareZipBatchesForCustomClassifierTraining(self, jsonConfig):
        classes = jsonConfig["classes"]
        self.outputWriter.writeTextOutput("Preparing zip files...")
        self.outputWriter.setNewRecord()
        for classInfo in classes:
            self.outputWriter.writeTextOutput("Preparing zip for class " + classInfo["class_name"] + ":")
            path = self.removeLastSlashInFolderPath(classInfo["path"])
            if self.checkPath(path) == False:
                raise Exception("ERROR: Path to class images folder does not exist!")
            dirAnalysis = self.analyzeDir(path, verbose=False)
            batchPaths = self.createZipFilesFromFiles(path, classInfo["class_name"], dirAnalysis["listOfRecognizedVRImages"])
            classInfo["batch_paths"]= batchPaths
            self.outputWriter.setNewRecord()

        if "negative_class" in jsonConfig:
            self.outputWriter.writeTextOutput("Preparing zip for negative class:")
            path = self.removeLastSlashInFolderPath(jsonConfig["negative_class"]["path"])
            if self.checkPath(path) == False:
                raise Exception("ERROR: Path to negative class images folder does not exist!")
            dirAnalysis = self.analyzeDir(path, verbose=False)
            negativeBatchPaths = self.createZipFilesFromFiles(path, "negative", dirAnalysis["listOfRecognizedVRImages"])
            jsonConfig["negative_class"]["batch_paths"] = negativeBatchPaths
        return jsonConfig

    def zipImagesForClassification(self, imagesFolder):
        folderAnalysis = self.analyzeDir(imagesFolder, verbose=False)
        imagesList = folderAnalysis["listOfRecognizedVRImages"]
        numberOfPictures = len(imagesList)
        totalBatchImages = 0
        totalBatchSize = 0
        fromIndex = 0
        toIndex = 0
        batchIndex = 0
        imagesListAux = []
        batchesPaths = []
        pathPrefix,_ = self.splitPath(imagesFolder)


        for i in range(numberOfPictures):
            if totalBatchImages + 1 <= self.maxZipedImagesImageClassification and totalBatchSize + (
                    os.path.getsize(imagesFolder + os.sep + imagesList[i]) / (
                    1024.0 * 1024.0)) <= self.maxZipSizeImageClassification and i != numberOfPictures - 1:
                toIndex = toIndex + 1
                totalBatchImages = totalBatchImages + 1
                totalBatchSize = totalBatchSize + (
                        os.path.getsize(imagesFolder + os.sep + imagesList[i]) / (1024.0 * 1024.0))
                imagesListAux.append(imagesList[i])
            else:
                batchIndex = batchIndex + 1
                batchPath = pathPrefix + os.sep + 'imagesClassificationBatch_' + str(batchIndex) + '.zip'
                batchesPaths.append(batchPath)
                batchZip = zipfile.ZipFile(batchPath, 'w', zipfile.ZIP_DEFLATED)
                if i == numberOfPictures - 1:
                    toIndex = toIndex + 1
                    totalBatchImages = totalBatchImages + 1
                    totalBatchSize = totalBatchSize + (
                            os.path.getsize(imagesFolder + os.sep + imagesList[i]) / (1024.0 * 1024.0))
                    imagesListAux.append(imagesList[i])
                for j in range(fromIndex, toIndex):
                    batchZip.write(imagesFolder + os.sep + imagesList[j], imagesList[j])
                self.outputWriter.writeTextOutput('Batch ' + str(batchIndex) + ':   ' + str(totalBatchImages) + ' images    ' + str(
                    totalBatchSize) + ' MB')
                fromIndex = i
                toIndex = i + 1
                totalBatchSize = (os.path.getsize(imagesFolder + os.sep + imagesList[i]) / (1024.0 * 1024.0))
                totalBatchImages = 1
                batchZip.close()
                imagesListAux = []
                imagesListAux.append(imagesList[i])
        return batchesPaths

    def zipSelectedImagesForClassification(self, imagesFolder, imagesList):
        auxFolder = "auxFolder"
        if self.checkPath(imagesFolder + os.sep + auxFolder):
            shutil.rmtree(imagesFolder + os.sep + auxFolder)
        os.mkdir(imagesFolder + os.sep + auxFolder)
        os.mkdir(imagesFolder + os.sep + auxFolder + os.sep + auxFolder)
        for image in imagesList:
            shutil.copyfile(imagesFolder + os.sep + image, imagesFolder + os.sep + auxFolder + os.sep + auxFolder + os.sep + image)
        self.zipImagesForClassification(imagesFolder + os.sep + auxFolder + os.sep + auxFolder)
        files = os.listdir(imagesFolder + os.sep + auxFolder)
        pathPrefix, _ = self.splitPath(imagesFolder)
        zips = []
        for file in files:
            if file.endswith(".zip"):
                shutil.move(imagesFolder + os.sep + auxFolder + os.sep + file, pathPrefix + os.sep + file)
                zips.append(pathPrefix + os.sep + file)
        shutil.rmtree(imagesFolder + os.sep + auxFolder)
        return zips


    def checkFile(self, file):
        if os.path.isfile(file) and os.path.exists(file):
            return True
        else:
            return False

    def deleteFile(self, filePath):
        if self.checkFile(filePath):
            os.remove(filePath)

    def getLastOsSepPosition(self, path):
        return path.rfind(os.sep)

    def getFileFromPath(self, path):
        return path[self.getLastOsSepPosition(path) + 1:path.rfind(self.getExtension(path))]

    def normalizeExtension(self, extension):
        if extension.lower() == ".jpg" or extension.lower() == ".jpeg":
            return "JPEG"
        if extension.lower() == ".png":
            return "PNG"
        if extension.lower() == ".png":
            return "PNG"
        if extension.lower() == ".bmp":
            return "BMP"

    def removeAllFilesInFolder(self, folder):
        folder = self.removeLastSlashInFolderPath(folder)
        status = True
        try:
            shutil.rmtree(folder)
            os.mkdir(folder)
            return True
        except shutil.Error:
            status = False
            return False
        except OSError:
            status = False
            return False

    def getFolderNameFromPath(self, path):
        path = self.removeLastSlashInFolderPath(path)
        return path[self.getLastOsSepPosition(path) + 1:]




