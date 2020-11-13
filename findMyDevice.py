import pyaudio
p = pyaudio.PyAudio()
stream = p.open(
    format=pyaudio.paInt16,
    channels=1,
    rate=44100,
    input=True,
    output=True,
    frames_per_buffer=2048
)

for i in range(p.get_device_count()):
    print(p.get_device_info_by_index(i))