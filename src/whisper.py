import torch
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
from elevenlabs import generate, play
import os
import librosa


def get_transcriber():
    device = "mps"
    torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

    model_id = "distil-whisper/distil-medium.en"

    model = AutoModelForSpeechSeq2Seq.from_pretrained(
        model_id, torch_dtype=torch_dtype, low_cpu_mem_usage=False, use_safetensors=True
    )
    model.to(device)

    processor = AutoProcessor.from_pretrained(model_id)

    transcriber = pipeline(
        "automatic-speech-recognition",
        model=model,
        tokenizer=processor.tokenizer,
        feature_extractor=processor.feature_extractor,
        max_new_tokens=128,
        torch_dtype=torch_dtype,
        device=device,
    )
    return transcriber

def transcribe_and_process(x, transcriber=None, rasa=None):
    sampling_rate, waveform = x
    print(waveform)

    waveform = waveform / 32678.0

    # convert to mono if stereo
    if len(waveform.shape) > 1:
        waveform = librosa.to_mono(waveform.T)

    # resample to 16 kHz if necessary
    if sampling_rate != 16000:
        waveform = librosa.resample(waveform, orig_sr=sampling_rate, target_sr=16000)

    # limit to 10 seconds
    waveform = waveform[:16000*10]

    print("Start speaking...")
    input_text = transcriber(waveform, generate_kwargs={"max_new_tokens": 128}) 
    print(input_text)
    print("---------------------------------------")
    output = rasa.process(query=input_text["text"])
    # feedback = rasa.generate_feedback(output)
    # audio = generate(
    #     text=feedback,
    #     voice="Bella",
    #     model="eleven_monolingual_v1"
    # )

    # play(audio)
    return " ".join([input_text["text"], output["response"]])

