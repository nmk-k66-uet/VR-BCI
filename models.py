#%%
import tensorflow as tf
from tensorflow.keras.models import Model, Sequential
from tensorflow.keras.layers import (Dense, Dropout, Activation, AveragePooling2D, MaxPooling2D,
                                     Conv1D, Conv2D, SeparableConv2D, DepthwiseConv2D, BatchNormalization, 
                                     Reshape, LayerNormalization, Flatten, Add, Concatenate, Lambda, Input, 
                                     Permute, multiply, GlobalAveragePooling1D)
from tensorflow.keras.regularizers import L2
from tensorflow.keras.constraints import max_norm
from tensorflow.keras import backend as K
from attention_models import attention_block

#%% The proposed ATCNet model, https://doi.org/10.1109/TII.2022.3197419
def ATCNet_(n_classes, in_chans = 22, in_samples = 1125, n_windows = 5, attention = 'mha', 
           eegn_F1 = 16, eegn_D = 2, eegn_kernelSize = 64, eegn_poolSize = 7, eegn_dropout=0.3, 
           tcn_depth = 2, tcn_kernelSize = 4, tcn_filters = 32, tcn_dropout = 0.3, 
           tcn_activation = 'elu', fuse = 'average'):
    # sửa in_chans = 3, in_samples = 500
    """ ATCNet model from Altaheri et al 2023.
        See details at https://ieeexplore.ieee.org/abstract/document/9852687
    
        Notes
        -----
        The initial values in this model are based on the values identified by
        the authors
        
        References
        ----------
        .. H. Altaheri, G. Muhammad, and M. Alsulaiman. "Physics-informed 
           attention temporal convolutional network for EEG-based motor imagery 
           classification." IEEE Transactions on Industrial Informatics, 
           vol. 19, no. 2, pp. 2249-2258, (2023) 
           https://doi.org/10.1109/TII.2022.3197419
    """
    input_1 = Input(shape = (1,in_chans, in_samples))   #     TensorShape([None, 1, 22, 1125])
    input_2 = Permute((3,2,1))(input_1) 

    dense_weightDecay = 0.5  
    conv_weightDecay = 0.009
    conv_maxNorm = 0.6
    from_logits = False

    numFilters = eegn_F1
    F2 = numFilters*eegn_D

    block1 = Conv_block_(input_layer = input_2, F1 = eegn_F1, D = eegn_D, 
                        kernLength = eegn_kernelSize, poolSize = eegn_poolSize,
                        weightDecay = conv_weightDecay, maxNorm = conv_maxNorm,
                        in_chans = in_chans, dropout = eegn_dropout)
    block1 = Lambda(lambda x: x[:,:,-1,:])(block1)
       
    # Sliding window 
    sw_concat = []   # to store concatenated or averaged sliding window outputs
    for i in range(n_windows):
        st = i
        end = block1.shape[1]-n_windows+i+1
        block2 = block1[:, st:end, :]
        
        # Attention_model
        if attention is not None:
            if (attention == 'se' or attention == 'cbam'):
                block2 = Permute((2, 1))(block2) # shape=(None, 32, 16)
                block2 = attention_block(block2, attention)
                block2 = Permute((2, 1))(block2) # shape=(None, 16, 32)
            else: block2 = attention_block(block2, attention)

        # Temporal convolutional network (TCN)
        block3 = TCN_block_(input_layer = block2, input_dimension = F2, depth = tcn_depth,
                            kernel_size = tcn_kernelSize, filters = tcn_filters, 
                            weightDecay = conv_weightDecay, maxNorm = conv_maxNorm,
                            dropout = tcn_dropout, activation = tcn_activation)
        # Get feature maps of the last sequence
        block3 = Lambda(lambda x: x[:,-1,:])(block3)
        
        # Outputs of sliding window: Average_after_dense or concatenate_then_dense
        if(fuse == 'average'):
            sw_concat.append(Dense(n_classes, kernel_regularizer=L2(dense_weightDecay))(block3))
        elif(fuse == 'concat'):
            if i == 0:
                sw_concat = block3
            else:
                sw_concat = Concatenate()([sw_concat, block3])
                
    if(fuse == 'average'):
        if len(sw_concat) > 1: # more than one window
            sw_concat = tf.keras.layers.Average()(sw_concat[:])
        else: # one window (# windows = 1)
            sw_concat = sw_concat[0]
    elif(fuse == 'concat'):
        sw_concat = Dense(n_classes, kernel_regularizer=L2(dense_weightDecay))(sw_concat)
               
    if from_logits:  # No activation here because we are using from_logits=True
        out = Activation('linear', name = 'linear')(sw_concat)
    else:   # Using softmax activation
        out = Activation('softmax', name = 'softmax')(sw_concat)
       
    return Model(inputs = input_1, outputs = out)

#%% Convolutional (CV) block used in the ATCNet model
def Conv_block(input_layer, F1=4, kernLength=64, poolSize=8, D=2, in_chans=22, dropout=0.1):
    """ Conv_block
    
        Notes
        -----
        This block is the same as EEGNet with SeparableConv2D replaced by Conv2D 
        The original code for this model is available at: https://github.com/vlawhern/arl-eegmodels
        See details at https://arxiv.org/abs/1611.08024
    """
    F2= F1*D
    block1 = Conv2D(F1, (kernLength, 1), padding = 'same',data_format='channels_last',use_bias = False)(input_layer)
    block1 = BatchNormalization(axis = -1)(block1)
    block2 = DepthwiseConv2D((1, in_chans), use_bias = False, 
                                    depth_multiplier = D,
                                    data_format='channels_last',
                                    depthwise_constraint = max_norm(1.))(block1)
    block2 = BatchNormalization(axis = -1)(block2)
    block2 = Activation('elu')(block2)
    block2 = AveragePooling2D((8,1),data_format='channels_last')(block2)
    block2 = Dropout(dropout)(block2)
    block3 = Conv2D(F2, (16, 1),
                            data_format='channels_last',
                            use_bias = False, padding = 'same')(block2)
    block3 = BatchNormalization(axis = -1)(block3)
    block3 = Activation('elu')(block3)
    
    block3 = AveragePooling2D((poolSize,1),data_format='channels_last')(block3)
    block3 = Dropout(dropout)(block3)
    return block3

def Conv_block_(input_layer, F1=4, kernLength=64, poolSize=8, D=2, in_chans=22, 
                weightDecay = 0.009, maxNorm = 0.6, dropout=0.25):
    """ Conv_block
    
        Notes
        -----
        using  different regularization methods.
    """
    
    F2= F1*D
    block1 = Conv2D(F1, (kernLength, 1), padding = 'same', data_format='channels_last', 
                    kernel_regularizer=L2(weightDecay),
                    
                    # In a Conv2D layer with data_format="channels_last", the weight tensor has shape 
                    # (rows, cols, input_depth, output_depth), set axis to [0, 1, 2] to constrain 
                    # the weights of each filter tensor of size (rows, cols, input_depth).
                    kernel_constraint = max_norm(maxNorm, axis=[0,1,2]),
                    use_bias = False)(input_layer)
    block1 = BatchNormalization(axis = -1)(block1)  # bn_axis = -1 if data_format() == 'channels_last' else 1
    
    block2 = DepthwiseConv2D((1, in_chans),  
                             depth_multiplier = D,
                             data_format='channels_last',
                             depthwise_regularizer=L2(weightDecay),
                             depthwise_constraint  = max_norm(maxNorm, axis=[0,1,2]),
                             use_bias = False)(block1)
    block2 = BatchNormalization(axis = -1)(block2)
    block2 = Activation('elu')(block2)
    block2 = AveragePooling2D((8,1),data_format='channels_last')(block2)
    block2 = Dropout(dropout)(block2)
    
    block3 = Conv2D(F2, (16, 1),
                            data_format='channels_last',
                            kernel_regularizer=L2(weightDecay),
                            kernel_constraint = max_norm(maxNorm, axis=[0,1,2]),
                            use_bias = False, padding = 'same')(block2)
    block3 = BatchNormalization(axis = -1)(block3)
    block3 = Activation('elu')(block3)
    
    block3 = AveragePooling2D((poolSize,1),data_format='channels_last')(block3)
    block3 = Dropout(dropout)(block3)
    return block3

#%% Temporal convolutional (TC) block used in the ATCNet model
def TCN_block(input_layer,input_dimension,depth,kernel_size,filters,dropout,activation='relu'):
    """ TCN_block from Bai et al 2018
        Temporal Convolutional Network (TCN)
        
        Notes
        -----
        THe original code available at https://github.com/locuslab/TCN/blob/master/TCN/tcn.py
        This implementation has a slight modification from the original code
        and it is taken from the code by Ingolfsson et al at https://github.com/iis-eth-zurich/eeg-tcnet
        See details at https://arxiv.org/abs/2006.00622

        References
        ----------
        .. Bai, S., Kolter, J. Z., & Koltun, V. (2018).
           An empirical evaluation of generic convolutional and recurrent networks
           for sequence modeling.
           arXiv preprint arXiv:1803.01271.
    """    
    
    block = Conv1D(filters,kernel_size=kernel_size,dilation_rate=1,activation='linear',
                   padding = 'causal',kernel_initializer='he_uniform')(input_layer)
    block = BatchNormalization()(block)
    block = Activation(activation)(block)
    block = Dropout(dropout)(block)
    block = Conv1D(filters,kernel_size=kernel_size,dilation_rate=1,activation='linear',
                   padding = 'causal',kernel_initializer='he_uniform')(block)
    block = BatchNormalization()(block)
    block = Activation(activation)(block)
    block = Dropout(dropout)(block)
    if(input_dimension != filters):
        conv = Conv1D(filters,kernel_size=1,padding='same')(input_layer)
        added = Add()([block,conv])
    else:
        added = Add()([block,input_layer])
    out = Activation(activation)(added)
    
    for i in range(depth-1):
        block = Conv1D(filters,kernel_size=kernel_size,dilation_rate=2**(i+1),activation='linear',
                   padding = 'causal',kernel_initializer='he_uniform')(out)
        block = BatchNormalization()(block)
        block = Activation(activation)(block)
        block = Dropout(dropout)(block)
        block = Conv1D(filters,kernel_size=kernel_size,dilation_rate=2**(i+1),activation='linear',
                   padding = 'causal',kernel_initializer='he_uniform')(block)
        block = BatchNormalization()(block)
        block = Activation(activation)(block)
        block = Dropout(dropout)(block)
        added = Add()([block, out])
        out = Activation(activation)(added)
        
    return out

def TCN_block_(input_layer,input_dimension,depth,kernel_size,filters, dropout,
               weightDecay = 0.009, maxNorm = 0.6, activation='relu'):
    """ TCN_block from Bai et al 2018
        Temporal Convolutional Network (TCN)
        
        Notes
        -----
        using different regularization methods
    """    
    
    block = Conv1D(filters, kernel_size=kernel_size, dilation_rate=1, activation='linear',
                    kernel_regularizer=L2(weightDecay),
                    kernel_constraint = max_norm(maxNorm, axis=[0,1]),
                    
                    padding = 'causal',kernel_initializer='he_uniform')(input_layer)
    block = BatchNormalization()(block)
    block = Activation(activation)(block)
    block = Dropout(dropout)(block)
    block = Conv1D(filters,kernel_size=kernel_size,dilation_rate=1,activation='linear',
                    kernel_regularizer=L2(weightDecay),
                    kernel_constraint = max_norm(maxNorm, axis=[0,1]),

                    padding = 'causal',kernel_initializer='he_uniform')(block)
    block = BatchNormalization()(block)
    block = Activation(activation)(block)
    block = Dropout(dropout)(block)
    if(input_dimension != filters):
        conv = Conv1D(filters,kernel_size=1,
                    kernel_regularizer=L2(weightDecay),
                    kernel_constraint = max_norm(maxNorm, axis=[0,1]),
                      
                    padding='same')(input_layer)
        added = Add()([block,conv])
    else:
        added = Add()([block,input_layer])
    out = Activation(activation)(added)
    
    for i in range(depth-1):
        block = Conv1D(filters,kernel_size=kernel_size,dilation_rate=2**(i+1),activation='linear',
                    kernel_regularizer=L2(weightDecay),
                    kernel_constraint = max_norm(maxNorm, axis=[0,1]),
                    
                   padding = 'causal',kernel_initializer='he_uniform')(out)
        block = BatchNormalization()(block)
        block = Activation(activation)(block)
        block = Dropout(dropout)(block)
        block = Conv1D(filters,kernel_size=kernel_size,dilation_rate=2**(i+1),activation='linear',
                    kernel_regularizer=L2(weightDecay),
                    kernel_constraint = max_norm(maxNorm, axis=[0,1]),

                    padding = 'causal',kernel_initializer='he_uniform')(block)
        block = BatchNormalization()(block)
        block = Activation(activation)(block)
        block = Dropout(dropout)(block)
        added = Add()([block, out])
        out = Activation(activation)(added)
        
    return out


#%% Reproduced TCNet_Fusion model: https://doi.org/10.1016/j.bspc.2021.102826
def TCNet_Fusion(n_classes, Chans=22, Samples=1125, layers=2, kernel_s=4, filt=12,
                 dropout=0.3, activation='elu', F1=24, D=2, kernLength=32, dropout_eeg=0.3):
    """ TCNet_Fusion model from Musallam et al 2021.
    See details at https://doi.org/10.1016/j.bspc.2021.102826
    
        Notes
        -----
        The initial values in this model are based on the values identified by
        the authors
        
        References
        ----------
        .. Musallam, Y.K., AlFassam, N.I., Muhammad, G., Amin, S.U., Alsulaiman,
           M., Abdul, W., Altaheri, H., Bencherif, M.A. and Algabri, M., 2021. 
           Electroencephalography-based motor imagery classification
           using temporal convolutional network fusion. 
           Biomedical Signal Processing and Control, 69, p.102826.
    """
    input1 = Input(shape = (1,Chans, Samples))
    input2 = Permute((3,2,1))(input1)
    regRate=.25

    numFilters = F1
    F2= numFilters*D
    
    EEGNet_sep = EEGNet(input_layer=input2,F1=F1,kernLength=kernLength,D=D,Chans=Chans,dropout=dropout_eeg)
    block2 = Lambda(lambda x: x[:,:,-1,:])(EEGNet_sep)
    FC = Flatten()(block2) 

    outs = TCN_block(input_layer=block2,input_dimension=F2,depth=layers,kernel_size=kernel_s,filters=filt,dropout=dropout,activation=activation)

    Con1 = Concatenate()([block2,outs]) 
    out = Flatten()(Con1) 
    Con2 = Concatenate()([out,FC]) 
    dense        = Dense(n_classes, name = 'dense',kernel_constraint = max_norm(regRate))(Con2)
    softmax      = Activation('softmax', name = 'softmax')(dense)
    
    return Model(inputs=input1,outputs=softmax)

#%% Reproduced EEGTCNet model: https://arxiv.org/abs/2006.00622
def EEGTCNet(n_classes, Chans=22, Samples=1125, layers=2, kernel_s=4, filt=12, dropout=0.3, activation='elu', F1=8, D=2, kernLength=32, dropout_eeg=0.2):
    """ EEGTCNet model from Ingolfsson et al 2020.
    See details at https://arxiv.org/abs/2006.00622
    
    The original code for this model is available at https://github.com/iis-eth-zurich/eeg-tcnet
    
        Notes
        -----
        The initial values in this model are based on the values identified by the authors
        
        References
        ----------
        .. Ingolfsson, T. M., Hersche, M., Wang, X., Kobayashi, N.,
           Cavigelli, L., & Benini, L. (2020, October). 
           Eeg-tcnet: An accurate temporal convolutional network
           for embedded motor-imagery brain–machine interfaces. 
           In 2020 IEEE International Conference on Systems, 
           Man, and Cybernetics (SMC) (pp. 2958-2965). IEEE.
    """
    input1 = Input(shape = (1,Chans, Samples))
    input2 = Permute((3,2,1))(input1)
    regRate=.25
    numFilters = F1
    F2= numFilters*D

    EEGNet_sep = EEGNet(input_layer=input2,F1=F1,kernLength=kernLength,D=D,Chans=Chans,dropout=dropout_eeg)
    block2 = Lambda(lambda x: x[:,:,-1,:])(EEGNet_sep)
    outs = TCN_block(input_layer=block2,input_dimension=F2,depth=layers,kernel_size=kernel_s,filters=filt,dropout=dropout,activation=activation)
    out = Lambda(lambda x: x[:,-1,:])(outs)
    dense        = Dense(n_classes, name = 'dense',kernel_constraint = max_norm(regRate))(out)
    softmax      = Activation('softmax', name = 'softmax')(dense)
    
    return Model(inputs=input1,outputs=softmax)

#%% Reproduced MBEEG_SENet model: https://doi.org/10.3390/diagnostics12040995
def MBEEG_SENet(nb_classes, Chans, Samples, D=2):
    """ MBEEG_SENet model from Altuwaijri et al 2022.
    See details at https://doi.org/10.3390/diagnostics12040995
    
        Notes
        -----
        The initial values in this model are based on the values identified by
        the authors
        
        References
        ----------
        .. G. Altuwaijri, G. Muhammad, H. Altaheri, & M. Alsulaiman. 
           A Multi-Branch Convolutional Neural Network with Squeeze-and-Excitation 
           Attention Blocks for EEG-Based Motor Imagery Signals Classification. 
           Diagnostics, 12(4), 995, (2022).  
           https://doi.org/10.3390/diagnostics12040995
    """

    input1 = Input(shape = (1,Chans, Samples))
    input2 = Permute((3,2,1))(input1)
    regRate=.25

    EEGNet_sep1 = EEGNet(input_layer=input2, F1=4, kernLength=16, D=D, Chans=Chans, dropout=0)
    EEGNet_sep2 = EEGNet(input_layer=input2, F1=8, kernLength=32, D=D, Chans=Chans, dropout=0.1)
    EEGNet_sep3 = EEGNet(input_layer=input2, F1=16, kernLength=64, D=D, Chans=Chans, dropout=0.2)

    SE1 = attention_block(EEGNet_sep1, 'se', ratio=4)
    SE2 = attention_block(EEGNet_sep2, 'se', ratio=4)
    SE3 = attention_block(EEGNet_sep3, 'se', ratio=2)

  
    FC1 = Flatten()(SE1)
    FC2 = Flatten()(SE2)
    FC3 = Flatten()(SE3)

    CON = Concatenate()([FC1,FC2,FC3])
   
    dense1 = Dense(nb_classes, name = 'dense1',kernel_constraint = max_norm(regRate))(CON)
    softmax = Activation('softmax', name = 'softmax')(dense1)
    
    return Model(inputs=input1,outputs=softmax)

#%% Reproduced EEGNeX model: https://arxiv.org/abs/2207.12369
def EEGNeX_8_32(n_timesteps, n_features, n_outputs):
    """ EEGNeX model from Chen et al 2022.
    See details at https://arxiv.org/abs/2207.12369
    
    The original code for this model is available at https://github.com/chenxiachan/EEGNeX
           
        References
        ----------
        .. Chen, X., Teng, X., Chen, H., Pan, Y., & Geyer, P. (2022).
           Toward reliable signals decoding for electroencephalogram: 
           A benchmark study to EEGNeX. arXiv preprint arXiv:2207.12369.
    """

    model = Sequential()
    model.add(Input(shape=(1, n_features, n_timesteps)))

    model.add(Conv2D(filters=8, kernel_size=(1, 32), use_bias = False, padding='same', data_format="channels_first"))
    model.add(LayerNormalization())
    model.add(Activation(activation='elu'))
    model.add(Conv2D(filters=32, kernel_size=(1, 32), use_bias = False, padding='same', data_format="channels_first"))
    model.add(LayerNormalization())
    model.add(Activation(activation='elu'))

    model.add(DepthwiseConv2D(kernel_size=(n_features, 1), depth_multiplier=2, use_bias = False, depthwise_constraint=max_norm(1.), data_format="channels_first"))
    model.add(LayerNormalization())
    model.add(Activation(activation='elu'))
    model.add(AveragePooling2D(pool_size=(1, 4), padding='same', data_format="channels_first"))
    model.add(Dropout(0.5))

    
    model.add(Conv2D(filters=32, kernel_size=(1, 16), use_bias = False, padding='same', dilation_rate=(1, 2), data_format='channels_first'))
    model.add(LayerNormalization())
    model.add(Activation(activation='elu'))
    
    model.add(Conv2D(filters=8, kernel_size=(1, 16), use_bias = False, padding='same', dilation_rate=(1, 4),  data_format='channels_first'))
    model.add(LayerNormalization())
    model.add(Activation(activation='elu'))
    model.add(Dropout(0.5))
    
    model.add(Flatten())
    model.add(Dense(n_outputs, kernel_constraint=max_norm(0.25)))
    model.add(Activation(activation='softmax'))
    
    # save a plot of the model
    # plot_model(model, show_shapes=True, to_file='EEGNeX_8_32.png')
    model.compile(loss='categorical_crossentropy', optimizer='adam', metrics=['accuracy'])
    return model 

#%% Reproduced EEGNet model: https://arxiv.org/abs/1611.08024
def EEGNet_classifier(n_classes, Chans=22, Samples=1125, F1=8, D=2, kernLength=64, dropout_eeg=0.25):
    input1 = Input(shape = (1,Chans, Samples))   
    input2 = Permute((3,2,1))(input1) 
    regRate=.25

    eegnet = EEGNet(input_layer=input2, F1=F1, kernLength=kernLength, D=D, Chans=Chans, dropout=dropout_eeg)
    eegnet = Flatten()(eegnet)
    dense = Dense(n_classes, name = 'dense',kernel_constraint = max_norm(regRate))(eegnet)
    softmax = Activation('softmax', name = 'softmax')(dense)
    
    return Model(inputs=input1, outputs=softmax)

def EEGNet(input_layer, F1=8, kernLength=64, D=2, Chans=22, dropout=0.25):
    """ EEGNet model from Lawhern et al 2018
    See details at https://arxiv.org/abs/1611.08024
    
    The original code for this model is available at: https://github.com/vlawhern/arl-eegmodels
    
        Notes
        -----
        The initial values in this model are based on the values identified by the authors
        
        References
        ----------
        .. Lawhern, V. J., Solon, A. J., Waytowich, N. R., Gordon,
           S. M., Hung, C. P., & Lance, B. J. (2018).
           EEGNet: A Compact Convolutional Network for EEG-based
           Brain-Computer Interfaces.
           arXiv preprint arXiv:1611.08024.
    """
    F2= F1*D
    block1 = Conv2D(F1, (kernLength, 1), padding = 'same',data_format='channels_last',use_bias = False)(input_layer)
    block1 = BatchNormalization(axis = -1)(block1)
    block2 = DepthwiseConv2D((1, Chans), use_bias = False, 
                                    depth_multiplier = D,
                                    data_format='channels_last',
                                    depthwise_constraint = max_norm(1.))(block1)
    block2 = BatchNormalization(axis = -1)(block2)
    block2 = Activation('elu')(block2)
    block2 = AveragePooling2D((8,1),data_format='channels_last')(block2)
    block2 = Dropout(dropout)(block2)
    block3 = SeparableConv2D(F2, (16, 1),
                            data_format='channels_last',
                            use_bias = False, padding = 'same')(block2)
    block3 = BatchNormalization(axis = -1)(block3)
    block3 = Activation('elu')(block3)
    block3 = AveragePooling2D((8,1),data_format='channels_last')(block3)
    block3 = Dropout(dropout)(block3)
    return block3

#%% Reproduced DeepConvNet model: https://doi.org/10.1002/hbm.23730
def DeepConvNet(nb_classes, Chans = 64, Samples = 256,
                dropoutRate = 0.5):
    """ Keras implementation of the Deep Convolutional Network as described in
    Schirrmeister et. al. (2017), Human Brain Mapping.
    See details at https://onlinelibrary.wiley.com/doi/full/10.1002/hbm.23730
    
    The original code for this model is available at: https://github.com/braindecode/braindecode

        Notes
        -----
        The initial values in this model are based on the values identified by the authors

        This implementation is taken from code by the Army Research Laboratory (ARL) 
        at https://github.com/vlawhern/arl-eegmodels
       
        References
        ----------
        .. Schirrmeister, R. T., Springenberg, J. T., Fiederer, L. D. J., 
           Glasstetter, M., Eggensperger, K., Tangermann, M., ... & Ball, T. (2017). 
           Deep learning with convolutional neural networks for EEG decoding 
           and visualization. Human brain mapping, 38(11), 5391-5420.

    """

    # start the model
    # input_main   = Input((Chans, Samples, 1))
    input_main   = Input((1, Chans, Samples))
    input_2 = Permute((2,3,1))(input_main) 
    
    block1       = Conv2D(25, (1, 10), 
                                 input_shape=(Chans, Samples, 1),
                                 kernel_constraint = max_norm(2., axis=(0,1,2)))(input_2)
    block1       = Conv2D(25, (Chans, 1),
                                 kernel_constraint = max_norm(2., axis=(0,1,2)))(block1)
    block1       = BatchNormalization(epsilon=1e-05, momentum=0.9)(block1)
    block1       = Activation('elu')(block1)
    block1       = MaxPooling2D(pool_size=(1, 3), strides=(1, 3))(block1)
    block1       = Dropout(dropoutRate)(block1)
  
    block2       = Conv2D(50, (1, 10),
                                 kernel_constraint = max_norm(2., axis=(0,1,2)))(block1)
    block2       = BatchNormalization(epsilon=1e-05, momentum=0.9)(block2)
    block2       = Activation('elu')(block2)
    block1       = MaxPooling2D(pool_size=(1, 3), strides=(1, 3))(block1)
    block2       = Dropout(dropoutRate)(block2)
    
    block3       = Conv2D(100, (1, 10),
                                 kernel_constraint = max_norm(2., axis=(0,1,2)))(block2)
    block3       = BatchNormalization(epsilon=1e-05, momentum=0.9)(block3)
    block3       = Activation('elu')(block3)
    block1       = MaxPooling2D(pool_size=(1, 3), strides=(1, 3))(block1)
    block3       = Dropout(dropoutRate)(block3)
    
    block4       = Conv2D(200, (1, 10),
                                 kernel_constraint = max_norm(2., axis=(0,1,2)))(block3)
    block4       = BatchNormalization(epsilon=1e-05, momentum=0.9)(block4)
    block4       = Activation('elu')(block4)
    block1       = MaxPooling2D(pool_size=(1, 3), strides=(1, 3))(block1)
    block4       = Dropout(dropoutRate)(block4)
    
    flatten      = Flatten()(block4)
    
    dense        = Dense(nb_classes, kernel_constraint = max_norm(0.5))(flatten)
    softmax      = Activation('softmax')(dense)
    
    return Model(inputs=input_main, outputs=softmax)

#%% need these for ShallowConvNet
def square(x):
    return K.square(x)

def log(x):
    return K.log(K.clip(x, min_value = 1e-7, max_value = 10000))  

#%% Reproduced ShallowConvNet model: https://doi.org/10.1002/hbm.23730
def ShallowConvNet(nb_classes, Chans = 64, Samples = 128, dropoutRate = 0.5):
    """ Keras implementation of the Shallow Convolutional Network as described
    in Schirrmeister et. al. (2017), Human Brain Mapping.
    See details at https://onlinelibrary.wiley.com/doi/full/10.1002/hbm.23730
       
    The original code for this model is available at: https://github.com/braindecode/braindecode

        Notes
        -----
        The initial values in this model are based on the values identified by the authors

        This implementation is taken from code by the Army Research Laboratory (ARL) 
        at https://github.com/vlawhern/arl-eegmodels
       
        References
        ----------
        .. Schirrmeister, R. T., Springenberg, J. T., Fiederer, L. D. J., 
           Glasstetter, M., Eggensperger, K., Tangermann, M., ... & Ball, T. (2017). 
           Deep learning with convolutional neural networks for EEG decoding 
           and visualization. Human brain mapping, 38(11), 5391-5420.

    """
    # start the model
    # input_main   = Input((Chans, Samples, 1))
    input_main   = Input((1, Chans, Samples))
    input_2 = Permute((2,3,1))(input_main) 

    block1       = Conv2D(40, (1, 25), 
                                 input_shape=(Chans, Samples, 1),
                                 kernel_constraint = max_norm(2., axis=(0,1,2)))(input_2)
    block1       = Conv2D(40, (Chans, 1), use_bias=False, 
                          kernel_constraint = max_norm(2., axis=(0,1,2)))(block1)
    block1       = BatchNormalization(epsilon=1e-05, momentum=0.9)(block1)
    block1       = Activation(square)(block1)
    block1       = AveragePooling2D(pool_size=(1, 75), strides=(1, 15))(block1)
    block1       = Activation(log)(block1)
    block1       = Dropout(dropoutRate)(block1)
    flatten      = Flatten()(block1)
    dense        = Dense(nb_classes, kernel_constraint = max_norm(0.5))(flatten)
    softmax      = Activation('softmax')(dense)
    
    return Model(inputs=input_main, outputs=softmax)

#%% EEG-DBNet: https://arxiv.org/pdf/2405.16090v3
def LC_Block(input_layer, F1=8, kernLength=64, D=2, Chans=22, dropout=0.25, activation='elu', AveragePooling=True):
    conv_block1 = Conv2D(F1, kernel_size=(1, kernLength), padding='same', data_format='channels_first',
                         use_bias=False)(input_layer)
    conv_block1 = BatchNormalization(axis=1)(conv_block1)

    conv_block2 = DepthwiseConv2D(kernel_size=(Chans, 1), depth_multiplier=D, data_format='channels_first',
                                  use_bias=False, depthwise_constraint=max_norm(1.))(conv_block1)
    conv_block2 = BatchNormalization(axis=1)(conv_block2)
    conv_block2 = Activation(activation)(conv_block2)
    if AveragePooling:
        conv_block2 = AveragePooling2D(pool_size=(1, kernLength / 8), data_format='channels_first')(conv_block2)
    else:
        conv_block2 = MaxPooling2D(pool_size=(1, kernLength / 8), data_format='channels_first')(conv_block2)
    conv_block2 = Dropout(dropout)(conv_block2)

    conv_block3 = SeparableConv2D(F1*D, kernel_size=(1, kernLength // 4), padding='same', data_format='channels_first',
                                  use_bias=False)(conv_block2)
    conv_block3 = BatchNormalization(axis=1)(conv_block3)
    conv_block3 = Activation(activation)(conv_block3)
    if AveragePooling:
        conv_block3 = AveragePooling2D(pool_size=(1, kernLength / 8), data_format='channels_first')(conv_block3)
    else:
        conv_block3 = MaxPooling2D(pool_size=(1, kernLength / 8), data_format='channels_first')(conv_block3)

    conv_block3 = Dropout(dropout)(conv_block3)
    conv_block3 = K.squeeze(conv_block3, axis=-2)

    return conv_block3

def SE_Block(input_layer, Seize=2, activation1='relu', activation2='sigmoid', BandSE=True):
    if BandSE: # (32, 17)
        aver_block = GlobalAveragePooling1D(data_format='channels_first')(input_layer) # (32)
        bands = input_layer.shape[1]
        aver_block = Reshape((1, bands))(aver_block) # (1, 32)
        se_block = Dense(Seize, activation=activation1, kernel_initializer='he_normal', use_bias=True,
                         bias_initializer='zeros')(aver_block) # (1, 2)
        se_block = Dense(bands, activation=activation2, kernel_initializer='he_normal', use_bias=True,
                         bias_initializer='zeros')(se_block) # (1, 32)
        se_block = Permute((2, 1))(se_block) # (32, 1)
    else: # (16, 31)
        aver_block = GlobalAveragePooling1D(data_format='channels_last')(input_layer) # (31)
        timePoints = input_layer.shape[2]
        aver_block = Reshape((1, timePoints))(aver_block) # (1, 31)
        se_block = Dense(Seize, activation=activation1, kernel_initializer='he_normal', use_bias=True,
                         bias_initializer='zeros')(aver_block) # (1, 2)
        se_block = Dense(timePoints, activation=activation2, kernel_initializer='he_normal', use_bias=True,
                         bias_initializer='zeros')(se_block) # (1, 31)

    se_block = multiply([input_layer, se_block])

    return se_block

def GC_Block(input_layer, dropout=0.3, depth=2, activation='elu', kernel_size=4, TimeConv=True, n_windows=5, step=4,
             seize=2):
    F1 = input_layer.shape[1]
    F2 = input_layer.shape[2]
    sw_concat = []

    if TimeConv:  # (16, 31)
        for j in range(n_windows):
            st = j * step
            end = F2 - (n_windows - j - 1) * step
            sw = input_layer[:, :, st:end]
            se_block = SE_Block(input_layer=sw, BandSE=False, Seize=seize, activation1='relu')
            last_block = se_block
            for i in range(depth):
                block_1 = Conv1D(F1, kernel_size=kernel_size, dilation_rate=i+1, padding='causal',
                                 kernel_initializer='he_uniform', data_format='channels_first')(last_block)
                block_1 = BatchNormalization(axis=1)(block_1)
                block_1 = Activation(activation)(block_1)
                block_1 = Dropout(dropout)(block_1)
                add_block = Add()([block_1, se_block])
                last_block = Activation(activation)(add_block)
            fl_block = Flatten()(last_block)
            sw_concat.append(fl_block)
        ca_block = Concatenate()(sw_concat)

    else: # (32, 17)
        for j in range(n_windows):
            st = j * step
            end = F1 - (n_windows - j - 1) * step
            sw = input_layer[:, st:end, :]
            se_block = SE_Block(input_layer=sw, BandSE=True, Seize=seize, activation1='relu')
            last_block = se_block
            for i in range(depth):
                block_1 = Conv1D(F2, kernel_size=kernel_size, dilation_rate=i+1, padding='causal',
                                 kernel_initializer='he_uniform', data_format='channels_last')(last_block)
                block_1 = BatchNormalization(axis=-1)(block_1)
                block_1 = Activation(activation)(block_1)
                block_1 = Dropout(dropout)(block_1)
                add_block = Add()([block_1, se_block])
                last_block = Activation(activation)(add_block)
            fl_block = Flatten()(last_block)
            sw_concat.append(fl_block)
        ca_block = Concatenate()(sw_concat)

    return ca_block

def EEG_DBNet(nb_classes=4, Chans=22, Samples=1125, regRate=0.25, d=4, k=4, n=6, s=1, se=2):
    inputs = Input(shape=(1, Chans, Samples))

    LC_Block1 = LC_Block(input_layer=inputs, F1=8, kernLength=48, Chans=Chans, dropout=0.3, activation='elu',
                         AveragePooling=True) # (16, 31)
    LC_Block2 = LC_Block(input_layer=inputs, F1=16, kernLength=64, Chans=Chans, dropout=0.3, activation='elu',
                         AveragePooling=False) # (32, 17)

    GC_Block1 = GC_Block(input_layer=LC_Block1, TimeConv=True, depth=d, kernel_size=k, n_windows=n, step=s,
                         seize=se, activation='elu')
    GC_Block2 = GC_Block(input_layer=LC_Block2, TimeConv=False, depth=d, kernel_size=k, n_windows=n, step=s,
                         seize=se, activation='elu')

    conc_block = Concatenate()([GC_Block1, GC_Block2]) # 512

    dense_block = Dense(nb_classes, kernel_constraint=max_norm(regRate))(conc_block)
    softmax = Activation('softmax')(dense_block)

    return Model(inputs=inputs, outputs=softmax)
