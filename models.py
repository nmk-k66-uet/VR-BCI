#%%
import tensorflow as tf
import numpy as np
from tensorflow.keras.models import Model
from tensorflow.keras.layers import (Dense, Dropout, Activation, AveragePooling2D,
                                     Conv2D, SeparableConv2D, DepthwiseConv2D, BatchNormalization, 
                                     Reshape, Flatten, Add, Concatenate, 
                                     Input, GlobalAveragePooling2D, Multiply)
from tensorflow.keras.regularizers import l2
from tensorflow.keras.constraints import max_norm
from tensorflow.keras import backend as K
from tensorflow.keras.optimizers import Adam

def ComplexDBEEGNet_classifier(n_classes, Chans=22, Samples=1125, F1=8, D=2, kernLength=64, dropout_eeg=0.25):
    input1 = Input(shape = (2,Chans, Samples))   
    regRate=.25

    real_part = input1[:,0,:,:]
    imag_part = input1[:,1,:,:]
    real_part = Reshape((Chans, Samples, 1))(real_part)
    imag_part = Reshape((Chans, Samples, 1))(imag_part)

    eegnet_real = EEGNet(input_layer=real_part, F1=F1, kernLength=kernLength, D=D, Chans=Chans, dropout=dropout_eeg, prefix='real')
    eegnet_real = Flatten()(eegnet_real)

    eegnet_imag = EEGNet(input_layer=imag_part, F1=F1, kernLength=kernLength, D=D, Chans=Chans, dropout=dropout_eeg, prefix='imag')
    eegnet_imag = Flatten()(eegnet_imag)

    merged_features = Concatenate()([eegnet_real, eegnet_imag])

    dense = Dense(n_classes, name = 'dense',kernel_constraint = max_norm(regRate), kernel_regularizer=l2(0.01))(merged_features)
    softmax = Activation('softmax', name = 'softmax')(dense)

    return Model(inputs=input1, outputs=softmax)

def residual_block(x, filters, kernel_size, dropout_rate, prefix=''):
    shortcut = x
    x = Conv2D(filters, kernel_size, padding='same', use_bias=False, name=prefix+'res_conv1')(x)
    x = BatchNormalization(name=prefix+'res_bn1')(x)
    x = Activation('relu', name=prefix+'res_act1')(x)
    x = Dropout(dropout_rate, name=prefix+'res_dropout1')(x)

    x = Conv2D(filters, kernel_size, padding='same', use_bias=False, name=prefix+'res_conv2')(x)
    x = BatchNormalization(name=prefix+'res_bn2')(x)

    x = Add(name=prefix+'res_add')([x, shortcut])
    x = Activation('relu', name=prefix+'res_act2')(x)
    return x

def attention_block(x, prefix=''):
    channels = x.shape[-1]
    avg_pool = GlobalAveragePooling2D(name=prefix+'attn_gap')(x)
    avg_pool = Dense(channels // 16, activation='relu', name=prefix+'attn_dense1')(avg_pool)
    avg_pool = Dense(channels, activation='sigmoid', name=prefix+'attn_dense2')(avg_pool)
    avg_pool = Reshape((1, 1, channels), name=prefix+'attn_reshape')(avg_pool)
    
    x = Multiply(name=prefix+'attn_multiply')([x, avg_pool])
    return x

def EEGNet(input_layer, F1=32, kernLength=256, D=4, Chans=22, dropout=0.5, prefix=''):
    F2= F1*D
    block1 = Conv2D(F1, (kernLength, 1), padding = 'same',data_format='channels_last',use_bias = False)(input_layer)
    block1 = BatchNormalization(axis = -1)(block1)
    block1 = Activation('elu')(block1)
    block1 = Dropout(dropout)(block1)

    block1 = residual_block(block1, F1, (kernLength, 1), dropout, prefix)
    block1 = attention_block(block1, prefix)

    block2 = DepthwiseConv2D((1, Chans), use_bias = False, 
                                    depth_multiplier = D,
                                    data_format='channels_last',
                                    depthwise_constraint = max_norm(1.))(block1)
    block2 = BatchNormalization(axis = -1)(block2)
    block2 = Activation('elu')(block2)
    block2 = AveragePooling2D((2,1),data_format='channels_last')(block2)
    block2 = Dropout(dropout)(block2)

    block3 = SeparableConv2D(F2, (32, 1),
                            data_format='channels_last',
                            use_bias = False, padding = 'same')(block2)
    block3 = BatchNormalization(axis = -1)(block3)
    block3 = Activation('elu')(block3)
    block3 = AveragePooling2D((2,1),data_format='channels_last')(block3)
    block3 = Dropout(dropout)(block3)

    return block3