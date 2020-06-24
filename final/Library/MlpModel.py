from IModel import IModel
from IProcessor import IProcessor
from IDataset import IDataset

from Hurriyet import Hurriyet
from Aahaber import Aahaber
from Tweet3K import Tweet3K
from Tweet17K import Tweet17K
from Milliyet import Milliyet
from TurkishProcessor import TurkishProcessor
from helpers import get_external_stopwords, find_max_length
import tensorflow as tf
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Flatten, Embedding, Dropout
from tensorflow.keras.preprocessing import sequence
from tensorflow.keras.callbacks import TensorBoard
from tensorflow.keras.callbacks import ModelCheckpoint, EarlyStopping
from sklearn.model_selection import train_test_split
from sklearn import preprocessing
from keras.utils import to_categorical
import pickle


class MlpModel (IModel):

    EPOCHS = 30
    BATCH_SIZE = 100
    ACTIVATION = 'sigmoid'
    LOSSFUNC = 'binary_crossentropy'
    TEST_SIZE = 0.2
    NUM_WORDS = 1500

    def __init__(self, processor: IProcessor, dataset: IDataset):
        self.processor = processor
        self.dataset = dataset

    def evaluate(self):

        features = self.processor.process()
        #pickle.dump(features, open("bow.p", "wb"))
        #features = pickle.load(open("bow.p", "rb"))
        labels = self.dataset.getClasses()
        le = preprocessing.LabelEncoder()
        labels = le.fit_transform(labels)
        labels = to_categorical(labels)
        self.mlp_model(features, labels)

    def setParameters(self):
        pass

    def mlp_model(self, processed_features, labels):
        classes_num = self.dataset.getParameters()["classes_num"]
        X_train, X_test, y_train, y_test = train_test_split(
            processed_features, labels, test_size=self.TEST_SIZE, random_state=0)
        tokenizer = Tokenizer(num_words=self.NUM_WORDS)
        tokenizer.fit_on_texts(X_train)
        X_train = tokenizer.texts_to_sequences(X_train)
        X_test = tokenizer.texts_to_sequences(X_test)
        lenth = find_max_length(X_train)
        vocab_size = len(tokenizer.word_index) + 1
        X_train = pad_sequences(X_train, padding='post', maxlen=lenth)
        X_test = pad_sequences(X_test, padding='post', maxlen=lenth)
        model = Sequential()
        model.add(Embedding(vocab_size, 64, input_length=lenth))
        model.add(Flatten())
        model.add(Dense(4, activation='relu'))
        model.add(Dropout(0.4))
        model.add(Dense(classes_num, activation=self.ACTIVATION))
        model.compile(loss=self.LOSSFUNC, optimizer='adam',
                      metrics=['accuracy'])
        es_callback = EarlyStopping(
            monitor='val_loss', patience=3)
        model.summary()

        model.fit(X_train,
                  y_train,
                  validation_data=(X_test, y_test),
                  epochs=self.EPOCHS,
                  batch_size=self.BATCH_SIZE,
                  verbose=1, callbacks=[es_callback])

        predicted_sentiment = model.predict(X_test)
        scores = model.evaluate(X_test, y_test, verbose=1)
        print("Accuracy: %.2f%%" % (scores[1]*100))


H = Aahaber(False, False)
tp = TurkishProcessor(H)
mm = MlpModel(tp, H)
mm.evaluate()
