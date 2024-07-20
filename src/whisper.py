import torch
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
try:
    from src.read_wave import read_wave
    from src.resample import resample_16k_direct
    from src.openai_init import *
except ImportError:
    from read_wave import read_wave
    from resample import resample_16k_direct
    from openai_init import *

class TranscriptionModel:
    def __init__(self, local=False, model='large-v3'):
        self.local = local
        if self.local:
            # Setup for local model
            print(f"Starting local instance of whisper-{model}")
            if torch.cuda.is_available():
                print("GPU found...   using that shit for transcription.")
            self.device = "cuda:0" if torch.cuda.is_available() else "cpu"
            self.torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32
            self.model = AutoModelForSpeechSeq2Seq.from_pretrained(
                f"openai/whisper-{model}", 
                torch_dtype=self.torch_dtype, 
                low_cpu_mem_usage=True, 
                use_safetensors=True
            )
            self.model.to(self.device)
            self.processor = AutoProcessor.from_pretrained(f"openai/whisper-{model}")
            self.pipe = pipeline(
                "automatic-speech-recognition",
                model=self.model,
                tokenizer=self.processor.tokenizer,
                feature_extractor=self.processor.feature_extractor,
                max_new_tokens=128,
                chunk_length_s=30,
                batch_size=16,
                return_timestamps=True,
                torch_dtype=self.torch_dtype,
                device=self.device,
            )
        else:
            print("Using whisper via openai api.")
            self.client = client
            pass

    def transcribe(self, file):
        if self.local:
            sample, rate = read_wave(file)
            if rate != 16000:
                sample, rate = resample_16k_direct(file)
            result = self.pipe(sample)
        else:
            with open(file, "rb") as audio_file:
                result = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                )
        return result


if __name__ == '__main__':
    # Example of using the class
    transcriber = TranscriptionModel()  # Change to False to use remote transcription
    result = transcriber.transcribe("speech_segments/20240720_145550.wav")
    print(result)