from watson_developer_cloud import VisualRecognitionV3
import simplejson

class VrPythonApi:
    vrObject = None

    def __init__(self, api_key, api_version):
        self.apiVersion = api_version
        self.apiKey = api_key

    def getApiKey(self):
        return self.apiKey

    def getApiVersion(self):
        return  self.apiVersion

    def initializeVRObject(self):
        if len(self.apiKey) == 40: 
            self.vrObject = VisualRecognitionV3(self.apiVersion, api_key=self.apiKey)
        else:
            self.vrObject = VisualRecognitionV3(self.apiVersion, iam_apikey=self.apiKey)

    def closeVisualRecognitionService(self):
        self.vrObject = None

    def getCustomClassifiers(self):
        return self.vrObject.list_classifiers(verbose=True)

    def getCustomClassifier(self, classifierId):
        return  self.vrObject.get_classifier(classifierId)

    def deleteClassifier(self, classifierId):
        self.vrObject.delete_classifier(classifierId)

    def createClassifier(self, classifierName, kwargs):
        return self.vrObject.create_classifier(classifierName, **kwargs)

    def updateClassifier(self, classifierId, kwargs):
        return self.vrObject.update_classifier(classifierId, **kwargs)

    def classifyImage(self, classiferId, image):
        return self.vrObject.classify(images_file=image, parameters=simplejson.dumps({"classifier_ids": [classiferId], "threshold": 0}))
