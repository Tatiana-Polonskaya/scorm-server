from fastapi import FastAPI, HTTPException
import os
import shutil
import zipfile
from fastapi import FastAPI, File, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware

import tempfile
import uuid

import time
from pathlib import Path
import json
from starlette import status
from starlette.responses import Response

app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:5173",
    "https://localhost:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

local_project_path = "/scorms"
local_info_scorms = "app/list_of_scorms.json"
encoding="UTF-8"

if not os.path.exists(local_project_path):
        os.makedirs(local_project_path)

#Вычисляет размер папки, количество файлов и количество итераций функции
def folderSize(path):
    fsize = 0
    for file in Path(path).rglob('*'):
        if (os.path.isfile(file)):
            fsize += os.path.getsize(file)
    return fsize

# Получение всех скорм пакетов, которые есть 
@app.get("/")
async def get_list_of_scorms():
   with open(local_info_scorms, "r", encoding=encoding) as json_file:
    data = json.load(json_file)
    return data

# Cохранение скорм-пакета 
@app.post("/upload/")
async def upload_files( file: UploadFile = File(...)):

    uuid4 = str(uuid.uuid4())
    new_path = f"{local_project_path}/{uuid4}"

    if not os.path.exists(new_path):
        os.makedirs(new_path)
    else:
        raise Exception(f"Папка {new_path} уже существует. Дальнейшее выполнение программы прервано.")
    
    start_time = time.time()

    with tempfile.TemporaryDirectory() as temp_dir:
        file_location = os.path.join(temp_dir, file.filename)

        with open(file_location, "wb") as file_object:
            shutil.copyfileobj(file.file, file_object)

        # разархивируем файл в папку scorm
        with zipfile.ZipFile(file_location, 'r') as zip_ref:
            zip_ref.extractall(new_path)
        
    end_time = time.time()

    size = folderSize(new_path)

    data = {
        'id':uuid4,
        'title':file.filename,
        'link': f'{new_path}/index.html',
        'time_download': end_time - start_time,
        'time_render': 0,
        'archive_size': file.size, # bytes
        'final_size':size, # bytes
    }

    # Проверка существования файла data.json
    if os.path.exists(local_info_scorms):
        with open(local_info_scorms, 'r', encoding=encoding) as json_file:
            data_list = json.load(json_file)
    else:
        data_list = []
    data_list.append(data)
    with open(local_info_scorms, 'w', encoding=encoding) as json_file:
        json.dump(data_list, json_file)

    return {"message": f"Файл успешно загружен, сохранен и разархивирован в папке {new_path}", "data": data}

# Получение скорм-пакета по id
@app.get("/scorm/{scorm_id}")
async def get_scorm_by_id(scorm_id):
    with open(local_info_scorms, "r", encoding=encoding) as f:
        scorms = json.load(f)
    try:
        scorm = next(a for a in scorms if a["id"] == scorm_id)
        return scorm
    except StopIteration:
        raise HTTPException(status_code=404, detail="Scorm not found")

# Изменение поля time_render по id
@app.put("/scorm/{scorm_id}")
async def put_scorm_by_id(scorm_id, time_render: int):
    with open(local_info_scorms, "r", encoding=encoding) as f:
        scorms = json.load(f)
    try:
        edit_scorm =  next(a for a in scorms if a["id"] == scorm_id)
        edit_scorm["time_render"] = time_render
        scorms[scorms.index(next(a for a in scorms if a["id"] == scorm_id))] = edit_scorm
    except ValueError:
        raise HTTPException(status_code=404, detail="Scorm not found")
    with open(local_info_scorms, "w") as f:
        json.dump(scorms, f)
    return Response(status_code=status.HTTP_200_OK)

# отправка на облако
@app.post("/upload_and_extract_to_mail/")
async def upload_and_extract_to_mail(file: UploadFile = File(...)):
    new_path = str(uuid.uuid4())
    client.mkdir(new_path)
    # Создание временной директории
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_zip_path = os.path.join(temp_dir, file.filename)
        
        # Сохранение zip-файла во временной директории
        with open(temp_zip_path, "wb") as temp_zip:
            temp_zip.write(await file.read())
        
        # Разархивация содержимого zip-файла
        with zipfile.ZipFile(temp_zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
            
            # Загрузка содержимого временной директории на облако Mail.ru
            for root, _, files in os.walk(temp_dir):
                for file_name in files:
                    file_path = os.path.join(root, file_name)
                    with open(file_path, 'rb') as uploaded_file:
                        remote_path = f"{new_path}/{file_name}"
                        result = client.upload(remote_path=remote_path, local_path=file_path)
    print(result)
    if result:
        return {"message": "Файлы успешно загружены на облачное хранилище Mail.ru"}
    else:
        return {"message": "Ошибка при загрузке файлов на облачное хранилище"}

