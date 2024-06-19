import pyttsx3	


tts = pyttsx3.init()
tts.setProperty('rate', 200)				#скорость речи
tts.setProperty('voice', 'uk')

def speaker(text):
    tts.say(text)
    tts.runAndWait()

voices = tts.getProperty('voices')

for voice in voices:
    if voice.name == 'Anatol':
        tts.setProperty('voice', voice.id)
