import torch
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
from transformers.pipelines.audio_utils import ffmpeg_microphone_live
import sys
import gradio as gr
import scipy.signal as sps
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

def transcribe(x):
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
    output = transcriber(waveform, generate_kwargs={"max_new_tokens": 128}) 

    return output

#transcribe()
input_audio = gr.Audio(
    sources = ["microphone"],
    waveform_options=gr.WaveformOptions(
        waveform_color="#01C6FF",
        waveform_progress_color="#0066B4",
        skip_length=2,
        show_controls=False,
    ),
)

transcriber = get_transcriber()
sampling_rate = transcriber.feature_extractor.sampling_rate
print('Sampling Rate:',  sampling_rate)
demo = gr.Interface(
    fn=transcribe,
    inputs=input_audio,
    outputs="text",
    cache_examples=False,
    live=True
)

if __name__ == "__main__":
    demo.launch()


"""
"let's" is a good trigger point
slides are implemented as page breaks in a markdown document

ex:
go to slide with a dog


interface functions

controls for GPT to change the slides
- jump_to_slide(int n) -> int

- produce_text(str text) -> str

controls for 
- get_existing_slides_md() -> str
- 
- retrieve_existing_text()    
"""