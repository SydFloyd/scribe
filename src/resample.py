import librosa
import soundfile as sf

def resample_16k(file_path):
    # Load the original WAV file
    # y, sr = librosa.load(file_path, sr=48000)
    y, sr = sf.read(file_path)

    # Resample to 16000 Hz
    y_resampled = librosa.resample(y, orig_sr=sr, target_sr=16000)

    return y_resampled, 16000

import io

def resample_16k_direct(file_like_object):
    with sf.SoundFile(file_like_object, mode='r') as file:
        y = file.read(dtype='float32')
        sr = file.samplerate

    # Resample to 16000 Hz
    y_resampled = librosa.resample(y, orig_sr=sr, target_sr=16000)

    return y_resampled, 16000