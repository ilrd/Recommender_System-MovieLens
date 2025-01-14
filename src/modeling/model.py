from database.preparation import get_ratings_df
import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras.layers import *
from tensorflow.keras import Model
from sklearn.model_selection import train_test_split
import pandas as pd
import matplotlib.pyplot as plt
from tensorflow.keras import callbacks


def load_center_data(rows=None, build=False):
    datagen = get_ratings_df(rows)

    ratings_df = pd.concat(list(datagen))

    user_ids = ratings_df['userId'].values
    movie_ids = ratings_df['movieId'].values
    ratings = ratings_df['rating'].values

    train_user, test_user, train_movie, test_movie, train_ratings, test_ratings = train_test_split(user_ids, movie_ids,
                                                                                                   ratings,
                                                                                                   test_size=0.2,
                                                                                                   shuffle=True)
    ratings_mean = train_ratings.mean()
    train_ratings -= ratings_mean
    test_ratings -= ratings_mean

    if build:
        N = np.unique(user_ids).shape[0]
        M = np.unique(movie_ids).shape[0]

        return ([train_user, train_movie], train_ratings), ([test_user, test_movie], test_ratings), N, M

    return ([train_user, train_movie], train_ratings), ([test_user, test_movie], test_ratings)


def build_model(N, M):
    # Embedding dimension
    K = 5

    u = Input((1,))
    m = Input((1,))

    u_emb = Embedding(N, K)(u)
    m_emb = Embedding(M, K)(m)

    u_emb = Flatten()(u_emb)
    m_emb = Flatten()(m_emb)

    x = Concatenate()([u_emb, m_emb])

    x = Dense(1024, activation='relu')(x)
    x = Dropout(0.2)(x)
    x = Dense(256, activation='relu')(x)
    outputs = Dense(1)(x)

    model = Model([u, m], outputs)

    optimizer = keras.optimizers.Adam(lr=0.01)
    model.compile(optimizer, 'mse', 'mae')
    return model


def train(model, train_data, test_data):
    # Callbacks
    fit_callbacks = [
        callbacks.ReduceLROnPlateau(
            monitor='val_loss',
            factor=0.1,
            patience=2,
            verbose=1,
            min_lr=0.000001,
            min_delta=0.0003,
        ),
        callbacks.ModelCheckpoint(
            'modeling/checkpoints/model_checkpoint.h5',
            monitor='val_loss',
            verbose=0,
            save_best_only=True,
        ),
    ]

    history = model.fit(train_data[0], train_data[1], batch_size=3072, epochs=10,
                        validation_data=(test_data[0], test_data[1]), callbacks=fit_callbacks)

    plt.plot(history.history['loss'], label='loss')
    plt.plot(history.history['val_loss'], label='val_loss')

    # To save:
    # model.save('25epochs_model.h5')


train_data, test_data, N, M = load_center_data(build=True)
model = build_model(N, M)

train(model, train_data, train_data)

# Testing
# model = keras.models.load_model('25epochs_model.h5')
# model.evaluate(test_data[0], test_data[1], batch_size=3072)  # mae - 0.6109
