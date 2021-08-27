import pickle
import pymorphy2

class NewbiesModel:

    def __init__(self):
        self.clf = None
        self.vectorizer = None
        self.morph = pymorphy2.MorphAnalyzer()
        self.trigger_words = ["помогите", "помощь", "курс", "новичок", "новенький", "книг", "совет", "учить", "учеба"]

    def upload_model(self, path: str):
        with open(path, "rb") as f:
            self.clf, self.vectorizer = pickle.load(f)

    def predict_senctence(self, text: str) -> int:
        triggers = [word for word in self.trigger_words if word in text]
        if len(triggers) == 0:
            return 0
        else:
            if (self.clf is None) | (self.vectorizer is None):
                raise ValueError("You need to teach the model first")
            else:
                new_word = [self.morph.parse(word)[0].normal_form for word in [text]]
                new_text_counts = self.vectorizer.transform(new_word)
                return self.clf.predict(new_text_counts)[0]
