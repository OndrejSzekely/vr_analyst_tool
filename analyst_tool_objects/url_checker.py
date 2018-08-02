import requests

class UrlChecker:

    def __init__(self, filesManager):
        self.filesManager = filesManager

    def getServerType(self, url):
        if url.find("flickr.com") != -1:
            return "flickr"
        return "other"

    def flickrCheck(self, url):
        request = requests.get(url)
        if request.request.url.find("photo_unavailable.png") != -1:
            return False
        return True

    def otherCheck(self, url):
        request = requests.get(url)
        extension = self.filesManager.getExtension(request.request.url)
        if self.filesManager.checkGivenExtensionOfImage(extension, False) == False:
            return False
        return True

    def checkAscii(self, url):
        try:
            url.encode('ascii')
            return True
        except Exception:
            return False

    def checkUrl(self, url):
        type = self.getServerType(url)
        if self.checkAscii(url) == False:
            return False
        if (type == "flickr") and self.flickrCheck(url) == False:
            return False
        if (type == "other") and self.otherCheck(url) == False:
            return False
        return True
