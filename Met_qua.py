import os
import math
import concurrent.futures
from google.cloud import speech_v1 as speech
from pydub import AudioSegment
import pandas as pd
import asyncio
from rasa.core.agent import Agent   
import shutil
import json


def move_file_to_new_folder(file_path):
    folder_path = os.path.join(os.path.dirname(file_path), os.path.splitext(os.path.basename(file_path))[0])
    if not os.path.exists(folder_path):
        os.mkdir(folder_path)
    else:
        shutil.rmtree(folder_path)
        os.mkdir(folder_path)
        
    # Move file into corresponding folder
    new_file_path = os.path.join(folder_path, os.path.basename(file_path))
    os.rename(file_path, new_file_path)
    path = [] 
    path.append(new_file_path)
    return path

def get_folder_path(file_path):
    # Check if the input path exists
    if not os.path.exists(file_path):
        print(f"Path '{file_path}' does not exist.")
        return None
    
    # Check if the input path is a file
    if os.path.isfile(file_path):
        # Remove the extension and get the directory path
        folder_path = os.path.dirname(file_path)
    else:
        folder_path = file_path  # If it's a folder, return the same path
    
    return folder_path

def check_mp3_files_and_create_folders(folder_path):
    mp3_files = [f for f in os.listdir(folder_path) if f.endswith('.mp3')]
    print(f'There are {len(mp3_files)} MP3 files in the folder "{folder_path}"')
    
    for mp3_file in mp3_files:
        mp3_filename = os.path.splitext(mp3_file)[0]
        mp3_folder_path = os.path.join(folder_path, mp3_filename)
        if not os.path.exists(mp3_folder_path):
            os.mkdir(mp3_folder_path)
        else:
            shutil.rmtree(mp3_folder_path)
            os.mkdir(mp3_folder_path)
        print(f'Created folder "{mp3_folder_path}" for MP3 file "{mp3_file}"')
        
        # Move MP3 file into corresponding folder
        src = os.path.join(folder_path, mp3_file)
        dst = os.path.join(mp3_folder_path, mp3_file)
        os.rename(src, dst)

def check_folders_for_mp3_files(root_folder):
    lis1 = []
    for folder in os.listdir(root_folder):
        folder_path = os.path.join(root_folder, folder)
        if os.path.isdir(folder_path):
            mp3_files = [f for f in os.listdir(folder_path) if f.endswith('.mp3')]
            if len(mp3_files) == 0:
                print(f'No MP3 files found in folder "{folder_path}"')
            else:
                print(f'Found {len(mp3_files)} MP3 files in folder "{folder_path}"')
                for mp3_file in mp3_files:
                    mp3_file_path = os.path.join(folder_path, mp3_file)
                    lis1.append(mp3_file_path)
    return lis1

def split_mp3_to_wav(mp3_file, min_per_split):
    sound = AudioSegment.from_file(mp3_file, format="mp3")
    sound = sound.set_frame_rate(24000)
    
    total_mins = math.ceil(sound.duration_seconds / 55)
    split_folder = os.path.join(os.path.dirname(mp3_file), 'split_files')
    if not os.path.exists(split_folder):
        os.makedirs(split_folder)
        
    for i in range(0, total_mins, min_per_split):
        t1 = i * 55 * 1000
        t2 = (i + min_per_split) * 55 * 1000 if (i + min_per_split) < total_mins else sound.duration_seconds * 1000
        split_audio = sound[t1:t2]
        
        split_fn = str(i) + '_' + os.path.basename(mp3_file).split('.')[0] + '.wav'
        split_filepath = os.path.join(split_folder, split_fn)
        
        split_audio.export(split_filepath, format="wav")
        print(f"Segment {i//min_per_split+1}/{math.ceil(total_mins/min_per_split)} done.")
    
    print('Chờ xử lý, sẽ tốn 1 ít thời gian')

def recognize_audio_files_in_directory(folder, save_path=None):
    # Define a function to recognize the audio from a single file
    def recognize_audio(file_path):
        # Read the contents of the file
        with open(file_path, 'rb') as f:
            byte_data = f.read()
        # Create a RecognitionConfig object
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=24000,
            enable_automatic_punctuation=False,
            language_code='vi-VN',
            model='latest_long'
        )
        # Create a RecognitionAudio object
        audio = speech.RecognitionAudio(content=byte_data)
        # Create a SpeechClient object
        client = speech.SpeechClient()
        # Call the recognize method to convert audio to text
        response = client.recognize(config=config, audio=audio)
        # Get the result from the response object
        result = response.results[0]
        alternative = result.alternatives[0]
        transcript = alternative.transcript.encode('utf-8').decode('unicode_escape').encode('latin1').decode('utf-8')
        return transcript

    # Get the list of audio files in the directory
    audio_folder = os.path.join(folder, 'split_files')
    audio_files = [os.path.join(audio_folder, f) for f in os.listdir(audio_folder) if f.endswith('.wav')]

    # Create output directory if it doesn't exist
    if save_path is not None:
        os.makedirs(save_path, exist_ok=True)

    # Use ThreadPoolExecutor to process the files concurrently
    results = {}
    with concurrent.futures.ThreadPoolExecutor() as executor:
        for i, file in enumerate(audio_files):
            # Call the recognize_audio function for each audio file
            future = executor.submit(recognize_audio, file)
            results[os.path.basename(file)] = future

        # Get the results from the futures that were called
        final_results = []
        for file in sorted(results.keys()):
            future = results[file]
            result = future.result()
            final_results.append(result)

            # Save the result to a file if a save path is provided
            if save_path is not None:
                transcription = result
                filename = os.path.basename(file)
                with open(os.path.join(save_path, f"transcript_{filename}.txt"), "w", encoding="utf-8") as f:
                    f.write(transcription)

    # Return the list of text transcripts in the order of audio file names
    transcripts = ''.join(final_results)
    return transcripts

def split_mp3_and_recognize_audio_and_run_exam(folder_path, dapan, save_path=None):
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'D:\Scienceproject\RASA\key.json'
    speech_client = speech.SpeechClient()

    # folder_path_1 = get_folder_path(folder_path)

    # # CHECK folder có bao nhiêu file.mp3
    # check_mp3_files_and_create_folders(folder_path_1)

    # # Lấy đường file_path đuôi mp3
    # mp3_file = check_folders_for_mp3_files(folder_path_1)
    # print(mp3_file)
    mp3_file = move_file_to_new_folder(folder_path)
    # đưa từng file vào xử lý
    mp3_file_name_all =[]
    for mp3_file_path in mp3_file:
        mp3_folder_path, mp3_filename = os.path.split(mp3_file_path)
        mp3_file_name = os.path.splitext(mp3_filename)[0]
        mp3_file_name_all.append(mp3_file_name)
        # Lấy đường dẫn folder chứa file mp3
        if save_path is None:
            save_path = mp3_folder_path

        # Chia tệp MP3 thành các tệp WAV
        split_mp3_to_wav(mp3_file_path, 1)

        # Nhận dạng các tệp WAV trong thư mục `split_files`
        text = recognize_audio_files_in_directory(os.path.dirname(mp3_file_path), mp3_folder_path)
        # Tiếp tục xử lý đoạn văn bản nhận dạng được
        list_cau1 = text.lower().split('kết thúc cảm ơn')[0:-1]
        print(list_cau1)
        questions3 = []
        
        for j in range(len(list_cau1)):
            cau1 = list_cau1[j].split()
            print(cau1)
            dau_1 = 0
            ket_1 = len(cau1)

            for i in range(len(cau1)):
                if cau1[i] == 'trả':
                    if i+3 < len(cau1) and cau1[i+1] == 'lời' and cau1[i+2] == 'câu' and cau1[i+3] == 'hỏi':
                        dau_1 = i+6
                if cau1[i] == 'thời':
                    if i+3 < len(cau1) and cau1[i+1] == 'gian' and cau1[i+2] == 'trả' and cau1[i+3] == 'lời':
                        ket_1 = i

            list_cau1[j] = cau1[int(dau_1):int(ket_1)]
            questions2 = list_cau1
            cau1.clear()
        print(questions2)
        for q in questions2:
            question = ' '.join(q)
            questions3.append(question)
        return questions3,mp3_folder_path,mp3_file_name

def read_items(questions):
    agent = Agent.load(r"D:\Scienceproject\RASA\model_rasa\models\20230314-093029-watery-pudding.tar.gz",action_endpoint=None)
    traloi = []
    cau = []
    for i in range(len(questions)):
        response = agent.parse_message(message_data=questions[i])
        result = asyncio.run(response)
        intent_name = result["intent"]["name"]
        cau.append(intent_name)
    for j in range(len(cau)):
        if cau[j] == 'DAP_AN_A':
            traloi.append('A')
        elif cau[j] == 'DAP_AN_B':
            traloi.append('B')
        elif cau[j] == 'DAP_AN_C':
            traloi.append('C')
        elif cau[j] == 'DAP_AN_D':
            traloi.append('D')
        else:
            traloi.append('0')
    return traloi
def analyze_results(dapan, traloi, folder,file_name):
    ketqua = []
    score = 0
    # Lấy đường file_path đuôi mp3
    for i in range(len(dapan)):
        ketqua.append("TRUE" if dapan[i] == traloi[i] else "FALSE")
        if dapan[i] == traloi[i]:
            score += 1
    df = pd.DataFrame(zip(dapan, traloi, ketqua), index=['Questions 1','Questions 2','Questions 3','Questions 4','Questions 5'], columns=['SOLUTION', 'ANSWER', 'RESULT'])
    # Đặt tên cho tệp JSON theo tên file mp3 tương ứng
    # json_file_name = os.path.splitext(file_name)[0] + ".json"
    # with open(os.path.join(folder, json_file_name), 'w', encoding='utf-8') as file:
    #     df.to_json(file, force_ascii=False)
    # print("Đây là kết quả:.........")
    # print(df)
    df1 = df.to_html()
    return df1


# dapan = []
# CAU = []
# path = input("Nhập đường dẫn: ")
# number = int(input("Nhập số lượng câu hỏi: "))
# for i in range(number):
#     b = i+1
#     B = input("Nhập đáp án câu %d: " %b).upper()
#     while B not in ["A", "B", "C", "D"]:
#         print("Đáp án không hợp lệ, vui lòng nhập lại!")
#         B = input("Nhập đáp án câu %d: " %b).upper()
#     dapan.append(B)
# ques,mp3_folder,mp3_name = split_mp3_and_recognize_audio_and_run_exam(path,dapan)
# Asw = read_items(ques)
# KQ = analyze_results(dapan,Asw,mp3_folder,mp3_name)
# print(KQ)