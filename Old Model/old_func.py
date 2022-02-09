import numpy as np
from numpy import random

def retrive_ScenarioData(fileName):
    QTransposeFound             =   False
    file                        =   open(fileName, 'r')
    scenariosMatrix             =   []

    for line in file:
        string_list         =   line.split()
        if string_list:
            if string_list[0] == ']' and QTransposeFound:
                QTransposeFound   =   False  
            if string_list[0] == 'Pi:':
                PI                  = float(string_list[1])
            if QTransposeFound:
                map_object              = map(int, string_list)
                list_of_integers        = list(map_object)
                scenariosMatrix.append(list_of_integers)

            if  string_list[0] == 'QTranspose:':
                QTransposeFound = True  
    return scenariosMatrix, PI

def write_scenarios(path, groups, TargetTroughput, nScenarios, seed,name):
    with open(path, 'a') as file:
        file.write("param " + name + " : ")
        for i in range(nScenarios):
            file.write(str(i+1) + " ")
        file.write(":=\n")
        
        np.random.seed(seed)
        for i in range(len(groups)):
            file.write(str(groups[i]))
            for j in range(1,nScenarios+1):
                x= np.random.poisson(TargetTroughput[i])
                file.write(str(" " + str(x)))
            file.write("\n")
        file.write(";\n\n") 

def write_param_scenarios(path, ind1, groups, param, name):
    with open(path, 'a') as file:
        file.write("param " + name + " : ")
        for index in range(len(groups)):
            file.write(groups[index] + " ")
        file.write(":=\n")
        for i in range(len(ind1)):
            file.write(str(ind1[i]))
            for j in range(groups):
                file.write(str(" " + str(int(param[j][i]))))
            file.write("\n")
        file.write(";\n\n")
        
        