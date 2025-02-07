import asyncio
import io
import wave
from multiprocessing import Process, Value

import pyaudio
import romajitable
from RealtimeSTT import AudioToTextRecorder
from voicevox import Client

from transcript.eng_to_kana.eng_to_kana import EngToKana

# Zundamon: 1
# Lolita: 14
# Sora Mom: 15
# Voidoll: 89
# Zone-po: 90
# Tsurugi (Samurai): 94
speaker = Value("i", 1)
p = pyaudio.PyAudio()
output_index = list(
    filter(
        lambda device: device.get("maxOutputChannels") > 0
        and "CABLE Input" in device.get("name"),
        [
            p.get_device_info_by_host_api_device_index(0, i)
            for i in range(p.get_host_api_info_by_index(0).get("deviceCount"))
        ],
    )
)[0].get("index")


async def play_sound(text: str, speaker):
    eng_to_kana = EngToKana()
    words = (
        text.lower()
        .translate(str.maketrans(".,?", "##$"))
        .replace("#", " # ")
        .replace("$", " $ ")
        .split(" ")
    )
    print(f"{text = }")
    # print(f"{words = }")
    result = eng_to_kana.fromWordList(words)
    joined_words = "".join(
        [
            (romajitable.to_kana(words[i]).katakana if word[0] == "E_DIC" else word[0])
            for i, word in enumerate(result)
        ]
    )
    spaced_words = joined_words.replace("#", " ").replace("$", "？")
    print(f"Playing: {spaced_words}")

    client = Client()
    audio_query = await client.create_audio_query(spaced_words, speaker=speaker.value)
    audio_query.speed_scale = 1
    # audio_query.pitch_scale = -0.05
    audio = await audio_query.synthesis(speaker=speaker.value)
    with wave.open(io.BytesIO(audio)) as f:
        p = pyaudio.PyAudio()
        # open stream
        stream = p.open(
            format=p.get_format_from_width(f.getsampwidth()),
            channels=f.getnchannels(),
            rate=f.getframerate(),
            output=True,
            output_device_index=output_index,
        )
        data = f.readframes(1024)
        while data:
            stream.write(data)
            data = f.readframes(1024)
        stream.stop_stream()
        stream.close()
        p.terminate()
    await client.close()


async def process_text_async(text):
    await play_sound(text)


def process_text(text, speaker):
    # print(f"{speaker.value=}")
    asyncio.run(play_sound(text, speaker))


def start_listening(speaker):
    with AudioToTextRecorder(spinner=False, language="en") as recorder:
        print("Start listening thread")
        while True:
            recorder.text(lambda text: process_text(text, speaker))


async def main():
    p = Process(target=start_listening, args=(speaker,))
    p.start()
    
    # Not accurate
    # client = Client()
    # i = 0
    # for info_speaker in await Client().fetch_speakers():
    #     for style in info_speaker.styles:
    #         print(f"{i} - {info_speaker.name} ({style.name})")
    #         i += 1
    # await client.close()
    
    try:
        while text := input("Change speaker: "):
            speaker.value = int(text)
    except KeyboardInterrupt:
        p.terminate()


if __name__ == "__main__":
    asyncio.run(main())
