from fastapi import FastAPI, HTTPException, Request, Form, UploadFile, File, Depends, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import List, Union
import shutil
import str_time

app = FastAPI()
templates = Jinja2Templates(directory="templates")

time = str_time.now_utc()
dir_name = str_time.str_yyyy_mm_dd(time)
file_name = str_time.get_time()

@app.post("/multiple-upload")
async def upload(files: List[UploadFile] = File(...)):
    for file_in_list in files:
        try:
            dir_path = "upload/" + str_time.str_yyyy_mm_dd(time)
            str_time.create_path(dir_path)
            type = file_in_list.filename.split(".")[1]
            file_path = dir_path + "/" + f'{file_name}.{type}'
            file_bytes = file_in_list.file.read()
            str_time.upload_file_bytes(file_bytes, file_path)
        except Exception:
            return {"message": "There was an error uploading the file"}
        finally:
            file_in_list.file.close()   
    return {"message": f"Successfuly uploaded {file_in_list.filename}"}

# @app.get("/")
# async def main(request: Request):
#     return templates.TemplateResponse("template.html", {"request": request})