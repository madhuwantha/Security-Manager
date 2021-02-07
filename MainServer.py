from __future__ import print_function

import keras
from keras.models import Sequential, load_model
from keras.layers import Dense, Dropout, Flatten
from datetime import datetime
from keras.utils import to_categorical

import numpy as np
import pandas as pd
import glob
from os import path

from Env import Env


class FLModel:
    _env = Env()

    def __init__(self, epochs=10):
        """
        :param epochs:
        """
        self._x_train, self._y_train, self._x_val, self._y_val = self._processData()
        self._epochs = epochs
        self._model = None
        self._batch_size = self._env.get(key="batchSize")

    def _processData(self):
        x = pd.read_csv('LocalData/x.csv')
        y = pd.read_csv('LocalData/y.csv')

        y['0'] = y['0'].replace(['c-SCAN', 'c-LOGIN', 'c-CNC_COM', 'c-MAL_DOWN', 'c-DDOS'], [
            self._env.get(key="c-SCAN"),
            self._env.get(key="c-LOGIN"),
            self._env.get(key="c-CNC_COM"),
            self._env.get(key="c-MAL_DOWN"),
            self._env.get(key="c-DDOS")
        ])
        print(x.shape, y.shape)
        y = pd.DataFrame(to_categorical(y))

        return [], [], x, y

    def _loadModels(self):
        print("Loading client models...........")
        arr = []
        models = glob.glob("ClientModels/*.npy")
        for i in models:
            arr.append(np.load(i, allow_pickle=True))

        return np.array(arr)

    def _flAverage(self):
        print("Getting average .......")
        arr = self._loadModels()
        fl_avg = np.average(arr, axis=0)

        for i in fl_avg:
            print(i.shape)

        return fl_avg

    def _buildModel(self, avg):
        model = None
        with keras.backend.get_session().graph.as_default():
            if path.exists("PersistentStorage/agg_model.h5"):
                print("Agg model exists...\nLoading agg model...")
                model = load_model("PersistentStorage/agg_model.h5", compile=False)
            else:
                print("No agg _model found!\nBuilding _model...")
                model = Sequential()
                model.add(Dense(units=200, activation='relu', input_shape=[len(self._x_val.columns)]))
                model.add(Dense(500, activation='relu'))
                model.add(Dropout(0.8))
                model.add(Dense(1000, activation='relu'))
                model.add(Dropout(0.7))
                model.add(Dense(400, activation='relu'))
                model.add(Dropout(0.8))
                model.add(Dense(len(self._y_val.columns), activation='softmax'))

            print("****************************Model ready******************")

            model.set_weights(avg)

            model.compile(loss=keras.losses.categorical_crossentropy, optimizer=keras.optimizers.Adadelta(),
                          metrics=['accuracy'])

            print("****************************Complied******************")

        return model

    def _evaluateModel(self, model, x_test, y_test):
        print("********************Evaluating*******************")
        with keras.backend.get_session().graph.as_default():
            score = model.evaluate(x_test, y_test, verbose=0)
            print('Test loss:', score[0])
            print('Test accuracy:', score[1])
        print("********************Evaluated*******************")

    def _saveAggModel(self, model):
        with keras.backend.get_session().graph.as_default():
            model.save("PersistentStorage/agg_model.h5")
            now = datetime.now()
            now = str(now).replace(" ", "-").replace(":", "-").replace(".", "-")
            model.save('AggModel/model-' + now + "-saved.h5")
            print("Model written to storage!")

    def modelAggregation(self):
        _, _, x_test, y_test = self._processData()
        avg = self._flAverage()
        model = self._buildModel(avg)
        self._evaluateModel(model, x_test, y_test)
        self._saveAggModel(model)
        print("///////////////////////////////////////////////////////////////////")
