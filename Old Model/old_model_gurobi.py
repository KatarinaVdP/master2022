from argon2 import Parameters
import pandas as pd
import math
import numpy as np
from numpy import random
from scipy.stats import poisson
import gurobipy as gp
from gurobipy import GRB
from gurobipy import multidict

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

def read_matrix(sheet, prefix, colombs):
    matrix = []
    for i in range(colombs):
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

def read_subset(matrix, affiliating_set, index_set):
        subset=[]
        for i in range(len(index_set)):
            subsublist=[]
            for j in range(len(affiliating_set)):
                if int(matrix[i][j])==1:
                    subsublist.append(affiliating_set[j])
            subset.append(subsublist) 
        return subset
    
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
    file        =   file_name
    parameters  =   pd.read_excel(file, sheet_name='Parameters')
    sets        =   pd.read_excel(file, sheet_name='Sets')
    MC          =   pd.read_excel(file, sheet_name='MC')    
    IC          =   pd.read_excel(file, sheet_name='IC')  
                           
# ----- Reading/Creting sets -----
    '--- Set of Wards ---'
    W                   =   read_list(sets, "Wards")                  
    print("W:=")
    print(W)
    '--- Set of Specialties ---'
    S                   =   read_list(sets, "Specialties")                
    print("S:=")
    print(S)
    '--- Set of Surgery Groups ---'
    G                   =   read_list(sets, "Surgery Groups")             
    print("G:=")
    print(G)
    '--- Subset of Groups in Wards ---'
    WardGroup           =   read_matrix(sets,"Gr",len(G))
    GroupWard           =   list(map(list, np.transpose(WardGroup)))
    GW                  =   read_subset(GroupWard,G,W)                  
    print("GW:=")
    print(GW)
    '--- Subset of Groups in Specialties ---'    
    SpecialtyGroup      =   read_matrix(sets,"G",len(G))
    GroupSpecialty      =   list(map(list, np.transpose(SpecialtyGroup)))
    GS                  =   read_subset(GroupSpecialty,G,S)
    print("GS:=")
    print(GS)
    '--- Set of Rooms ---'   
    R                   =   read_list(sets, "Operating Rooms") 
    print("R:=")
    print(R)                               
    '--- Subset of Rooms in Specialties ---' 
    SpecialtyRoom       =   read_matrix(sets,"R",len(R))
    RoomSpecialty       =   list(map(list, np.transpose(SpecialtyRoom)))   
    RS                  =   read_subset(RoomSpecialty,R,S)                 
    print("RS:=")
    print(RS)    
    '--- Subset of Rooms for Groups ---'     
    RG                  =   []
    for g in range(len(G)):
        sublist = []
        for s in range(len(S)):
            if G[g] in GS[s][:]:
                sublist=RS[s][:]
                break
        RG.append(sublist)
    print("RG:=")
    print(RG)
    '--- Set of Days ---'  
    D                   =   []
    nDays = int(parameters["Planning Days"].values[0])
    for d in range(1,nDays+1):
        D.append(d) 
    print("D:=")
    print(D)
    '--- Set of Scenarios ---'
    C                   =   []                                                                                 
    for scenario in range(1,nScenarios+1):
        C.append(scenario)  
    print("C:=")
    print(C)   


# ----- Testing Multidictionary ---- #
    multi = {}
    associated_wards={}
    associated_specialty={}
    associated_rooms={}
    for g in range(len(G)):  
        associated_wards[g]         =   []
        for w in range(len(W)):
            if G[g] in GW[w]:
                associated_wards[g].append(W[w])
        associated_rooms[g]         =   []
        for r in range(len(R)):
            if R[r] in RG[g]:
                associated_rooms[g].append(R[r])   
        associated_specialty[g]   =   []
        for s in range(len(S)):
            if S[s] in GS[s]:
                associated_specialty[g] = S[s] 
        
        multi[g] =[associated_wards[g],associated_rooms[g], associated_specialty[g]]
    
    group, associated_wards, associated_Rooms, associated_specialty = multidict(multi) 
    print(multi)
               

# ----- Reading/Creating Parameters ----- #
    F           =   float(parameters["Flexible Share"].values[0])           #Flexible Share             F
    E           =   int(parameters["Extended Time"].values[0])              #Extended time              E
    TC          =   int(parameters["Cleaning Time"].values[0])              #Cleaning Time              T^C
    I           =   int(parameters["Cycles in PP"].values[0])               #Cycles in Planning Period  I
    B           =   read_matrix(parameters,"B",nDays)                       #Bedward Capacity           B_(w,d)
    H           =   read_list(parameters, "Opening Hours")                  #Opening hours              H_(d)
    K           =   read_matrix(parameters,"K",nDays)                       #Team Capacity per day      K_(s,d)
    L           =   read_list(parameters,"Surgery Duration")                #Surgery uration            L_(g)
    U           =   read_list(parameters,"Max Extended Days")               #Max long days              U_(s)
    N           =   []                                                      #Open ORs each days         N_(d)
    for day in D:
        if day%7 == 0 or day%7 == 6:
            N.append(0) 
        else:
            N.append(len(R))     
    T           =   read_list(parameters,"Target Throughput")               #Target troughput           T_(g)
    Co          =   [element+TC for element in L]                           #Cost                       C_(g)
    J           =   read_list(parameters,"Max LOS",True)                    #Maximum LOS at the wards   J_(w)
    P           =   read_3d([MC, IC], "J", max(J))                          #Probabilies                P_(g,w,d)
    
    # ----- Scenario generation ----- #
    Q = generate_scenarios(G,T,nScenarios,seed)                             #Demand                     Q^T_(g,c)
    Pi=[]                                                                   #Probability of scenario    PI_(c)
    for scenario in C:
        Pi.append(1/nScenarios)

main("Old Model/Input/model_input.xlsx",10,1)