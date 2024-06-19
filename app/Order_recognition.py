#from main import t2
import spacy
from word2number import w2n
nlp = spacy.load("uk_core_news_lg")
import re

#self.remove_words = ["бокал", "порція", "тарілка", "стакан", "кружка", "чашка", "келих"]

class FoodOrderParser:
    def __init__(self, menu):
        self.menu = {key.lower(): value for key, value in menu.items()}
        self.remove_words = ["бокал", "порція", "тарілка", "стакан", "кружка", "чашка", "келих"]

    def lemmatize_sentence(self, sentence):
        # Видаляємо вказані слова зі списку remove_words
        for word in self.remove_words:
            sentence = sentence.replace(word, "")

        doc = nlp(sentence)
        return ' '.join([token.lemma_ for token in doc])

    def parse_order(self, order):
        lemmatized_order = self.lemmatize_sentence(order)

        # Визначення правилових виразів для кількості та страв
        quantity_patterns = r"(\d+|один|два|три|чотири|п'ять)"
        dish_patterns = "|".join(re.escape(dish.lower()) for dish in self.menu.keys())
        combined_pattern = rf"({dish_patterns})\s*{quantity_patterns}|{quantity_patterns}\s*({dish_patterns})|({dish_patterns})"

        # Пошук відповідностей у замовленні
        matches = re.findall(combined_pattern, lemmatized_order.lower())

        # Обробка знайдених відповідностей
        dishes = {}
        for match in matches:
            dish = None
            quantity = 1  # Default quantity is 1

            if match[0] and match[1]:
                dish = match[0]
                quantity = match[1]
            elif match[2] and match[3]:
                dish = match[3]
                quantity = match[2]
            elif match[4]:
                dish = match[4]

            if isinstance(quantity, str) and quantity.isdigit():
                quantity = int(quantity)
            else:
                try:
                    quantity = w2n.word_to_num(quantity)
                except (ValueError, TypeError):
                    quantity = 1

            if dish in self.menu:
                if dish in dishes:
                    dishes[dish] += quantity
                else:
                    dishes[dish] = quantity

        return dishes, lemmatized_order

"""
def take_o(order):
    dishes, lemmatized_order = parser.parse_order(order)
    print("Замовлення:", lemmatized_order)
    print("Страви та їх кількості:", dishes)
    return dishes

parser = FoodOrderParser()
"""


