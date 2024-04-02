import os
import shutil
import zipfile
from fastapi import FastAPI, File, Form, UploadFile
from zipfile import ZipFile 

pathDir = "C:\\projects\\python\\scorm-server\\scorm"

app = FastAPI()
@app.get("/")

async def home():
   return {"data": "Hello World"}

@app.post("/upload_files/")
async def upload_files(folder_name: str = Form(...), file: UploadFile = File(...)):
    # сохраняем загруженный файл
    file_location = f"uploaded_files/{file.filename}"
    with open(file_location, "wb") as file_object:
        shutil.copyfileobj(file.file, file_object)
    
    # Проверяем существование папки "title"
    if not os.path.exists(folder_name):
        # Если папка не существует, создаем ее
        os.makedirs(folder_name)
    else:
        # Если папка уже существует, вызываем ошибку
        raise Exception("Папка уже существует. Дальнейшее выполнение программы прервано.")

    # разархивируем файл в папку scorm
    with zipfile.ZipFile(file_location, 'r') as zip_ref:
        zip_ref.extractall(folder_name)

    return {"message": "Файл успешно загружен, сохранен и разархивирован в папке "}