import vosk                 #pip install vosk
from sklearn.feature_extraction.text import CountVectorizer     #pip install scikit-learn
from sklearn.linear_model import LogisticRegression
import sounddevice as sd    #pip install sounddevice

import nltk
from nltk.stem import WordNetLemmatizer

import json
import queue

from words_operation import replace_words_with_numbers
import vocabular 
from interaction import *
import voice
from DB import *
from QR import *
from Order_recognition import FoodOrderParser

#print(get_menu_list())
q = queue.Queue()
parser = FoodOrderParser(get_menu_list())
#try_qr()

model = vosk.Model('model')       # голосова модель

device = sd.default.device  = 2,6     # <--- за замовчуванням
                                       #обо -> sd.default.device = 1, 3, python -m sounddevice просмотр 
samplerate = int(sd.query_devices(device[0], 'input')['default_samplerate'])  #отримуємо частоту мікрофону


#def t2():
#    return get_menu()

def callback(indata, frames, time, status):
    '''
     Додає в чергу семпли з потоку.
     викликається щоразу при наповненні blocksize
     в sd.RawInputStream'''

    q.put(bytes(indata))


def recognize(data, vectorizer, clf):
    '''
    Аналіз голосу
    '''
    #print("before", data)

    #проверяем есть ли имя бота в data, если нет, то return
    trg = vocabular.triggers.intersection(data.split())
    if not trg:
        return
    
    print("\nНеоброблене запитання:", data)

    #удаляем имя бота из текста
    data.replace(list(trg)[0], '')

    #получаем вектор полученного текста
    #сравниваем с вариантами, получая наиболее подходящий ответ
    text_vector = vectorizer.transform([data])

    predict_prob = clf.predict_proba(text_vector)
    trust = 0.15

    max_probability = max(predict_prob[0])
    print("Коефіцієнт схожості: ", max_probability)
    if max_probability >= trust:
        answer = clf.classes_[predict_prob[0].argmax()]
    else:
        voice.speaker("Команда не розпізнана")
        return


    #print("text_vector ", text_vector, "answer ", answer)

    #получение имени функции из ответа из data_set
    func_name = answer.split()[0]

    #озвучка ответа из модели data_set
    voice.speaker(answer.replace(func_name, ''))
    
    _, data = parser.parse_order(data)
    data = replace_words_with_numbers(data) # <-- Помилка
    print("Оброблене запитання:", data)

    if func_name in ['take_order', 'table_access_get', 'remove_from_order']:
        #print("data:", data)
        exec(func_name + '(data, parser)')
    else:
        #запуск функции из skills
        exec(func_name + '()')

    #print(total_order)

         
def main():
    '''
    Обучаем матрицу ИИ
    и постоянно слушаем микрофон
    '''
    voice.speaker('Готов до роботи')

    #Обучение матрицы на data_set модели
    vectorizer = CountVectorizer()

    vectors = vectorizer.fit_transform(list(vocabular.vocab.keys()))
    
    clf = LogisticRegression()
    clf.fit(vectors, list(vocabular.vocab.values()))

    del vocabular.vocab

    #постоянная прослушка микрофона
    with sd.RawInputStream(samplerate=samplerate, blocksize = 24000, device=device[0], dtype='int16',
                                channels=1, callback=callback):

        rec = vosk.KaldiRecognizer(model, samplerate)
        while True:
            data = q.get()
            if rec.AcceptWaveform(data):
                data = json.loads(rec.Result())['text']
                recognize(data, vectorizer, clf)
            # else:
            #     print(rec.PartialResult())


if __name__ == '__main__':
    main()