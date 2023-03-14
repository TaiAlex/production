from fastapi import FastAPI, HTTPException, Request, Form, UploadFile, File, Depends, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import List, Union
from models import Choice, Answer
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer,OAuth2PasswordRequestForm
from pydantic import BaseModel
from testAPI import find_path, mp3_to_wav, split_list_answer
from Speechtotext import split_mp3_and_recognize_audio_and_run_exam as wav_to_txt
import str_time
import os
import uvicorn

app = FastAPI()
templates = Jinja2Templates(directory="templates")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


time = str_time.now_utc()
dir_name = str_time.str_yyyy_mm_dd(time)
file_name = str_time.get_time()
answer_input = []

fake_users_db = {
    "truc": {
        "username": "truc",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "hashed_password": "fakehashed123456",
        "disabled": False,
    },
    "taialex": {
        "username": "taialex",
        "full_name": "Tài A-lét",
        "email": "example@hello.com",
        "hashed_password": "fakehashednon",
        "disabled": False,
    },
    "alice": {
        "username": "alice",
        "full_name": "Alice Wonderson",
        "email": "alice@example.com",
        "hashed_password": "fakehashedsecret2",
        "disabled": True,
    },
}

class User(BaseModel):
    username: str
    email: Union[str, None] = None
    full_name: Union[str, None] = None
    disabled: Union[bool, None] = None
    
class UserInDB(User):
    hashed_password: str = Form(...), 



def fake_hash_password(password: str = Form(...)):
    return "fakehashed" + password

def fake_decode_token(username : str = Form(...)):
    return User(
        username=username + "fakedecoded",
        email="john@example.com"
    )

async def get_current_user(token: str = Depends(oauth2_scheme)):
    user = fake_decode_token(token)
    return user

def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)

def fake_decode_token(token):
    user = get_user(fake_users_db, token)
    return user

async def get_current_user(token: str = Depends(oauth2_scheme)):
    user = fake_decode_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

@app.post("/token",response_class=HTMLResponse)
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    user_dict = fake_users_db.get(form_data.username)
    if not user_dict:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    user = UserInDB(**user_dict)
    hashed_password = fake_hash_password(form_data.password)
    if not hashed_password == user.hashed_password:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    return templates.TemplateResponse("index.html", {"request": request})

@app.post('/api/data')
async def process_data(Q1: str = Form(...), Q2: str = Form(...), Q3: str = Form(...), Q4: str = Form(...), Q5: str = Form(...)):
    answer_input.clear()
    answer_input.append(Q1.upper())
    answer_input.append(Q2.upper())
    answer_input.append(Q3.upper())
    answer_input.append(Q4.upper())
    answer_input.append(Q5.upper())
    return answer_input

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    try:
        dir_path = "upload/" + str_time.str_yyyy_mm_dd(time)
        str_time.create_path(dir_path)
        type = file.filename.split(".")[1]
        file_path = dir_path + "/" + f'{file_name}.{type}'
        file_bytes = file.file.read()
        str_time.upload_file_bytes(file_bytes, file_path)
    except Exception:
        return {"message": "There was an error uploading the file"}
    finally:
        file.file.close()   
    return {"message": f"Successfuly uploaded {file.filename}"}

@app.get("/to_text")
async def test():
    try:
        path = find_path()
        text_id = wav_to_txt(path)
        text = split_list_answer(text_id, answer_input)
        return text
    except:
        return "Error!!!"

@app.get("/answer")
async def print():
    with open(r'E:\23-02-2023\input\upload\24-02-2023\204950.txt', 'r', encoding = 'UTF-8') as data:
        text = data.read()
    return text

@app.get("/")
async def main(request: Request):
    return templates.TemplateResponse("template.html", {"request": request})
