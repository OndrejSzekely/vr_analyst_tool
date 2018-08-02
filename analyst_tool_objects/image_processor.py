import PIL
import os
from io import BytesIO
from PIL import Image
from analyst_tool_objects import tile_operator
import math
from analyst_tool_objects import crop_operator
import cv2
import numpy as np
import random
from distutils.dir_util import copy_tree
from tqdm import tqdm
import shutil


class ImageIterator:

    def __init__(self, imagesFolderPath, imageToProcess, filesManager):
        self.filesManager = filesManager
        self.imagesFolderPath = imagesFolderPath

        if filesManager.checkPath(imagesFolderPath + os.sep + imageToProcess) == False:
            self.tiling = False
            self.relativePath = os.sep
            self.imageExtension = self.filesManager.getExtension(imageToProcess)
            self.imageNames = imageToProcess[0:imageToProcess.rfind(self.imageExtension)]
        else:
            self.tiling = True
            self.imageTilePath = self.imagesFolderPath + os.sep + imageToProcess
            self.imageTiles = tile_operator.TileOperator(self.filesManager)
            self.imageTiles.loadOperator(imagesFolderPath + os.sep + imageToProcess)
            self.imageExtension = self.imageTiles.tilingGeneralInfo.imageExtension

    def getListOfSubImages(self):
        if self.tiling == False:
            return [self.imagesFolderPath + self.relativePath + self.imageNames + self.imageExtension]
        else:
            return self.imageTiles.getAllImages()

    def updateImageExtension(self, extension):
        self.imageExtension = extension
        if self.tiling == True:
            self.imageTiles.tilingGeneralInfo.imageExtension = extension
            self.imageTiles.tilingGeneralInfo.save(self.imageTiles.tilingGeneralInfo.loadedPath)

    def updateImageTilingStatus(self):
        self.tiling = True

    def updateMetadataInfo(self):
        if self.tiling == True:
            self.imageTiles.updateMetadata()

class ImageProcessor:

    supportedOperations = ["downsample", "convert_format", "tiling"]
    downsample_resizeScale = 0.92
    MAX_VR_IMAGE_SIZE = 2
    supportedImageFormats = ["jpeg", "png"]

    def __init__(self, outputWriter, filesManger):
        self.outputWriter = outputWriter
        self.filesManager = filesManger

    def getImageAspectRatio(self, image):
       size = image.size
       gcd = math.gcd(size[0], size[1])
       return (int(size[0]/gcd), int(size[1]/gcd))

    def downsampleImageToNetworkSize(self, image, imagePath, parameters):
        image = cv2.resize(image, (224, 224))
        cv2.imwrite(imagePath, image)
        return (True, "")

    def downsampleImage(self, image, imagePath, parameters):
        maxSize = None
        maxRes = None

        if "max_size" in parameters:
            maxSize = parameters["max_size"]
        if "max_resolution" in parameters:
            maxRes = (parameters["max_resolution"]["width"], parameters["max_resolution"]["height"])

        if maxSize == None and maxRes == None:
            return (False, "ERROR: No parameter set for image downsample!")

        imageSize = os.path.getsize(imagePath) / (1024.0 * 1024.0)

        if maxSize != None and  imageSize > maxSize:
            extension = self.filesManager.normalizeExtension(self.filesManager.getExtension(imagePath))
            while imageSize > maxSize:
                bytesFile = BytesIO()
                temp = list(image.size)
                temp[0] = int(round(temp[0] * self.downsample_resizeScale))
                temp[1] = int(round(temp[1] * self.downsample_resizeScale))
                image.thumbnail(temp, Image.LANCZOS)
                image.save(bytesFile, extension)
                imageSize = bytesFile.tell() / (1024.0 * 1024.0)

        if maxRes != None and ( maxRes[0] < image.width or maxRes[1] < image.height ):
            extension = self.filesManager.normalizeExtension(self.filesManager.getExtension(imagePath))
            while maxRes[0] < image.width or maxRes[1] < image.height:
                bytesFile = BytesIO()
                temp = list(image.size)
                temp[0] = int(round(temp[0] * self.downsample_resizeScale))
                temp[1] = int(round(temp[1] * self.downsample_resizeScale))
                image.thumbnail(temp, Image.LANCZOS)
                image.save(bytesFile, extension)
                imageSize = bytesFile.tell() / (1024.0 * 1024.0)

        return (True, "")

    def convertFormat(self, image, parameters):
        if "format" not in parameters:
            return ("", False, "ERROR: Required key \"format\" is not set!")

        image.format = self.filesManager.normalizeExtension(parameters["format"])
        return (parameters["format"], True, "")

    def imageTiling(self, image, imagePath, imageName, extension, parameters):
        tileOperator = tile_operator.TileOperator(self.filesManager)
        tileOperator.create(image, imagePath, imageName, extension, parameters)

        return (True, "")

    def imageCropping(self, image, imagePath, imageName, extension, parameters):
        cropOperator = crop_operator.CropOperator()
        cropOperator.create(image, imagePath, imageName, extension, parameters, self.filesManager)

        return (True, "")

    def AugmentationRotation(self, image, imagePath, imageName, extension, parameters):
        rotationStep = parameters["angle_step"]
        cropp_center = parameters["cropp_center"]
        samples_num = parameters["samples_num"]
        minAngle = parameters["min_angle"]

        width, height = image.size
        if cropp_center > 0:
            left = (width - cropp_center) / 2;
            upper = (height - cropp_center) / 2;
            right = left + cropp_center;
            down = upper + cropp_center;

        if samples_num == 0:
            if rotationStep == 90:
                image.rotate(0).save(imagePath + os.sep + imageName + "_" + str(0) + extension)
                image.transpose(Image.ROTATE_90).save(imagePath + os.sep + imageName + "_" + str(90) + extension)
                image.transpose(Image.ROTATE_180).save(imagePath + os.sep + imageName + "_" + str(180) + extension)
                image.transpose(Image.ROTATE_270).save(imagePath + os.sep + imageName + "_" + str(270) + extension)
            else:
                numberOfRotations = int(360 / rotationStep)
                for rotateIteration in range(1, numberOfRotations + 1):
                    rotatedImage = image.rotate(rotateIteration * rotationStep, PIL.Image.BILINEAR)
                    if cropp_center > 0:
                        rotatedImage = rotatedImage.crop((left, upper, right, down))
                    rotatedImage.save(imagePath + os.sep + imageName + "_" + str(rotateIteration * rotationStep) + extension)
        else:
            getOrientation = lambda x: -1 if x == 0 else 1
            for index in range(0, samples_num):
                orientation = getOrientation(random.getrandbits(1))
                angle = 0
                while (angle < minAngle):
                    angle = random.randint(0, rotationStep)
                rotatedImage = image.rotate(orientation * angle, PIL.Image.BILINEAR)
                if cropp_center > 0:
                    rotatedImage = rotatedImage.crop((left, upper, right, down))
                rotatedImage.save(
                    imagePath + os.sep + imageName + "_rotated_" + str(orientation * angle) + extension)

        return True, ""

    def AugmentationTranslation(self, image, imagePath, imageName, extension, parameters):
        max_translation = parameters["max_translation"]
        min_translation = parameters["min_translation"]
        num_of_images = parameters["num_of_images"]
        cropp_center = parameters["cropp_center"]

        getOrientation = lambda x: -1 if x == 0 else 1
        width, height, channels = image.shape
        if cropp_center > 0:
            left = int((width - cropp_center) / 2);
            upper = int((height - cropp_center) / 2);

        for translationIndex in range(1, num_of_images + 1):
            xOrientation = getOrientation(random.getrandbits(1))
            yOrientation = getOrientation(random.getrandbits(1))
            transitionX = random.randint(min_translation, max_translation)
            transitionY = random.randint(min_translation, max_translation)
            M = np.float32([[1, 0, xOrientation * transitionX], [0, 1, yOrientation * transitionY]])
            translatedImage = cv2.warpAffine(image, M, (height,width))
            if cropp_center > 0:
                translatedImage = translatedImage[left:left+cropp_center, upper:upper+cropp_center]
            cv2.imwrite(imagePath + os.sep + imageName + "_" + "translation_" + "_" + str(translationIndex) + extension, translatedImage)

        return True, ""

    def processImagesRoutine(self, jsonConfig):
        processingTasks = jsonConfig["processing_tasks"]
        inputFolder = jsonConfig["input_folder"]
        #outputfolder = jsonConfig["output_folder"]
        imagesFolderPath = self.filesManager.removeLastSlashInFolderPath(inputFolder)
        #imagesOutputFolderPath = self.filesManager.removeLastSlashInFolderPath(outputfolder)
        imagesOutputFolderPath = imagesFolderPath
        status = self.filesManager.checkPath(imagesFolderPath)
        if status == False:
            raise Exception("ERROR: Images folder does not exist.")

        status = self.filesManager.checkPath(imagesOutputFolderPath)
        if status == False:
            raise Exception("ERROR: Images output folder does not exist.")

        #copy_tree(imagesFolderPath, imagesOutputFolderPath)

        dirAnalysis = self.filesManager.analyzeDir(imagesOutputFolderPath)

        imagesToProcess = dirAnalysis["listOfRecognizedImages"] + dirAnalysis["listOfFoldersWithImageTiles"] + \
                          dirAnalysis["listOfFoldersWithImageCrops"]
        numberOfImagesToProcess = len(imagesToProcess)

        self.outputWriter.setNewRecord()
        self.outputWriter.writeTextOutput("Performing images processing ...")

        for index in range(len(imagesToProcess)):
            percentage = index / numberOfImagesToProcess * 100
            self.outputWriter.setNewRecord()
            self.outputWriter.writeTextOutput("Already processed " + "{0:.4f}".format(percentage) + " % images.")
            self.outputWriter.writeTextOutput("Processing image: " + imagesToProcess[index] + " ...")
            status = True

            imageIterator = ImageIterator(imagesOutputFolderPath, imagesToProcess[index], self.filesManager)
            for imageProcessingTask in processingTasks:
                listOfImagesToProcess = imageIterator.getListOfSubImages()

                for image in listOfImagesToProcess:
                    openedImage = Image.open(image)
                    extension = imageIterator.imageExtension
                    imageNameWithoutExtension = self.filesManager.getFileFromPath(image)
                    if "downsample" in imageProcessingTask:
                        self.outputWriter.writeTextOutput("- Downsampling image ...")
                        status, message = self.downsampleImage(openedImage, image, imageProcessingTask["downsample"])
                        if status == False:
                            self.riseError(message)
                        else:
                            openedImage.save(image)
                            imageIterator.updateMetadataInfo()
                            openedImage.close()

                    if "downsampleImageToNetworkSize" in imageProcessingTask:
                        self.outputWriter.writeTextOutput("- Downsampling image tp NN input size...")
                        openedImage.close()
                        openedImage = cv2.imread(image)
                        status, message = self.downsampleImageToNetworkSize(openedImage, image, imageProcessingTask["downsampleImageToNetworkSize"])
                        if status == False:
                            self.riseError(message)
                        else:
                            imageIterator.updateMetadataInfo()

                    if "convert_format" in imageProcessingTask:
                        self.outputWriter.writeTextOutput("- Converting image ...")
                        extension, status, message = self.convertFormat(openedImage, imageProcessingTask["convert_format"])
                        if status == False:
                            self.riseError(message)
                        else:
                            imageIterator.updateImageExtension(extension)
                            if extension != self.filesManager.getExtension(image):
                                self.filesManager.deleteFile(image)
                            openedImage.save(image[0:image.rfind(self.filesManager.getExtension(image))] + extension)
                            openedImage.close()

                    if "standardize_file_names" in imageProcessingTask:
                        self.outputWriter.writeTextOutput("- Renaming image ...")
                        openedImage.save(imagesOutputFolderPath + os.sep + "renamed_" + str(index) + extension)
                        openedImage.close()
                        self.filesManager.deleteFile(image)

                    if "tiling" in imageProcessingTask:
                        self.outputWriter.writeTextOutput("- Cropping images into tiles ...")
                        status, message = self.imageTiling(openedImage, imagesOutputFolderPath, imageNameWithoutExtension, extension, imageProcessingTask["tiling"])
                        if status == False:
                            self.riseError(message)
                        else:
                            imageIterator.updateImageTilingStatus()
                            openedImage.close()
                            self.filesManager.deleteFile(image)

                    if "cropping" in imageProcessingTask:
                        self.outputWriter.writeTextOutput("- Cropping parts of the image ...")
                        status, message = self.imageCropping(openedImage, imagesFolderPath, imageNameWithoutExtension, extension, imageProcessingTask["cropping"])
                        if status == False:
                            self.riseError(message)
                        else:
                            imageIterator.updateImageTilingStatus()
                            openedImage.close()
                            self.filesManager.deleteFile(image)

                    if "augmentation_rotation" in imageProcessingTask:
                        self.outputWriter.writeTextOutput("- Augmenting images with rotation ...")
                        status, message = self.AugmentationRotation(openedImage, imagesFolderPath,
                                                                          imageNameWithoutExtension, extension,
                                                                          imageProcessingTask["augmentation_rotation"])
                        if status == False:
                            self.riseError(message)
                        else:
                            self.filesManager.deleteFile(image)

                    if "augmentation_translation" in imageProcessingTask:
                        openedImage.close()
                        openedImage = cv2.imread(image)
                        self.outputWriter.writeTextOutput("- Augmenting images with translation ...")
                        status, message = self.AugmentationTranslation(openedImage, imagesFolderPath,
                                                                          imageNameWithoutExtension, extension,
                                                                          imageProcessingTask["augmentation_translation"])
                        if status == False:
                            self.riseError(message)

        self.outputWriter.setNewRecord()
        self.outputWriter.writeTextOutput("Processing of images is completed!")

    def generateNegativeImagesTiles(self, jsonConfig):
        imagesFolder = jsonConfig["input_folder"]
        outputFolder = jsonConfig["output_folder"]
        imagesFolder = self.filesManager.removeLastSlashInFolderPath(imagesFolder)
        outputFolder = self.filesManager.removeLastSlashInFolderPath(outputFolder)

        status = self.filesManager.checkPath(imagesFolder)
        if status == False:
            raise Exception("ERROR: Given path to images folder is not folder!")

        status = self.filesManager.checkPath(outputFolder)
        if status == False:
            raise Exception("ERROR: Given path to output folder is not folder!")

        self.outputWriter.writeTextOutput("Processing generating negative image samples ... ")

        copy_tree(imagesFolder, outputFolder)
        jsonConf = {
            "input_folder": outputFolder,
            "processing_tasks": [{"tiling": jsonConfig["tiling_conf"]}]
        }

        self.processImagesRoutine(jsonConf)

        dirAnalysis = self.filesManager.analyzeDir(outputFolder, verbose=False)

        imageIndex = 0

        self.outputWriter.setNewRecord()
        self.outputWriter.writeTextOutput("Moving images tiles into output folder:")
        for image in dirAnalysis["listOfFoldersWithImageTiles"]:
            tileOperator = tile_operator.TileOperator(self.filesManager)
            tileOperator.loadOperator(outputFolder + os.sep + image)
            tilesList = tileOperator.getAllImages()
            for tile in tilesList:
                shutil.move(tile,
                            outputFolder + os.sep + str(imageIndex) + tileOperator.tilingGeneralInfo.imageExtension)
                imageIndex = imageIndex + 1
            shutil.rmtree(outputFolder + os.sep + image)

