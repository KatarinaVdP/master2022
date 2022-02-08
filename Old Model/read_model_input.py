import pandas as pd
import math
import xlwt
from xlwt import Workbook
import numpy as np


print("Importing read_input.py")

# ------------ Reading from excel file ------------

def read_list(sheet, name):
    set =  sheet[name].values
    list = []
    for value in set:
        if not str(value) == "nan":
            list.append(value)
    return list

def read_matrix(sheet, prefix, days):
    matrix = []
    for i in range(days):
        column = sheet[prefix + str(i + 1)].values
        sublist = []
        for j in column:
            if not math.isnan(j):
                sublist.append(j)
        matrix.append(sublist)
    return matrix

def read_3d(sheets, prefix, days):
    cube = []
    for sheet in sheets:
        matrix = read_matrix(sheet, prefix, days)
        cube.append(matrix)
    return cube

# --------------- Writing to data file --------------'


def write_range(path, param, name):
    with open(path, 'a') as file:
        file.write("param " + name + " :=")
        file.write(" " + str(param))
        file.write(";")
        file.write("\n \n")

def write_set(path, set, name):
    with open(path, 'a') as file:
        file.write("set " + name + " :=")
        for entry in set:
            file.write(" " + str(entry))
        file.write(";")
        file.write("\n \n")

def write_subset(path, members, membership, indices, name):
    with open(path, 'a') as file:
        for index in indices:
            file.write("set " + name + "[" + str(index) + "] :=")
            for j in range(len(membership)):
                if index == membership[j]:
                    file.write(" " + str(members[j]))
            file.write(";\n")
        file.write("\n")

def write_param_1i(path, indices, param, name):
    with open(path, 'a') as file:
        file.write("param " + name + " :=")
        for i in range(len(indices)):
            file.write("\n" + str(indices[i]) + " " + str(param[i]))
        file.write("\n;\n \n")

def write_param_2i(path, ind1, days, param, name):
    with open(path, 'a') as file:
        file.write("param " + name + " : ")
        for index in range(days):
            file.write(str(index+1) + " ")
        file.write(":=\n")
        for i in range(len(ind1)):
            file.write(str(ind1[i]))
            for j in range(days):
                file.write(str(" " + str(int(param[j][i]))))
            file.write("\n")
        file.write(";\n\n")

def write_param_3i(path, groups, wards, days, param, name):
    with open(path, 'a') as file:
        file.write("param " + name + " : ")
        for index in range(days):
            file.write(str(index+1) + " ")
        file.write(":=\n")
        for g in range(len(groups)):
            for w in range(len(wards)):
                file.write(str("(" + groups[g]) + " " + str(wards[w]) + ")")
                for d in range(days):
                    pass
                    #print("w: ", w)
                    #print("d: ", d)
                    #print("g: ", g)
                    file.write(" " + str(float(param[w][d][g] )))
                file.write("\n")
        file.write(";\n\n")

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

def main(file_name,nScenarios,seed):
    print("Running main from read_input_Iterative.py")
    file = file_name
    overview = pd.read_excel(file, sheet_name='Overview', encoding="latin-1")  

# ----- Reading Sets -----
    G = read_list(overview, "Surgery groups")                   #Surgery Groups
    W = read_list(overview, "Wards")                            #Wards
    S = read_list(overview, "Specialties")                      #Specialties
    R = read_list(overview, "Operating rooms")                  #Operating Rooms

    D = []
    nDays = int(overview["Planning days"].values[0]) 
    for day in range(1,nDays+1):
        D.append(day)                                           #Days
    C = []  
    for scenario in range(1,nScenarios+1):
        C.append(scenario)                                      #Scenarios
# ----- Reading Subsets -----
    GS_specialty = read_list(overview, "Specialty")             #Surgery groups to each speciality

    RS_spec  = read_list(overview, "Spec to OR")                #Room to Specialty to each speciality
    RS_rooms = read_list(overview, "OR to spec")                #Room to Specialty to each speciality

# ----- Reading Parameters -----
    FF  = float(overview["Flexible share"].values[0])           #Flexible Share
    E   = int(overview["Extended time"].values[0])              #Extended time
    TC  = int(overview["Cleaning time"].values[0])              #Cleaning Time
    I   = int(overview["Cycles in PP"].values[0])               #Cycles in Planning Period

    B   =   read_matrix(overview,"B",nDays)                     #Bedward Capacity
    H   =   read_matrix(overview, "H", nDays)                   #Opening hours
    K   =   read_matrix(overview,"K",nDays)                     #Team Capacity per day

    L   =   read_list(overview,"Surgery duration")              #Surgery uration
    M_L =   read_list(overview,"Max long days")                 #Max long days

    T   =   read_list(overview,"Target Troughput")
    PI  =   1/nScenarios
    Co   =   [element+TC for element in L]
# ----- Scenario generation -----
    filepathScenarios = "input_scenarios_"+str(len(G))+"g_"+str(nScenarios)+"c_"+str(seed)+".txt"

    with open(filepathScenarios, 'w') as file:
        file.write("param " + "Q" + " : ")
        for i in range(nScenarios):
            file.write(str(i+1) + " ")
        file.write(":=\n")
        np.random.seed(seed)
        for i in range(len(G)):
            file.write(str(G[i]))
            for j in range(1,nScenarios+1):
                x= np.random.poisson(T[i])
                file.write(str(" " + str(x)))
            file.write("\n")
        file.write(";\n\n")
    
    filepath = "input_file_prosjektoppgave.txt"

    with open(filepath, "w") as file:
        pass
# ----- Write sets --- #
    write_set(filepath, W, "W")                         #W
    write_set(filepath, S, "S")                         #S
    write_set(filepath, G, "G")                         #G
                                                        #G^W_(w)
    write_subset(filepath, G, GS_specialty, S, "GS")   #G^S_(s)
    write_set(filepath, R, "R")                         #R
    write_subset(filepath, RS_rooms, RS_spec, S, "RS") #R^S_(s)
                                                        #R^G_(g)                                                     
    write_set(filepath, D, "D")                         #D
                                                        #C
# ----- Write params --- #
    write_range(filepath,PI,"PI")                       #PI_(c)
    write_param_1i(filepath,G,Co,"Co")                  #C_g
    write_range(filepath, TC, "TC")                     #TC
    write_param_1i(filepath,G,L,"L")                    #L^SD_(g)
    write_range(filepath, FF, "FF")                     #F
                                                        #N_(d)
    write_param_1i(filepath,S,M_L,"U")                #U^X_(s)
    write_range(filepath, I, "I")                       #I
    write_param_2i(filepath,S,nDays,K,"K")              #K_(s,d)
    write_param_2i(filepath,R,nDays,H,"H")              #H_(r,d) ???
    write_range(filepath, E, "E")                       #E
    write_scenarios(filepath,G,T,nScenarios,seed,"Q")   #Q_(g,c)
                                                        #J_(w)
    write_param_2i(filepath,W,nDays,B,"B")              #B_(w,d)

    with open(filepath, "a") as file:
        file.close()

main("model_input_prosjektoppgave.xlsx",10,1)