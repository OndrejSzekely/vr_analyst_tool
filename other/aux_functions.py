import sys
import json
import os

def appendParrentFolderToModules():
    workingDirPath = os.getcwd()
    parrentFolder = workingDirPath[0:workingDirPath.rfind("/")]
    sys.path.insert(0,parrentFolder)