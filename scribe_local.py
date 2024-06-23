import pyaudio
import wave
import webrtcvad
import collections
import os
import threading
from time import sleep
from colorama import Fore, Back, Style, init
import datetime
import sqlite3

# from scribe_loc_api_call import get_transcription
from src.whisper import TranscriptionModel
from src.gpt import handy_GPT, GPT
from src.play_sound import play_sound
from src.tts import speak

init() # init colorama

transcriber = TranscriptionModel()

if not os.path.exists("./gpt_speech"):
    os.mkdir("./gpt_speech")

def gpt_speak():
    while True:
        if len(gpt_speech_file_heap) > 0:
            sleep(0.25)
            curr = gpt_speech_file_heap.pop(0)
            play_sound(f"./gpt_speech/{curr}")
        sleep(0.02)

def gpt_voice():
    output_index = 1
    while True:
        if len(gpt_voice_heap) > 0:
            curr = gpt_voice_heap.pop(0)
            speak(curr, f"gpt_speech/speech_{output_index}")
            gpt_speech_file_heap.append(f"speech_{output_index}.mp3")
            output_index += 1
        sleep(0.02)

# Insert a row of data
def store_clip(file_path, 
               transcript, 
               start_timestamp, 
               end_timestamp, 
               start_year, 
               start_month, 
               start_day, 
               start_hour,
               start_minute,
               start_second,
               end_year, 
               end_month, 
               end_day, 
               end_hour,
               end_minute,
               end_second,
               comment):
    with sqlite3.connect('scribe.db') as db_connection:
        db_connection.execute("INSERT INTO speech (file_path, transcript, start_timestamp, end_timestamp, start_year, start_month, start_day, start_hour, start_minute, start_second, end_year, end_month, end_day, end_hour, end_minute, end_second, comment) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                            (file_path, 
                            transcript, 
                            start_timestamp, 
                            end_timestamp, 
                            start_year, 
                            start_month, 
                            start_day, 
                            start_hour,
                            start_minute,
                            start_second,
                            end_year, 
                            end_month, 
                            end_day,
                            end_hour,
                            end_minute,
                            end_second,
                            comment))

def process_heap():
    global system_message

    def contains_non_english_characters(text):
        try:
            text.encode('ascii')
        except UnicodeEncodeError:
            return True
        return False
    
    # has to be lowercase
    blacklisted_transcriptions = [
        '', ' ', '.', 'bye!', 'bye.',
        "thanks for watching.", "thanks for watching!", 
        "thank you for watching.", "thank you for watching!", "thank you for watching !",
        "thank you so much for watching !",
        "you", "you.",
        "i'll see you guys in the next one. bye.",
        "i'll see you guys in the next one.", "thank you so much for watching, until the next videos !!!",
        "subs by www.zeoranger.co.uk",
        "thank you for watching. always be happy.",
        'thank you.',
    ]

    awakening_phrases = ["hey computer", "hey computer.", 
                         "computer", "computer.",
                         "hey gpt.", "hey gpt",
                         "hey chat gpt.", "hey chat gpt",
                         "gpt", "gpt.",
                         ]
    sending_phrases = ['send.', 'send', 
                       'end.', 'end', 
                       'sand.', 'sand',
                       'shoot.', 'shoot',
                       'go.', 'go',
                       ]

    current_color = Fore.CYAN
    gpt_listening = False
    message = ""

    while True:
        if len(transcript_heap) > 0:
            block = transcript_heap.pop(0)
            curr = block[1].strip()

            if curr.lower() in blacklisted_transcriptions or contains_non_english_characters(curr):
                continue

            if curr.lower() in awakening_phrases:
                print(Fore.RED + "GPT LISTENING.")
                play_sound("sounds/ready.wav")
                gpt_listening = True
                current_color = Fore.WHITE

            if curr.lower() in sending_phrases:
                current_color = Fore.CYAN

                if gpt_listening:
                    gpt_listening = False
                    play_sound("sounds/sent.wav")
                    print(Fore.YELLOW + f"\nCOMPILED MESSAGE: {message}\n\n")
                    response = m.prompt(message)
                    # response = mistral_prompt(message, system_message=system_message)
                    print(Fore.LIGHTMAGENTA_EX + response)
                    gpt_voice_heap.append(response)
                    message = ""

            if curr.lower() in ['cancel.', 'cancel', 'nevermind.', 'nevermind']:
                current_color = Fore.CYAN

                if gpt_listening:
                    play_sound("sounds/cancel.wav")
                    gpt_listening = False
                    message = ""

            if gpt_listening and curr.lower() not in awakening_phrases:
                message += " " + curr

            print()
            print(current_color + curr)

            # Store audio and transcription
            if curr.lower() not in awakening_phrases and gpt_listening:
                store_clip(*block, 'Text was sent to chatGPT')
            else:
                store_clip(*block, '')

        sleep(0.02)

def transcribe_heap():
    while True:
        if len(rec_heap) > 0:
            item = rec_heap.pop(0) # get latest segment path
            # audio_file = open(segment_filename, "rb")
            # transcript = get_transcription(item[0])
            try:
                transcript = transcriber.transcribe(item[0])['text']
            except:
                transcript = transcriber.transcribe(item[0]).text
            transcript_heap.append((item[0], 
                                    transcript,
                                    *item[1:]))
        sleep(0.02)

def record_speech(output_dir='speech_segments', 
                  vad_aggressiveness=3, 
                  chunk_duration_ms=30, 
                  padding_duration_ms=500, 
                  min_speech_time_ms=100,
                  rate=48000, 
                  channels=1):
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    FORMAT = pyaudio.paInt16

    vad = webrtcvad.Vad(vad_aggressiveness)

    chunk = int(chunk_duration_ms/1000 * rate) # chunk=480
    
    num_padding_chunks = int(padding_duration_ms / chunk_duration_ms)
    sliding_window = collections.deque(maxlen=num_padding_chunks)

    recording = False
    triggered = False

    p = pyaudio.PyAudio()

    stream = p.open(format=FORMAT,
                    channels=channels,
                    rate=rate,
                    input=True,
                    frames_per_buffer=chunk)

    print("Listening...")

    frames = []
    rec_index = 1

    # metadata
    start_timestamp = ""
    end_timestamp = ""
    start_year = None
    start_month = None
    start_day = None
    start_hour = None
    start_minute = None
    start_second = None
    end_year = None
    end_month = None
    end_day = None
    end_hour = None
    end_minute = None
    end_second = None


    while True:
        chunk_data = stream.read(chunk)
        #valid_chunk = webrtcvad.valid_rate_and_frame_length(rate, chunk) # check chunk is readable

        active = vad.is_speech(chunk_data, rate)

        if not recording and active:
            # print("Start recording")
            recording = True
            triggered = False
            frames = []

            # start metadata
            current_datetime = datetime.datetime.now()
            start_timestamp = current_datetime.strftime("%Y%m%d_%H%M%S")
            start_year = current_datetime.strftime('%Y')
            start_month = current_datetime.strftime('%m')
            start_day = current_datetime.strftime('%d') 
            start_hour = current_datetime.strftime('%H')  
            start_minute = current_datetime.strftime('%M')
            start_second = current_datetime.strftime('%S') 

        if recording:
            frames.append(chunk_data)
            sliding_window.append(active)
            # print('-', end='', flush=True)

            if not active and not triggered:
                triggered = True # ready to stop recording when activity stops
            
            if not active and triggered and all(not s for s in sliding_window):
                if len(frames)*chunk_duration_ms > min_speech_time_ms+padding_duration_ms:

                    # Save the recorded speech segment
                    segment_filename = os.path.join(output_dir, f'{start_timestamp}.wav')
                    wf = wave.open(segment_filename, 'wb')
                    wf.setnchannels(channels)
                    wf.setsampwidth(p.get_sample_size(FORMAT))
                    wf.setframerate(rate)
                    wf.writeframes(b''.join(frames))
                    wf.close()

                    # end metadata
                    current_datetime = datetime.datetime.now()
                    end_timestamp = current_datetime.strftime("%Y%m%d_%H%M%S")
                    end_year = current_datetime.strftime('%Y') 
                    end_month = current_datetime.strftime('%m')
                    end_day = current_datetime.strftime('%d')
                    end_hour = current_datetime.strftime('%H')
                    end_minute = current_datetime.strftime('%M')
                    end_second = current_datetime.strftime('%S')

                    # add recording to queue
                    rec_heap.append((segment_filename, 
                                     start_timestamp,
                                     end_timestamp,
                                     start_year,
                                     start_month,
                                     start_day,
                                     start_hour,
                                     start_minute,
                                     start_second,
                                     end_year,
                                     end_month,
                                     end_day,
                                     end_hour,
                                     end_minute,
                                     end_second))
                    rec_index += 1
                else:
                    pass

                # Reset the state
                recording = False
                triggered = False
                frames = []
                sliding_window.clear()


if __name__ == '__main__':
    try:
        global system_message

        system_message = "You are a verbal assistant, and your outputs are turned to audio via tts, so speak accordingly :).\n"
        system_message += "Be clever and find imaganitive ways to compact lots of information into a small message.\n"
        system_message += "Thank you <3"

        m = GPT(system_message=system_message, save_messages=True)

        gpt_speech_file_heap = []
        gpt_voice_heap = []
        transcript_heap = []
        rec_heap = []

        voice_thread = threading.Thread(target=gpt_voice)
        speech_thread = threading.Thread(target=gpt_speak)
        process_thread = threading.Thread(target=process_heap)
        transcribe_thread = threading.Thread(target=transcribe_heap)
        record_thread = threading.Thread(target=record_speech)

        voice_thread.start()
        speech_thread.start()
        process_thread.start()
        transcribe_thread.start()
        record_thread.start()

        # Wait for the threads to finish
        voice_thread.join()
        speech_thread.join()
        process_thread.join()
        transcribe_thread.join()
        record_thread.join()

    except KeyboardInterrupt:
        print("\nInterrupt received, shutting down...")
    finally:
        print("Exited program.")