import numpy as np
import tensorflow as tf
import random as rn

## Set up random seed and session to reproduce the results
np.random.seed(42)
rn.seed(42)
tf.compat.v1.set_random_seed(11)
session_conf = tf.ConfigProto(intra_op_parallelism_threads=1, inter_op_parallelism_threads=1)
sess = tf.Session(graph=tf.get_default_graph(), config=session_conf)

from tensorflow import keras
from tensorflow.keras import models, layers, optimizers
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D
from tensorflow.keras.preprocessing.image import ImageDataGenerator, load_img
from tensorflow.keras.applications.inception_v3 import InceptionV3

train_dir = './flower-dataset/train'
validation_dir = './flower-dataset/validation'
image_size = 224
train_batchsize = 50
val_batchsize = 10

## Importing model and setting up top layers
base_model = InceptionV3(weights='imagenet', include_top=False)
top_layer = base_model.output
top_layer = GlobalAveragePooling2D()(top_layer)
top_layer = Dense(1024, activation='relu')(top_layer)
predictions = Dense(3, activation='softmax')(top_layer)

model = Model(inputs=base_model.input, outputs=predictions)

## Freezing base layers
for layer in base_model.layers:
    layer.trainable = False


## Setting up augmentations and importing training and validation data
train_datagen = ImageDataGenerator(
      rescale=1./255,
      rotation_range=60,
      width_shift_range=0.2,
      height_shift_range=0.2,
      horizontal_flip=True,
      fill_mode='nearest')
train_generator = train_datagen.flow_from_directory(
        train_dir,
        target_size=(image_size, image_size),
        batch_size=train_batchsize,
        class_mode='categorical')

validation_datagen = ImageDataGenerator(rescale=1./255)
validation_generator = validation_datagen.flow_from_directory(
        validation_dir,
        target_size=(image_size, image_size),
        batch_size=val_batchsize,
        class_mode='categorical',
        shuffle=False)

model.compile(optimizer='rmsprop', loss='categorical_crossentropy')

# Train the model
history = model.fit_generator(
      train_generator,
      epochs=2,
      validation_data=validation_generator,
      validation_steps=validation_generator.samples/validation_generator.batch_size,
      verbose=1)

# Run the model on validation dataset to calculate accuracy
validation_generator = validation_datagen.flow_from_directory(
        validation_dir,
        target_size=(image_size, image_size),
        batch_size=val_batchsize,
        class_mode='categorical',
        shuffle=False)

predictions = model.predict_generator(validation_generator, verbose=1)
predicted_classes = np.argmax(predictions, axis=1)

errors = np.where(predicted_classes != validation_generator.classes)[0]
print("Accuracy = {}".format(1-(len(errors)/validation_generator.samples)))

# Save the Model
model.save('finetunedInceptionModel.h5')

