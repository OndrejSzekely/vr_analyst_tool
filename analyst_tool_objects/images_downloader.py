import os
import pickle
from analyst_tool_objects import url_checker
import urllib
import urllib.parse
import urllib.request

class ImagesDownloadMetadataChecker:
    def __init__(self, folderPath, filesManager):
        self.filesManager = filesManager
        self.validUrls = 0
        self.index = 0
        self.metadataFileName = 'imagesDownloadMetadata.pkl'
        self.folderPath = folderPath

    def save(self):
        outputFile = open(self.folderPath + os.sep + self.metadataFileName, 'wb')
        pickle.dump(self.__dict__, outputFile, pickle.HIGHEST_PROTOCOL)
        outputFile.close()

    def load(self):
        filePath = self.folderPath + os.sep + self.metadataFileName
        exist = self.filesManager.checkFile(filePath)
        if exist == True:
            inputFile = open(filePath, 'rb')
            metaDataAux = pickle.load(inputFile)
            inputFile.close()
            self.__dict__.update(metaDataAux)
        else:
            self.index = 1
            self.validUrls = 0

    def delete(self):
        filePath = self.folderPath + os.sep + self.metadataFileName
        self.filesManager.deleteFile(filePath)


class ImagesDownloader:
    def __init__(self, outputWriter, filesManager):
        self.filesManager = filesManager
        self.outputWriter = outputWriter
        self.urlChecker = None

    def downloadFile(self, url, destination, fileName):
        try:
            urllib.request.urlopen(url)
            if self.urlChecker.checkUrl(url) == False:
                self.outputWriter.printWarning("WARNING: Unreachable URL adress - There is not image!")
                return False
            urllib.request.urlretrieve(url, destination + os.sep + fileName)
            return True
        except urllib.error.URLError:
            self.outputWriter.printWarning("WARNING: Unreachable URL adress!")
            return False
        except ConnectionError:
            self.outputWriter.printWarning("WARNING: Unreachable URL adress!")
            return False
        except Exception:
            self.outputWriter.printWarning("WARNING: Unreachable URL adress!")
            return False

    def downloadImages(self, jsonConfig):
        completed = False
        try:
            outputFolder = jsonConfig["output_folder"]
            imagesUrlFile = jsonConfig["url_file_path"]
            startFromBeginning = jsonConfig["new_start"]
            imagePrefix = jsonConfig["image_prefix"]
            outputFolder = self.filesManager.removeLastSlashInFolderPath(outputFolder)
            self.imagesDownloadsMetadata = ImagesDownloadMetadataChecker(outputFolder, self.filesManager)
            self.urlChecker = url_checker.UrlChecker(self.filesManager)

            self.outputWriter.setNewRecord()
            self.outputWriter.writeTextOutput("Downloading images from URLs ...")
            status = self.filesManager.checkPath(outputFolder)
            if status == False:
                raise Exception("ERROR: Destination folder to download images does not exist.")
            urlFile = open(imagesUrlFile, 'r')

            numberOfUrls = sum(1 for url in urlFile)
            if startFromBeginning == 1:
                self.imagesDownloadsMetadata.delete()
            else:
                self.imagesDownloadsMetadata.load()
            urlFile.seek(0)

            for _ in range(self.imagesDownloadsMetadata.index):
                next(urlFile)

            length = 25
            for url in urlFile:
                url = url.strip()
                percentage = (self.imagesDownloadsMetadata.index) / numberOfUrls * 100
                self.outputWriter.setNewRecord()
                self.outputWriter.writeTextOutput("Already processed " + "{0:.4f}".format(percentage) + " % URLs.")
                self.outputWriter.writeFormatedTextOutput(
                    ["- Processing URL index:", str(self.imagesDownloadsMetadata.index)], length)
                self.outputWriter.writeFormatedTextOutput(["- Processing URL:", url], length)

                extension = self.filesManager.getExtension(url)
                imageName = imagePrefix + str(self.imagesDownloadsMetadata.index) + extension

                if self.downloadFile(url, outputFolder, imageName) == True:
                    if self.filesManager.tryToOpenImage(outputFolder + os.sep + imageName) == True:
                        self.imagesDownloadsMetadata.validUrls = self.imagesDownloadsMetadata.validUrls + 1
                    else:
                        self.filesManager.deleteFile(outputFolder + os.sep + imageName)
                self.imagesDownloadsMetadata.index = self.imagesDownloadsMetadata.index + 1
            self.outputWriter.setNewRecord()
            self.outputWriter.writeTextOutput("ALL FILES HAS BEEN DOWNLOADED!")
            self.outputWriter.writeTextOutput("Downloaded " + str(self.imagesDownloadsMetadata.validUrls) + "(" + "{0:.2f}".format(
                self.imagesDownloadsMetadata.validUrls / numberOfUrls * 100) + " %) valid URLs.")
            urlFile.close()
            self.imagesDownloadsMetadata.delete()
            completed = True
            self.outputWriter.setNewRecord()

        finally:
            if completed == False:
                self.outputWriter.setNewRecord()
                self.imagesDownloadsMetadata.save()
                self.outputWriter.writeTextOutput("Program is terminated! Progress was saved!")

