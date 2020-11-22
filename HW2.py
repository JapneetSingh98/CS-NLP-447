# -*- coding: utf-8 -*-
"""HW2 (1).ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1n0j9BJfV38FJ68BQaUS98B-jiXW3SVzd

# CS447 - Assignment 2

In this part of assignment 2 we'll be building a machine learning model to detect the sentiment of movie reviews using the Stanford Sentiment Treebank([SST])(http://ai.stanford.edu/~amaas/data/sentiment/) dataset. First we will import all the required libraries. We highly recommend that you finish the PyTorch Tutorials [ 1 ](https://pytorch.org/tutorials/beginner/pytorch_with_examples.html),[ 2 ](https://pytorch.org/tutorials/beginner/data_loading_tutorial.html),[ 3 ](https://github.com/yunjey/pytorch-tutorial) before starting this assignment. 

After finishing this assignment you will able to answer the following questions:
* How to write Dataloaders in Pytorch?
* How to build dictionaries and vocabularies for Deep Nets?
* How to use Embedding Layers in Pytorch?
* How to use a Convolutional Neural Network for  sentiment analysis?
* How to build various recurrent models (LSTMs and GRUs) for sentiment analysis?
* How to use packed_padded_sequences for sequential models?
Please make sure that you have selected "GPU" as the Hardware accelerator from Runtime -> Change runtime type.

## Import Libraries
"""

# Don't import any other libraries
from collections import defaultdict
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.nn.utils.rnn import pack_padded_sequence, pad_packed_sequence
import torch.optim as optim
from torchtext import data, datasets

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

if __name__=='__main__':
    print('Using device:', device)

"""## Download dataset
First we will download the dataset using [torchtext](https://torchtext.readthedocs.io/en/latest/index.html), which is a package that supports NLP for PyTorch. The following command will get you 3 objects `train_data`, `val_data` and `test_data`. To access the data:

*   To access list of textual tokens - `train_data[0].text`
*   To access label - `train_data[0].label`
"""

if __name__=='__main__':
    train_data, val_data, test_data = datasets.SST.splits(data.Field(tokenize = 'spacy'), data.LabelField(dtype = torch.float), filter_pred=lambda ex: ex.label != 'neutral')

    print('{:d} train and {:d} test samples'.format(len(train_data), len(test_data)))

    print('Sample text:', train_data[0].text)
    print('Sample label:', train_data[0].label)

"""# 1. Define the Dataset Class (4 points)

In the following cell, we will define the dataset class. You need to implement the following functions: 


*   ` build_dictionary() ` - creates the dictionaries `ixtoword` and `wordtoix`. Converts all the text of all examples, in the form of text ids and stores them in `textual_ids`. If a word is not present in your dictionary, it should use `<unk>`. Use the hyperparameter `THRESHOLD` to control which words appear in the dictionary, based on their frequency in the training data. Note that a word’s frequency should be `>=THRESHOLD` to be included in the dictionary. Also make sure that `<end>` should be at idx 0, and `<unk>` should be at idx 1

*   ` get_label() ` - This function should return the value `1` if the label in the dataset is `positive`, and should return `0` if it is `negative`. The data type for the returned item should be `torch.LongTensor`

*   ` get_text() ` - This function should pad the review with `<end>` character up to a length of `MAX_LEN` if the length of the text is less than the `MAX_LEN`. If length is more than `MAX_LEN` then it should only return the first `MAX_LEN` words. This function should also return the original length of the review. The data type for the returned items should be `torch.LongTensor`. Note that the text returned is a list of indices of the words from your `wordtoix` mapping

*   ` __len__() ` - This function should return the total length (int value) of the dataset i.e. the number of sentences

*   ` __getitem__() ` - This function should return the padded text, the length of the text (without the padding) and the label. The data type for all the returned items should be `torch.LongTensor`. You will use the ` get_label() ` and ` get_text() ` functions here

NOTE: Don't forget to convert all text to lowercase!
"""

THRESHOLD = 10
MAX_LEN = 60
UNK = '<unk>'
END = '<end>'

class TextDataset(data.Dataset):
    def __init__(self, examples, split, ixtoword=None, wordtoix=None, THRESHOLD=THRESHOLD, MAX_LEN=MAX_LEN):
        self.examples = examples
        self.split = split
        self.ixtoword = ixtoword
        self.wordtoix = wordtoix
        self.THRESHOLD = THRESHOLD
        self.MAX_LEN = MAX_LEN

        self.build_dictionary()
        
        ##### TODO : set this to the number of words in your vocabulary
        self.vocab_size = len(self.wordtoix)
        
        self.textual_ids = []
        self.labels = []
        
        ##### TODO #####
        # textual_ids contains list of word ids as per wordtoix for all sentences
        #   Replace words out of vocabulary with id of UNK token
        # labels is a list of integer labels (0 or 1) for all sentences
        for i in range(len(examples)):
            self.textual_ids.append([])
            current = self.textual_ids[i]
            line = examples[i]
            for word in line.text:
                wordLower = word.lower()
                if word not in self.wordtoix:
                    current.append(self.wordtoix[UNK])
                else:
                    current.append(self.wordtoix[wordLower])
            self.labels.append(self.get_label(i))
        
        
    def build_dictionary(self): 
        # This is built only from train dataset and then reused in test dataset 
        # by passing ixtoword and wordtoix from train dataset to __init__() when creating test dataset
        # which is done under 'Initialize the Dataloader' section
        if self.split.lower() != 'train':
            return
        
        # END should be at idx 0. UNK should be at idx 1 
        self.ixtoword = {0:END, 1:UNK}
        self.wordtoix = {END:0, UNK:1}

        ##### TODO #####
        # Count the frequencies of all words in the training data (self.examples)
        # Assign idx (starting from 2) to all words having word_freq >= THRESHOLD
        counter = {}
        for line in self.examples:
            for word in line.text:
                wordLower = word.lower()
                if wordLower in counter:
                    counter[wordLower] = counter[wordLower] + 1
                else:
                    counter[wordLower] = 1
                    
            index = 2
            for word in counter:
                if self.THRESHOLD <= counter[word]:
                    self.ixtoword[index] = word
                    self.wordtoix[word] = index
                    index = 1 + index
        print(self.wordtoix)


    
    def get_label(self, index):
        ##### TODO #####
        # This function should return the value 1 if the label is positive, and 0 if it is negative for sentence at index `index`
        # The data type for the returned item should be torch.LongTensor
    
        label = self.examples[index].label
        if label != "positive":
            label = torch.LongTensor([0]).squeeze()
        else:
            label = torch.LongTensor([1]).squeeze()
        return label
     
    def get_text(self, index):
        ##### TODO #####
        # This function should pad the text with END token uptil a length of MAX_LEN if the length of the text is less than the MAX_LEN
        #   If length is more than MAX_LEN then only return the first MAX_LEN words
        # This function should also return the original length of the review
        # The data type for the returned items should be torch.LongTensor
        # Note that the text returned is a list of indices of the words from your wordtoix mapping
        
        text = []
        review = []
        
        line = self.examples[index]
        review = line.text.copy()
        
        text_len = len(line.text)
        if text_len >= self.MAX_LEN:
            review = review[0:self.MAX_LEN]
        else:
            while len(review) < self.MAX_LEN:
                review.append(END)

        for word in review:
            wordLower = word.lower()
            if wordLower not in self.wordtoix:
                text.append(self.wordtoix[UNK])
            else:
                text.append(self.wordtoix[wordLower])
        
        return (torch.LongTensor(text),torch.LongTensor([text_len]).squeeze())


    def __len__(self):
        ##### TODO #####
        # This function should return the number of sentences (int value) in the dataset
        return len(self.examples)
    
    def __getitem__(self, index):
        text, text_len = self.get_text(index)
        label = self.get_label(index)

        return text, text_len, label


if __name__=='__main__':
    # Sample item
    Ds = TextDataset(train_data, 'train')
    print('vocab_size:', Ds.vocab_size)

    text, text_len, label = Ds[0]
    print('text:', text)
    print('text_len:', text_len)
    print('label:', label)

"""# Some helper functions"""

##### Do not modify this

def count_parameters(model):
    """
    Count number of trainable parameters in the model
    """
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


def accuracy(output, labels):
    """
    Returns accuracy per batch
    output: Tensor [batch_size, n_classes]
    labels: LongTensor [batch_size]
    """
    preds = output.argmax(dim=1) # find predicted class
    correct = (preds == labels).sum().float() # convert into float for division 
    acc = correct / len(labels)
    return acc

"""# Train your Model"""

##### Do not modify this

def train_model(model, num_epochs, data_loader, optimizer, criterion):
    print('Training Model...')
    model.train()
    for epoch in range(num_epochs):
        epoch_loss = 0
        epoch_acc = 0
        for texts, text_lens, labels in data_loader:
            texts = texts.to(device) # shape: [batch_size, MAX_LEN]
            text_lens = text_lens.to(device) # shape: [batch_size]
            labels = labels.to(device) # shape: [batch_size]

            optimizer.zero_grad()

            output = model(texts, text_lens)
            acc = accuracy(output, labels)
            
            loss = criterion(output, labels)
            loss.backward()
            optimizer.step()

            epoch_loss += loss.item()
            epoch_acc += acc.item()
        print('[TRAIN]\t Epoch: {:2d}\t Loss: {:.4f}\t Accuracy: {:.2f}%'.format(epoch+1, epoch_loss/len(data_loader), 100*epoch_acc/len(data_loader)))
    print('Model Trained!\n')

"""# Evaluate your Model"""

##### Do not modify this

def evaluate(model, data_loader, criterion):
    print('Evaluating performance on Test dataset...')
    model.eval()
    epoch_loss = 0
    epoch_acc = 0
    all_predictions = []
    for texts, text_lens, labels in data_loader:
        texts = texts.to(device)
        text_lens = text_lens.to(device)
        labels = labels.to(device)
        
        output = model(texts, text_lens)
        acc = accuracy(output, labels)
        all_predictions.append(output.argmax(dim=1))
        
        loss = criterion(output, labels)
        
        epoch_loss += loss.item()
        epoch_acc += acc.item()

    print('[TEST]\t Loss: {:.4f}\t Accuracy: {:.2f}%'.format(epoch_loss/len(data_loader), 100*epoch_acc/len(data_loader)))
    predictions = torch.cat(all_predictions)
    return predictions

"""# 2. Build your Convolutional Neural Network Model (3 points)
In the following we provide you the class to build your model. We provide some parameters that we expect you to use in the initialization of your sequential model. Do not change these parameters.
"""

class CNN(nn.Module):
    def __init__(self, vocab_size, embed_size, out_channels, filter_heights, stride, num_classes, dropout, pad_idx):
        super(CNN, self).__init__()
        
        ##### TODO #####
        # Create an embedding layer (https://pytorch.org/docs/stable/generated/torch.nn.Embedding.html)
        #   to represent the words in your vocabulary. You can vary the dimensionality of the embedding
        #self.embedding = None
        self.embedding = nn.Embedding(vocab_size, embed_size)

        # Define multiple Convolution layers (nn.Conv2d) with filter (kernel) size [filter_height, embed_size] based on your different filter_heights.
        #   Input channels will be 1 and output channels will be `out_channels` (these many different filters will be trained for each convolution layer)
        #   If you want, you can have a list of modules inside nn.ModuleList
        # Note that even though your conv layers are nn.Conv2d, we are doing a 1d convolution since we are only moving the filter in one direction
        #
        # You can vary the number of output channels, filter heights, and stride
        number_layers = 3
        input_channels = 1
        self.conv1 = nn.Conv2d(input_channels, out_channels, [filter_heights[0], embed_size])
        self.conv2 = nn.Conv2d(input_channels, out_channels, [filter_heights[1], embed_size])
        self.conv3 = nn.Conv2d(input_channels, out_channels, [filter_heights[2], embed_size])

        # Define a linear layer (nn.Linear) that consists of num_classes (2 in our case) units 
        #   and takes as input the concatenated output for all cnn layers (out_channels * num_of_cnn_layers units)
        self.linear = nn.Linear(3 * out_channels, num_classes)
        self.dropout = nn.Dropout()


    def forward(self, texts, text_lens):
        """
        texts: LongTensor [batch_size, MAX_LEN]
        text_lens: LongTensor [batch_size] - you might not even need to use this
        
        Returns output: Tensor [batch_size, num_classes]
        """
        ##### TODO #####

        # Pass texts through your embedding layer to convert from word ids to word embeddings
        # texts: [batch_size, MAX_LEN, embed_size]

        # input to conv should have 1 channel. Take a look at torch's unsqueeze() function
        # texts [batch_size, 1, MAX_LEN, embed_size]
        
        emb = self.embedding(texts)
        
        conv1 = self.conv1(torch.unsqueeze(emb, 1))
        conv2 = self.conv2(torch.unsqueeze(emb, 1))
        conv3 = self.conv3(torch.unsqueeze(emb, 1))
        
        relu1 = torch.squeeze(conv1, 3)
        relu2 = torch.squeeze(conv2, 3)
        relu3 = torch.squeeze(conv2, 3)
        
        fRelu1 = F.relu(relu1)
        fRelu2 = F.relu(relu2)
        fRelu3 = F.relu(relu3)
        
        pool1 = F.max_pool1d(fRelu1, kernel_size = fRelu1.shape[2]).squeeze(2)
        pool2 = F.max_pool1d(fRelu2, kernel_size = fRelu2.shape[2]).squeeze(2)
        pool3 = F.max_pool1d(fRelu3, kernel_size = fRelu3.shape[2]).squeeze(2)
        
        concat = torch.cat([pool1, pool2, pool3], dim = 1)
        
        dropConcat = self.dropout(concat)
        output = self.linear(concat)
        
        # Pass these texts to each of your cnn and compute their output as follows:
        #   Your cnn output will have shape [batch_size, out_channels, *, 1] where * depends on filter_height and stride
        #   Convert to shape [batch_size, out_channels, *] (see torch's squeeze() function)
        #   Apply non-linearity on it (F.relu() is a commonly used one. Feel free to try others)
        #   Take the max value across last dimension to have shape [batch_size, out_channels]
        # Concatenate (torch.cat) outputs from all your cnns [batch_size, (out_channels*num_of_cnn_layers)]
        #
        # Let's understand what you just did:
        #   Since each cnn is of different filter_height, it will look at different number of words at a time
        #     So, a filter_height of 3 means your cnn looks at 3 words (3-grams) at a time and tries to extract some information from it
        #   Each cnn will learn `out_channels` number of different features from the words it sees at a time
        #   Then you applied a non-linearity and took the max value for all channels
        #     You are essentially trying to find important n-grams from the entire text
        # Everything happens on a batch simultaneously hence you have that additional batch_size as the first dimension

        # optionally apply a dropout if you want to (You will have to initialize an nn.Dropout layer in __init__)

        # Pass your concatenated output through your linear layer and return its output ([batch_size, num_classes])

        ##### NOTE: Do not apply a sigmoid or softmax to the final output - done in evaluation method!

        
        return output

"""## Initialize the Dataloader
We initialize the training and testing dataloaders using the Dataset classes we create for both training and testing. Make sure you use the same vocabulary for both the datasets.
"""

if __name__=='__main__':
    BATCH_SIZE = 32 # Feel free to try other batch sizes

    ##### Do not modify this
    Ds = TextDataset(train_data, 'train')
    train_loader = torch.utils.data.DataLoader(Ds, batch_size=BATCH_SIZE, shuffle=True, num_workers=4, drop_last=True)

    test_Ds = TextDataset(test_data, 'test', Ds.ixtoword, Ds.wordtoix)
    test_loader = torch.utils.data.DataLoader(test_Ds, batch_size=1, shuffle=False, num_workers=1, drop_last=False)

"""## Training and Evaluation for CNN Model

We first train your model using the training data. Feel free to play around with the hyperparameters. We recommend **you write code to save your model** [(save/load model tutorial)](https://pytorch.org/tutorials/beginner/saving_loading_models.html) as colab connections are not permanent and it can get messy if you'll have to train your model again and again.
"""

if __name__=='__main__':
    ##### Do not modify this
    VOCAB_SIZE = Ds.vocab_size
    NUM_CLASSES = 2
    PAD_IDX = 0
    
    # Hyperparameters (Feel free to play around with these)
    EMBEDDING_DIM = 202
    DROPOUT = 0.15
    OUT_CHANNELS = 16
    FILTER_HEIGHTS = [1, 2, 3] # [3 different filter sizes - unigram, bigram, trigram in this case. Feel free to try other n-grams as well]
    STRIDE = 2
    model = CNN(VOCAB_SIZE, EMBEDDING_DIM, OUT_CHANNELS, FILTER_HEIGHTS, STRIDE, NUM_CLASSES, DROPOUT, PAD_IDX)

    # put your model on device
    model = model.to(device)
    
    print('The model has {:,d} trainable parameters'.format(count_parameters(model)))

if __name__=='__main__':    
    LEARNING_RATE = 5e-4 # Feel free to try other learning rates

    # Define your loss function
    criterion = nn.CrossEntropyLoss().to(device)

    # Define your optimizer
    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)

if __name__=='__main__':    
    N_EPOCHS = 10 # Feel free to change this
    
    # train model for N_EPOCHS epochs
    train_model(model, N_EPOCHS, train_loader, optimizer, criterion)

##### Do not modify this

if __name__=='__main__':    
    # Compute test data accuracy
    predictions_cnn = evaluate(model, test_loader, criterion)

    # Convert tensor to numpy array 
    # This will be saved to your Google Drive below and you will be submitting this file to gradescope
    predictions_cnn = predictions_cnn.cpu().data.detach().numpy()

"""# 3. Build your Recurrent Neural Network Model (3 points)
In the following we provide you the class to build your model. We provide some parameters that we expect you to use in the initialization of your sequential model. Do not change these parameters.
"""

class RNN(nn.Module):
    def __init__(self, vocab_size, embed_size, hidden_size, num_classes, num_layers, bidirectional, dropout, pad_idx):
        super(RNN, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers

        ##### TODO #####
        # Create an embedding layer (https://pytorch.org/docs/stable/generated/torch.nn.Embedding.html) 
        #   to represent the words in your vocabulary. You can vary the dimensionality of the embedding
        self.embedding = None

        # Create a recurrent network (nn.LSTM or nn.GRU) with batch_first = False
        # You can vary the number of hidden units, directions, layers, and dropout
        self.rnn = None
        
        # Define a linear layer (nn.Linear) that consists of num_classes (2 in our case) units 
        #   and takes as input the output of the last timestep (in the bidirectional case: the output of the last timestep
        #   of the forward direction, concatenated with the output of the last timestep of the backward direction)
        self.linear = None


    def forward(self, texts, text_lens):
        """
        texts: LongTensor [batch_size, MAX_LEN]
        text_lens: LongTensor [batch_size]
        
        Returns output: Tensor [batch_size, num_classes]
        """
        ##### TODO #####

        # permute texts for sentence_len first dimension
        # texts: [MAX_LEN, batch_size]

        # Pass texts through your embedding layer to convert from word ids to word embeddings
        # texts: [MAX_LEN, batch_size, embed_size]

        # Pack texts into PackedSequence using nn.utils.rnn.pack_padded_sequence
        
        # Pass the pack through your recurrent network
        
        # Take output of the last timestep of the last layer for all directions and concatenate them (see torch.cat())
        #   depends on whether your model is bidirectional
        # Your concatenated output will have shape [batch_size, num_dirs*hidden_size]
        
        # optionally apply a dropout if you want to (You will have to initialize an nn.Dropout layer in __init__)

        # Pass your concatenated output through your linear layer and return its output ([batch_size, num_classes])

        ##### NOTE: Do not apply a sigmoid or softmax to the final output - done in evaluation method!

        
        return output

"""## Initialize the Dataloader
We initialize the training and testing dataloaders using the Dataset classes we create for both training and testing. Make sure you use the same vocabulary for both the datasets.
"""

if __name__=='__main__':
    BATCH_SIZE = 32 # Feel free to try other batch sizes

    ##### Do not modify this
    Ds = TextDataset(train_data, 'train')
    train_loader = torch.utils.data.DataLoader(Ds, batch_size=BATCH_SIZE, shuffle=True, num_workers=4, drop_last=True)

    test_Ds = TextDataset(test_data, 'test', Ds.ixtoword, Ds.wordtoix)
    test_loader = torch.utils.data.DataLoader(test_Ds, batch_size=1, shuffle=False, num_workers=1, drop_last=False)

"""## Training and Evaluation for Sequential Model

We first train your model using the training data. Feel free to play around with the hyperparameters. We recommend **you write code to save your model** [(save/load model tutorial)](https://pytorch.org/tutorials/beginner/saving_loading_models.html) as colab connections are not permanent and it can get messy if you'll have to train your model again and again.
"""

if __name__=='__main__':
    ##### Do not modify this
    VOCAB_SIZE = Ds.vocab_size
    NUM_CLASSES = 2
    PAD_IDX = 0

    # Hyperparameters (Feel free to play around with these)
    EMBEDDING_DIM = 64
    DROPOUT = 0
    BIDIRECTIONAL = True
    HIDDEN_DIM = 128
    N_LAYERS = 2
    
    model = RNN(VOCAB_SIZE, EMBEDDING_DIM, HIDDEN_DIM, NUM_CLASSES, N_LAYERS, BIDIRECTIONAL, DROPOUT, PAD_IDX)

    # put your model on device
    model = model.to(device)
    
    print('The model has {:,d} trainable parameters'.format(count_parameters(model)))

if __name__=='__main__':    
    LEARNING_RATE = 5e-4 # Feel free to try other learning rates

    # Define your loss function
    criterion = nn.CrossEntropyLoss().to(device)

    # Define your optimizer
    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)

if __name__=='__main__':    
    N_EPOCHS = 10 # Feel free to change this
    
    # train model for N_EPOCHS epochs
    train_model(model, N_EPOCHS, train_loader, optimizer, criterion)

##### Do not modify this

if __name__=='__main__':    
    # Compute test data accuracy
    predictions_rnn = evaluate(model, test_loader, criterion)

    # Convert tensor to numpy array 
    # This will be saved to your Google Drive below and you will be submitting this file to gradescope
    predictions_rnn = predictions_rnn.cpu().data.detach().numpy()

"""# Saving test results to your Google drive for submission.
You will save the `predictions_rnn.txt` and `predictions_cnn.txt` with your test data results. Make sure you do not **shuffle** the order of the `test_data` or the autograder will give you a bad score.

You will submit the following files to the autograder on the gradescope :
1.   Your `predictions_cnn.txt` of test data results
1.   Your `predictions_rnn.txt` of test data results
2.   Your code of this notebook. You can do it by clicking `File`-> `Download .py` - make sure the name of the downloaded file is `HW2.py`
"""

##### Do not modify this

if __name__=='__main__':
    try:
        from google.colab import drive
        drive.mount('/content/drive')
    except:
        pass

    np.savetxt('drive/My Drive/predictions_cnn.txt', predictions_cnn, delimiter=',')
    np.savetxt('drive/My Drive/predictions_rnn.txt', predictions_rnn, delimiter=',')

    print('Files saved successfully!')

