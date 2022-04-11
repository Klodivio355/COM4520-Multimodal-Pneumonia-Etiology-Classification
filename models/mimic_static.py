import sys
import os
import torch
from multiprocessing import freeze_support

sys.path.append(os.getcwd())

from unimodals.common_models import MLP, GRU # noqa
from models.get_data import get_dataloader # noqa
from fusions.common_fusions import Concat # noqa
from training_structures.Supervised_Learning import train, test # noqa

import scripts.const as const
import pandas as pd
import scripts.config as config



def runModel(nrRuns,outputRoot,nrEpochs,shuffle_split = True,lr =0.001,dropout=False,dropoutP=0.1,optimizer=torch.optim.RMSprop,earlyStop = True):

    MODEL_NAME = "static"

    static_output_size = 100
    test_accuracies = []
    for i in range(nrRuns):
        traindata, validdata, testdata = get_dataloader(
            7, imputed_path=config.impkPath, model = const.Models.static,shuffle_split = shuffle_split)
    

        encoders = [MLP(indim = const.nr_static_features, hiddim = 50, outdim = static_output_size, dropout=dropout,dropoutp=dropoutP).cuda()]
        head = MLP(static_output_size, 40, 2, dropout=False).cuda()
        fusion = Concat().cuda()

        # train
        stats = train(encoders, fusion, head, traindata, validdata, nrEpochs, auprc=True,lr = lr,early_stop=earlyStop,optimtype=optimizer)

        # test
        print("Testing: ")
        model = torch.load('best.pt').cuda()

        rob_curve = test(model, testdata, dataset='mimic 7', auprc=True)
        test_acc = rob_curve['Accuracy'][0] 
        test_accuracies.append(test_acc)

        outputStats(stats,outputRoot, "/run-{}-{}-validation.csv".format(str(i), MODEL_NAME))
    
    pd.DataFrame(test_accuracies,columns=['acc']).to_csv(outputRoot + "/{}-test.csv".format(MODEL_NAME))

    #Write the arhitecture of the model to a file
    #TODO: Be more specific about the arhitecture. Write down the size of every layer, not just the sizes of the output layers of the encoders
    with open(outputRoot + "/model_arhitecture.txt", 'w') as f:
        f.write('Static output layer: ' + str(static_output_size) + '\n')

def outputStats(stats,root,csvName):
    # Outputs statistics to csvPath
    pd.DataFrame(stats['valid'],columns = ['epoch','acc','valloss']).to_csv(root + csvName)

if __name__ == '__main__':
    freeze_support()
    runModel(nrRuns = 1,outputRoot = config.stats_root,nrEpochs = 20,shuffle_split=True)
