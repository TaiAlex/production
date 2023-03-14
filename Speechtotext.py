import os
import math
import concurrent.futures
from google.cloud import speech_v1 as speech
from pydub import AudioSegment
import shutil

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r'E:\14-03-2023\demo\key.json'
speech_client = speech.SpeechClient()

import os
import shutil

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
                file_1 = filename.split(".")[0]
                with open(os.path.join(save_path, f"transcript_{file_1}.txt"), "w", encoding="utf-8") as f:
                    f.write(transcription)

    # Return the list of text transcripts in the order of audio file names
    transcripts = ''.join(final_results)
    return transcripts

def split_mp3_and_recognize_audio_and_run_exam(folder_file, save_path=None):
    t = folder_file.split(".")[0]
    # CHECK folder có bao nhiêu file.mp3
    mp3_file = move_file_to_new_folder(folder_file)
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
        # Lưu kết quả nhận dạng vào file mới
        text_file_name = mp3_file_name + ".txt"
        text_file_path = os.path.join(save_path, text_file_name)
        with open(text_file_path, "w", encoding="utf-8") as f:
            f.write(text)
    t = f"{t}\{text_file_name}"
    return t