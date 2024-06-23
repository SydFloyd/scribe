import numpy as np
import wave

def read_wave(filename):
    with wave.open(filename, 'rb') as wave_file:
        # Extract Audio Parameters
        n_channels, sample_width, framerate, n_frames, comptype, compname = wave_file.getparams()
        
        # Read Audio Frames
        audio_frames = wave_file.readframes(n_frames)
        
        # Convert to numpy array based on sample width
        if sample_width == 1:
            dtype = np.uint8  # 8-bit audio
        elif sample_width == 2:
            dtype = np.int16  # 16-bit audio
        else:
            raise ValueError("Only supports 8 or 16 bit audio formats.")

        waveform = np.frombuffer(audio_frames, dtype=dtype)

        # If stereo, reshape
        if n_channels == 2:
            waveform = np.reshape(waveform, (n_frames, n_channels))
        
        return waveform, framerate