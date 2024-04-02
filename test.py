from zipfile import ZipFile

path = "C:\projects\python\scorm-server\scorm"
zipFile = "folkmap.zip"

with ZipFile(zipFile, "a") as myzip:
    myzip.extractall(path=path)

