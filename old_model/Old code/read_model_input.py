import pandas as pd
import math
import numpy as np
from numpy import random
from scipy.stats import poisson


print("Importing read_model_input.py")

# ------------ Reading from excel file ------------

def read_list(sheet, name,integerVal=False):
    set =  sheet[name].values
    list = []
    for value in set:
        if not str(value) == "nan":
            if integerVal:
                list.append(int(value))
            else:
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

def read_3d(sheets, prefix, nDays):
    cube = []
    for sheet in sheets:
        matrix = read_matrix(sheet, prefix, nDays)
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

def write_param_1i(path, indices, param, name,integerVal=False):
    with open(path, 'a') as file:
        file.write("param " + name + " :=")
        for i in range(len(indices)):
            if integerVal:
                file.write("\n" + str(indices[i])+" " + str(int(param[i])))
            else:
                file.write("\n" + str(indices[i])+" " + str(float(param[i])))
        file.write("\n;\n \n")

def write_param_2i(path, ind1, ind2, param, name,integerVal=False):
    with open(path, 'a') as file:
        file.write("param " + name + " : ")
        for index in range(len(ind2)):
            file.write(str(ind2[index]) + " ")
        file.write(":=\n")
        for i in range(len(ind1)):
            file.write(str(ind1[i]))
            for j in range(len(ind2)):
                if integerVal:
                    file.write(str(" " + str(int(param[j][i]))))
                else:
                    file.write(str(" " + str(float(param[j][i]))))
            file.write("\n")
        file.write(";\n\n")

def write_param_3i(path, groups, wards, maxLOS, param, name):
    with open(path, 'a') as file:
        file.write("param " + name + " : ")
        for index in range(maxLOS):
            file.write(str(index+1) + " ")
        file.write(":=\n")
        for g in range(len(groups)):
            for w in range(len(wards)):
                file.write(str("(" + groups[g]) + " " + str(wards[w]) + ")")
                for d in range(maxLOS):
                    pass
                    #print("w: ", w)
                    #print("d: ", d)
                    #print("g: ", g)
                    file.write(" " + str(float(param[w][d][g] )))
                file.write("\n")
        file.write(";\n\n")

def generate_scenarios(groups, TargetTroughput, nScenarios, seed):
    scenarioMatrix=[]
    np.random.seed(seed)
    for i in range(nScenarios):
        randVec=np.random.rand(1,len(groups))
        scenarioPre=poisson.ppf(randVec, TargetTroughput)
        scenario=[]
        for group in range(len(groups)):
            scenario.append(int(scenarioPre[0][group]))
        scenarioMatrix.append(scenario)
    return scenarioMatrix

def main(file_name,nScenarios,seed):

    file = file_name
    overview = pd.read_excel(file, sheet_name='Overview')
    MC = pd.read_excel(file, sheet_name='MC')    
    IC = pd.read_excel(file, sheet_name='IC')  

# ----- Reading/Creating Sets -----
    G = read_list(overview, "Surgery groups")                           #Surgery Groups
    W = read_list(overview, "Wards")                                    #Wards
    S = read_list(overview, "Specialties")                              #Specialties
    R = read_list(overview, "Operating rooms")                          #Operating Rooms
    D = read_list(overview, "Days",True)                                #Days
    C = []                                                              #Scenarios
    
    nDays = int(overview["Planning days"].values[0])                                       
    for scenario in range(1,nScenarios+1):
        C.append(scenario)                                      
# ----- Reading/Creting Subsets -----
    GS_specialty =  read_list(overview, "Specialty")                    #vector of specialties in   G^S_(s)
    GW_groups   =   read_list(overview, "Group to Ward")                #vector of groups in        G^W_(w)
    GW_wards    =   read_list(overview, "Ward to Group")                #vector of wards in         G^W_(w)
    RS_spec     =   read_list(overview, "Spec to OR")                   #vector of specialties in   R^S_(s)
    RS_rooms    =   read_list(overview, "OR to spec")                   #vector of ORs in           R^S_(s)
    RG_rooms    =   []                                                  #vector of ORs in           R^G_(g)
    RG_groups   =   []                                                  #vector of groups in        R^G_(g)
    
    for g in range(len(G)):
        for s in range(len(RS_spec)):
            if RS_spec[s] == GS_specialty[g]:             
                RG_groups.append(G[g])
                RG_rooms.append(RS_rooms[s])
# ----- Reading/Creating Parameters -----
    F           =   float(overview["Flexible share"].values[0])         #Flexible Share             F
    E           =   int(overview["Extended time"].values[0])            #Extended time              E
    TC          =   int(overview["Cleaning time"].values[0])            #Cleaning Time              T^C
    I           =   int(overview["Cycles in PP"].values[0])             #Cycles in Planning Period  I
    B           =   read_matrix(overview,"B",nDays)                     #Bedward Capacity           B_(w,d)
    H           =   read_list(overview, "Opening Hours")                #Opening hours              H_(d)
    K           =   read_matrix(overview,"K",nDays)                     #Team Capacity per day      K_(s,d)
    L           =   read_list(overview,"Surgery duration")              #Surgery uration            L_(g)
    M_L         =   read_list(overview,"Max long days")                 #Max long days              U_(s)
    N           =   []                                                  #Open ORs each days         N_(d)
    T           =   read_list(overview,"Target Troughput")              #Target troughput           T_(g)
    Co          =   [element+TC for element in L]                       #Cost                       C_(g)
    J           =   read_list(overview,"Max LOS",True)                  #Maximum LOS at the wards   J_(w)
    P           =   read_3d([MC, IC], "J", max(J))                      #Probabilies                P_(g,w,d)
    

    for day in D:
        if (day)%7 == 0 or (day)%7 == 6:
            N.append(0) 
        else:
            N.append(7)     
# ----- Scenario generation ----- #
    Q = generate_scenarios(G,T,nScenarios,seed)                         #Demand                     Q^T_(g,c)
    Pi=[]                                                               #Probability of scenario    PI_(c)
    for scenario in C:
        Pi.append(1/nScenarios)
# ----- Writing ----- #
    filepath = "Old Model/Input/input_model.dat"
    with open(filepath, "w") as file:
        pass
# ----- Write sets --- #
    write_set(filepath, W, "W")                                         #W
    write_set(filepath, S, "S")                                         #S
    write_set(filepath, G, "G")                                         #G
    write_subset(filepath,GW_groups,GW_wards,W,"GW")                    #G^W_(w)
    write_subset(filepath, G, GS_specialty, S, "GS")                    #G^S_(s)
    write_set(filepath, R, "R")                                         #R
    write_subset(filepath, RS_rooms, RS_spec, S, "RS")                  #R^S_(s)
    write_subset(filepath, RG_rooms, RG_groups, G, "RG")                #R^G_(g)                                                     
    write_set(filepath, D, "D")                                         #D
    write_set(filepath, C, "C")                                         #C
# ----- Write params --- #
    write_param_1i(filepath,C,Pi,"Pi")                                  #Pi_(c)
    write_param_1i(filepath,G,Co,"Co")                                  #C_g
    write_range(filepath, TC, "TC")                                     #TC
    write_param_1i(filepath,G,L,"L")                                    #L^SD_(g)
    write_range(filepath, F, "F")                                     #F
    write_param_1i(filepath,D,N,"N",True)                               #N_(d)
    write_param_1i(filepath,S,M_L,"U",True)                             #U^X_(s)
    write_range(filepath, I, "I")                                       #I
    write_param_2i(filepath,S,D,K,"K",True)                             #K_(s,d)
    write_param_1i(filepath,D,H,"H",True)                               #H_(d)
    write_range(filepath, E, "E")                                       #E
    write_param_2i(filepath,G,C,Q,"Q",True)                             #Q_(g,c)
    write_param_1i(filepath,W,J,"J",True)                               #J_(w)
    write_param_2i(filepath,W,D,B,"B")                                  #B_(w,d)
    write_param_3i(filepath, G, W, 20, P, "P")                          #P_(g,w,d)
    
    with open(filepath, "a") as file:
        file.close()

    print("   New input file created")

pathName= "Old Model/Input/model_input.xlsx"
main(pathName,10,1)
