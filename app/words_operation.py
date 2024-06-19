
from vocabular import word_to_num_ua

def replace_words_with_numbers(sentence):
    words = sentence.split()
    for i, word in enumerate(words):
        if word in word_to_num_ua:
            words[i] = word_to_num_ua[word]
    return ' '.join(words)

