from io import BytesIO
import cv2
import io
from PIL import Image
import math
import numpy as np
import os
from io import StringIO
import zipfile

class RecursiveClassifierProtocolOperator:

    def __init__(self, path):
        self.protocolFile = open(path, 'w')

    def close(self):
        self.protocolFile.close()

    def writeInfo(self, info):
        self.protocolFile.write(info)

class RecursiveClassifier:

    def __init__(self, outputWriter, filesManager, vrManager):
        self.outputWriter = outputWriter
        self.filesManager = filesManager
        self.vrManager = vrManager

    def checkImageDivStopCrit(self, subimages, actualLayer):
        res = 1

        if "stop_criterion" in actualLayer["image_division"]:
            crit = actualLayer["image_division"]["stop_criterion"]
            if "min_res" in crit:
                if crit["min_res"][0] > subimages[0]["position"][2] or crit["min_res"][1] > \
                        subimages[0]["position"][3]:
                    res = 0

        return res

    def generateSubimages(self, subimage, imageDivisionType):
        # cv2.imwrite("/Users/ondra/Desktop/subimage.png", subimage["subimage"])

        subimages = []
        if imageDivisionType["type"] == "none":
            subimages.append(subimage)
            return subimages
        if imageDivisionType["type"] == "halves":
            imageRes = (subimage["position"][2], subimage["position"][3])
            widthBlock = int(imageRes[0] / 2)
            heightBlock = int(imageRes[1] / 2)

            for i in range(2):
                for j in range(2):
                    origin = (
                        j * widthBlock + subimage["position"][0], i * heightBlock + subimage["position"][1])
                    originSubImage = (j * widthBlock, i * heightBlock)
                    # window = (min(originSubImage[0] + widthBlock, imageRes[0]), min(originSubImage[1] + heightBlock, imageRes[1]))
                    # window = (window[0] - originSubImage[0], window[1] - originSubImage[1])
                    window = (widthBlock, heightBlock)
                    subimages.append({"subimage": subimage["subimage"][
                                                  originSubImage[1]:originSubImage[1] + window[1],
                                                  originSubImage[0]:originSubImage[0] + window[0]],
                                      "position": (origin[0], origin[1], window[0], window[1])})
                    j += 1
                i += 1
            return subimages

    def handleColor(self, color):
        if color == "red":
            return (0, 0, 255)
        if color == "green":
            return (0, 255, 0)
        if color == "blue":
            return (255, 0, 0)
        if color == "fuchsia":
            return (255, 0, 255)
        if color == "orange":
            return (0, 165, 255)
        return (0, 0, 0)

    def classifyImages(self, jsonConfig):

        for layer in jsonConfig["layers"]:
            if not "classifier_ids" in layer:
                classifierNames = []
                for classifierName in layer["classifier_names"]:
                    details = self.vrManager.getClassifierDetails(classifierName=classifierName)
                    classifierNames.append(details[1]["classifier_id"])
                layer["classifier_ids"] = classifierNames

        imagesFolder = jsonConfig["input_folder"]
        outputFolder = jsonConfig["output_folder"]
        classifiersLayers = jsonConfig["layers"]

        self.outputWriter.setNewRecord()
        self.outputWriter.writeTextOutput(
            "Recursive classification of images from folder: " + self.filesManager.getFolderNameFromPath(imagesFolder))
        self.outputWriter.setNewRecord()

        imagesFolder = self.filesManager.removeLastSlashInFolderPath(imagesFolder)
        dirAnalysis = self.filesManager.analyzeDir(imagesFolder, verbose=False)

        for image in dirAnalysis["listOfRecognizedImages"]:
            inputImage = cv2.imread(os.path.join(imagesFolder, image))
            self.protocolOperator = RecursiveClassifierProtocolOperator(os.path.join(outputFolder, image + ".txt"))
            self.outputWriter.writeTextOutput("Classifing image " + image)
            initialChainBreakStatus = []
            previousRes = []
            numOfClassifiers = len(classifiersLayers[0]["classifier_ids"])
            for i in range(numOfClassifiers):
                initialChainBreakStatus.append(False)
                previousRes.append(0.0)
            outputImage = self.classifyLayer(inputImage, {"subimage": np.copy(inputImage), "position": (
                0, 0, inputImage.shape[1], inputImage.shape[0])}, 0, classifiersLayers,
                                              initialChainBreakStatus, previousRes, '')
            self.protocolOperator.close()
            cv2.imwrite(os.path.join(outputFolder, image), outputImage)

    def resolveSubImageClassifications(self, classifiersResults, results_processing, previousResults):
        numOfClassifiers = len(classifiersResults)

        # check criterion
        criterionStatus = []
        if "minimal_thresholds" in results_processing["pass"]["criterion"]:
            thresholds = results_processing["pass"]["criterion"]["minimal_thresholds"]
            for index in range(numOfClassifiers):
                if classifiersResults[index] >= thresholds[index]:
                    criterionStatus.append(True)
                else:
                    criterionStatus.append(False)

        if "keep_growing" in results_processing["pass"]["criterion"]:
            for index in range(numOfClassifiers):
                # eps = (1.0 - 1.0 / (1.0 + math.exp(-5.0 * classifiersResults[index]))) / 10.0
                eps = 0.2 * math.exp(-6.0 * classifiersResults[index])
                #eps = 0
                if previousResults[index] + eps <= classifiersResults[index]:
                    criterionStatus.append(True)
                else:
                    criterionStatus.append(False)

        # handle classifiers - pass
        handleResults = []
        for index in range(numOfClassifiers):
            handleResults.append(0)

        if results_processing["pass"]["handle_classifiers"] == "all":
            for index in range(numOfClassifiers):
                if criterionStatus[index] == True:
                    handleResults[index] = 1
        if results_processing["pass"]["handle_classifiers"] == "max":
            sortedIndices = np.argsort(classifiersResults)
            for index in range(numOfClassifiers-1, -1, -1):
                if criterionStatus[sortedIndices[index]] == True:
                    handleResults[index] = 1
                    break

        # handle classifiers - fail
        if results_processing["fail"]["handle_classifiers"] == "all":
            for index in range(numOfClassifiers):
                if criterionStatus[index] == False:
                    handleResults[index] = -1
        if results_processing["fail"]["handle_classifiers"] == "min":
            sortedIndices = np.argsort(classifiersResults)
            for index in range(numOfClassifiers):
                if criterionStatus[sortedIndices[index]] == False:
                    handleResults[index] = -1
                    break

        return handleResults

    def handleSubImages(self, subimagesResults, actualLayer):
        # handle pass subimages
        if actualLayer["pass"]["handle_tiles"] == "all":
            foo = 0

        # handle fail subimages
        if actualLayer["fail"]["handle_tiles"] == "all":
            return subimagesResults

    def generateChainPassStatuses(self, layerIndex, doLayerIndex, classifierLayers, chainPassStatuses):
        if layerIndex == doLayerIndex:
            return chainPassStatuses
        else:
            numOfClassifiers = len(classifierLayers[doLayerIndex]["classifier_ids"])
            res = []
            for i in range(numOfClassifiers):
                res.append(False)
            return res

    def generatePreviousLayerResults(self, layerIndex, doLayerIndex, classifierLayers, actualScores):
        if layerIndex == doLayerIndex:
            return actualScores
        else:
            numOfClassifiers = len(classifierLayers[doLayerIndex]["classifier_ids"])
            res = []
            for i in range(numOfClassifiers):
                res.append(0.0)
            return res

    def classifyLayer(self, drawingImage, subimage, layerIndex, classifierLayers, chainPassStatuses,
                            previousResults, metafilePrefix):

        # cv2.imwrite("/Users/ondra/Desktop/img.jpg", subimage["subimage"])

        actualLayer = classifierLayers[layerIndex]
        imageDivisionType = actualLayer["image_division"]
        subimages = self.generateSubimages(subimage, imageDivisionType)
        subimNum = len(subimages)
        classifiers = classifierLayers[layerIndex]["classifier_ids"]
        classifiersNum = len(classifiers)

        keepDividing = self.checkImageDivStopCrit(subimages, actualLayer)

        if keepDividing == 1:

            self.outputWriter.writeTextOutput(str(subimage["position"]))
            self.outputWriter.writeTextOutput("layer " + str(layerIndex))
            self.outputWriter.setNewRecord()

            results = []
            scores = []
            scoresMax = []
            scoresMin = []
            bytesZip = io.BytesIO()
            batchZip = zipfile.ZipFile(bytesZip, 'w', zipfile.ZIP_DEFLATED)
            ind = 0
            for subimg in subimages:
                bytesFile = io.BytesIO()
                b, g, r = cv2.split(subimg["subimage"])
                Image.fromarray(cv2.merge([r, g, b])).save(bytesFile, format='PNG')
                bytesFile.name = "img" + str(ind)
                bytesFile.seek(0)
                batchZip.writestr(str(ind) + ".png", bytesFile.getvalue())
                ind += 1
            for subimg_ind in range(len(subimages)):
                scores.append([])
            for classifier in classifiers:
                bytesZip.name = "images.zip"
                batchZip.close()

                scoreStatus = None
                while scoreStatus is None:
                    bytesZip.seek(0)
                    claificationRes = self.vrManager.vr.classifyImage(None, classifier, bytesZip)
                    scoreStatus = "ok"
                    for res in claificationRes["images"]:
                        if not "classifiers" in res:
                            scoreStatus = None

                for subimg_ind in range(len(subimages)):
                    score = 0;
                    for resRecord in claificationRes['images']:
                        score = resRecord['classifiers'][0]['classes'][0]["score"];
                        imgInd = int(resRecord['image'][11]);
                        if imgInd == subimg_ind:
                            break;

                    scores[subimg_ind].append(score)

            for subimg_ind in range(len(subimages)):
                scoreSlice = scores[subimg_ind]
                maxScore = 0
                minScore = math.inf
                results.append(self.resolveSubImageClassifications(scoreSlice, actualLayer["results_processing"],
                                                              previousResults))
                for obtainedScore_ind in range(len(scoreSlice)):
                    if scoreSlice[obtainedScore_ind] > maxScore and results[subimg_ind][obtainedScore_ind] == 1:
                        maxScore = scoreSlice[obtainedScore_ind]
                    if scoreSlice[obtainedScore_ind] < minScore and results[subimg_ind][obtainedScore_ind] == 1:
                        minScore = scoreSlice[obtainedScore_ind]
                scoresMax.append(maxScore)
                scoresMin.append(minScore)
            results = self.handleSubImages(results, actualLayer["results_processing"])

            # DO OUTPUT PASS
            for class_ind in range(classifiersNum):
                if actualLayer["results_processing"]["pass"]["do_output"][class_ind] != -1:
                    actualDo = actualLayer["results_processing"]["pass"]["do_output"][class_ind]
                    for subim_ind in range(subimNum):
                        if results[subim_ind][class_ind] == 1:
                            if "text" in actualDo:
                                info = metafilePrefix + str(subimages[subim_ind]["position"]) + " " + actualDo[
                                    "text"] + " Score: " + str(scores[subim_ind][class_ind]) + "\n"
                                self.protocolOperator.writeInfo(info)

                            if "color" in actualDo and scoresMax[subim_ind] == scores[subim_ind][class_ind]:
                                color = self.handleColor(actualDo["color"])
                                cv2.rectangle(drawingImage, (
                                    subimages[subim_ind]["position"][0], subimages[subim_ind]["position"][1]), (
                                                  subimages[subim_ind]["position"][0] +
                                                  subimages[subim_ind]["position"][2],
                                                  subimages[subim_ind]["position"][1] +
                                                  subimages[subim_ind]["position"][3]), color, 3)

            # DO OUTPUT FAIL
            for class_ind in range(classifiersNum):
                if actualLayer["results_processing"]["fail"]["do_output"][class_ind] != -1:
                    actualDo = actualLayer["results_processing"]["fail"]["do_output"][class_ind]
                    for subim_ind in range(subimNum):
                        if results[subim_ind][class_ind] == -1:
                            if "text" in actualDo:
                                info = metafilePrefix + str(subimages[subim_ind]["position"]) + actualDo[
                                    "text"] + "\t Score: " + str(scores[subim_ind][class_ind]) + "\n"
                                self.protocolOperator.writeInfo(info)
                            if "color" in actualDo and scoresMin[subim_ind] == scores[subim_ind][class_ind]:
                                color = self.handleColor(actualDo["color"])
                                cv2.rectangle(drawingImage, (
                                    subimages[subim_ind]["position"][0], subimages[subim_ind]["position"][1]), (
                                                  subimages[subim_ind]["position"][0] +
                                                  subimages[subim_ind]["position"][2],
                                                  subimages[subim_ind]["position"][1] +
                                                  subimages[subim_ind]["position"][3]), color, 3)

            # CHECK CHAIN PASS BREAK
            if "do_layer_on_chain_break" in actualLayer["results_processing"]["pass"]["criterion"]:
                for class_ind in range(classifiersNum):

                    resultsPassAny = 0
                    for ind in range(len(subimages)):
                        if results[ind][class_ind] == 1:
                            resultsPassAny = 1
                            break

                    if chainPassStatuses[class_ind] == True and (keepDividing + resultsPassAny) < 2:
                        doLayerIndex = \
                            actualLayer["results_processing"]["pass"]["criterion"]["do_layer_on_chain_break"][
                                class_ind]

                        self.classifyLayer(drawingImage, subimage, doLayerIndex, classifierLayers,
                                            self.generateChainPassStatuses(layerIndex, doLayerIndex,
                                                                      classifierLayers, chainPassStatuses),
                                            self.generatePreviousLayerResults(layerIndex, doLayerIndex,
                                                                         classifierLayers, previousResults),
                                            metafilePrefix + "\t")

            # DO LAYER PASS
            for class_ind in range(classifiersNum):
                if actualLayer["results_processing"]["pass"]["do_layer"][class_ind] != -1:
                    actualDo = actualLayer["results_processing"]["pass"]["do_layer"][class_ind]
                    for subim_ind in range(subimNum):
                        if results[subim_ind][class_ind] == 1:
                            passVar = True
                            if keepDividing == 0:
                                passVar = False
                            if passVar == True:
                                statuses = []
                                for i in range(len(classifierLayers[actualDo]["classifier_ids"])):
                                    statuses.append(True)
                                self.classifyLayer(drawingImage, subimages[subim_ind], actualDo,
                                                    classifierLayers, statuses,
                                                    self.generatePreviousLayerResults(layerIndex, actualDo,
                                                                                 classifierLayers,
                                                                                 scores[subim_ind]),
                                                    metafilePrefix + "\t")

            # DO LAYER FAIL
            for class_ind in range(classifiersNum):
                if actualLayer["results_processing"]["fail"]["do_layer"][class_ind] != -1:
                    actualDo = actualLayer["results_processing"]["fail"]["do_layer"][class_ind]
                    for subim_ind in range(subimNum):
                        if results[subim_ind][class_ind] == -1:
                            passVar = True
                            if keepDividing == 0:
                                passVar = False
                            if passVar == True:
                                statuses = []
                                for i in range(len(classifierLayers[actualDo]["classifier_ids"])):
                                    statuses.append(False)
                                self.classifyLayer(drawingImage, subimages[subim_ind], actualDo,
                                                    classifierLayers, statuses,
                                                    self.generatePreviousLayerResults(layerIndex, actualDo,
                                                                                 classifierLayers,
                                                                                 scores[subim_ind]),
                                                    metafilePrefix + "\t")

        else:
            # CHECK CHAIN PASS BREAK
            if "do_layer_on_chain_break" in actualLayer["results_processing"]["pass"]["criterion"]:
                for class_ind in range(classifiersNum):

                    if chainPassStatuses[class_ind] == True:
                        doLayerIndex = \
                            actualLayer["results_processing"]["pass"]["criterion"]["do_layer_on_chain_break"][
                                class_ind]
                        self.classifyLayer(drawingImage, subimage, doLayerIndex,
                                            classifierLayers,
                                            self.generateChainPassStatuses(layerIndex, doLayerIndex,
                                                                      classifierLayers,
                                                                      chainPassStatuses),
                                            self.generatePreviousLayerResults(layerIndex, doLayerIndex,
                                                                         classifierLayers,
                                                                         previousResults),
                                            metafilePrefix + "\t")

        return drawingImage