from faster_whisper import WhisperModel

model_name_or_path = "whisper_model"

# Run on GPU with FP16
model = WhisperModel(model_name_or_path, device="cuda", compute_type="float16", device_index=[0,1])

# or run on GPU with INT8
# model = WhisperModel(model_size, device="cuda", compute_type="int8_float16")
# or run on CPU with INT8
# model = WhisperModel(model_size, device="cpu", compute_type="int8")

segments, info = model.transcribe("/opt/minuteman/audio/Nitay-5861bf5b.wav", vad_filter=True, beam_size=1, language="he", task="translate") # task="transcribe"

print("Detected language '%s' with probability %f" % (info.language, info.language_probability))

for segment in segments:
    print("[%.2fs -> %.2fs] %s" % (segment.start, segment.end, segment.text))
