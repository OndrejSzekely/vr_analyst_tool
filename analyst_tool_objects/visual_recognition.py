from analyst_tool_objects import vr_python_api

class VisualRecognition:
    vr = None

    def __init__(self, api_key, api_version):
        self.vrServiceHandler = vr_python_api.VrPythonApi(api_key, api_version)
        self.vrServiceHandler.initializeVRObject()

    def getApiKey(self):
        return self.vrServiceHandler.getApiKey()

    def getApiVersion(self):
        return self.vrServiceHandler.getApiVersion()

    def endVisualRecognitionService(self):
        self.vrServiceHandler.closeVisualRecognitionService()

    # CHECK IF CLASSIFIER EXTISTS, GET CLASSIFIER ID OR NAME, CHECK IF EXISTS CLASSIFIER WITH GIVEN ID AND NAME
    # exists(Bool), classifierName, classifierId
    def existsClassifier(self, classifierName=None, classifierId=None):
            if classifierName != None and classifierId != None:
                listOfClassifiers = self.vrServiceHandler.getCustomClassifiers()
                for classifier in listOfClassifiers["classifiers"]:
                    if classifier["name"] == classifierName and classifier["classifier_id"] == classifierId:
                        return True, classifierName, classifierId
                return False, None, None

            if classifierName != None:
                listOfClassifiers = self.vrServiceHandler.getCustomClassifiers()
                for classifier in listOfClassifiers["classifiers"]:
                    if classifier["name"] == classifierName:
                        return True, classifierName, classifier["classifier_id"]
                return False, None, None

            if classifierId != None:
                listOfClassifiers = self.vrServiceHandler.getCustomClassifiers()
                for classifier in listOfClassifiers["classifiers"]:
                    if classifier["classifier_id"] == classifierId:
                        return True, classifier["name"], classifierId
                return False, None, None

            return False, None, None

    def deleteClassifier(self, classifierName = None, classifierId = None):
        if classifierName != None and classifierId != None:
            exists, name, id = self.existsClassifier(classifierName=classifierName, classifierId=classifierId)
            if exists == True:
                self.vrServiceHandler.deleteClassifier(id)
                return True
            else:
                return False

        if classifierName != None:
            exists, _, id = self.existsClassifier(classifierName=classifierName)
            if exists == True:
                self.vrServiceHandler.deleteClassifier(id)
                return True
            else:
                return False

        if classifierId != None:
            exists, _, _ = self.existsClassifier(classifierId=classifierId)
            if exists == True:
                self.vrServiceHandler.deleteClassifier(classifierId)
                return True
            else:
                return False

    def getCustomClassifiers(self):
        return self.vrServiceHandler.getCustomClassifiers()

    def createClassifier(self, classifierName, kwargs):
        try:
            return (True, self.vrServiceHandler.createClassifier(classifierName, kwargs))
        except Exception as e:
            return (False, e)

    def updateClassifier(self, classifierId, kwargs):
        try:
            self.vrServiceHandler.updateClassifier(classifierId, kwargs)
            return (True, "")
        except Exception as e:
            return (False, e)

    def getClassifiersDetails(self, classifierName = None, classifierId = None):
        if classifierName != None and classifierId != None:
            exists, name, id = self.existsClassifier(classifierName=classifierName, classifierId=classifierId)
            if exists == True:
                info = self.vrServiceHandler.getCustomClassifier(id)
                return (True,info)
            else:
                return (False, "Classifier does not exist.")

        if classifierName != None:
            exists, _, id = self.existsClassifier(classifierName=classifierName)
            if exists == True:
                info = self.vrServiceHandler.getCustomClassifier(id)
                return (True, info)
            else:
                return (False, "")

        if classifierId != None:
            exists, _, _ = self.existsClassifier(classifierId=classifierId)
            if exists == True:
                info = self.vrServiceHandler.getCustomClassifier(classifierId)
                return (True, info)
            else:
                return (False, "")

    def classifyImage(self, classifierName, classifierId, image):
        exist, classifierName, classifierId = self.existsClassifier(classifierName, classifierId)
        if exist == True:
            try:
                return self.vrServiceHandler.classifyImage(classifierId, image)
            except Exception:
                foo = 9
                return self.vrServiceHandler.classifyImage(classifierId, image)

        return ""
