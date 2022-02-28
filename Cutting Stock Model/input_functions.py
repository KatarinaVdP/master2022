import pandas as pd
import math
import numpy as np
from scipy.stats import poisson


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

def read_matrix(sheet, prefix, numColombs):
        matrix_trans = []
        for i in range(numColombs):
            column = sheet[prefix + str(i + 1)].values
            sublist = []
            for j in column:
                if not math.isnan(j):
                    sublist.append(j)
            matrix_trans.append(sublist)
        matrix =  list(map(list, np.transpose(matrix_trans)))    
        return matrix

def read_3d(sheets, prefix, numColombs):
        cube = []
        for sheet in sheets:
            matrix = read_matrix(sheet, prefix, numColombs) 
            cube.append(matrix)
        return cube

def read_subset(matrix, affiliating_set, index_set):
        subset=[]
        subsetIndex=[]
        for i in range(len(index_set)):
            subsublist=[]
            subsublistIndex=[]
            for j in range(len(affiliating_set)):
                if int(matrix[i][j])==1:
                    subsublist.append(affiliating_set[j])
                    subsublistIndex.append(j)
            subset.append(subsublist) 
            subsetIndex.append(subsublistIndex)
        return subset, subsetIndex
        
def read_input(file_name):
    input_dict ={}
    file        =   file_name
    parameters  =   pd.read_excel(file, sheet_name='Parameters')
    sets        =   pd.read_excel(file, sheet_name='Sets')
    MC          =   pd.read_excel(file, sheet_name='MC')    
    IC          =   pd.read_excel(file, sheet_name='IC')  
                        
# ----- Reading/Creating sets -----
    '--- Set of Wards ---'
    input_dict["W"]     =   read_list(sets, "Wards")
    input_dict["nWards"] = len(input_dict["W"])
    input_dict["Wi"]    =   [i for i in range(input_dict["nWards"])]    
    '--- Set of Specialties ---'
    input_dict["S"]     =   read_list(sets, "Specialties")
    input_dict["nSpecialties"] = len(input_dict["S"])    
    input_dict["Si"]    =   [i for i in range(input_dict["nSpecialties"])]              
    '--- Set of Surgery Groups ---'
    input_dict["G"]     =   read_list(sets, "Surgery Groups")             
    input_dict["nGroups"] = len(input_dict["G"])    
    input_dict["Gi"]    =   [i for i in range(input_dict["nGroups"])]
    '--- Subset of Groups in Wards ---'
    GroupWard           =   read_matrix(sets,"Gr",len(input_dict["G"]))
    input_dict["GW"] , input_dict["GWi"]    =   read_subset(GroupWard,input_dict["G"],input_dict["W"])                         
    '--- Subset of Groups in Specialties ---'    
    GroupSpecialty      =   read_matrix(sets,"G",len(input_dict["G"]))
    input_dict["GS"], input_dict["GSi"]     =   read_subset(GroupSpecialty,input_dict["G"],input_dict["S"])
    '--- Set of Rooms ---'   
    input_dict["R"]     =   read_list(sets, "Operating Rooms") 
    input_dict["nRooms"] = len(input_dict["R"])
    input_dict["Ri"]    =   [i for i in range(input_dict["nRooms"])]                             
    '--- Subset of Rooms in Specialties ---' 
    RoomSpecialty       =   read_matrix(sets,"R",len(input_dict["R"])) 
    input_dict["RS"], input_dict["RSi"]     =   read_subset(RoomSpecialty,input_dict["R"],input_dict["S"])                 
    '--- Subset of Rooms for Groups ---'     
    input_dict["RG"] = []
    input_dict["RGi"] = []
    
    for g in range(len(input_dict["G"])):
        sublist = []
        for s in range(len(input_dict["S"])):
            if input_dict["G"][g] in input_dict["GS"][s]:
                sublist=input_dict["RS"][s]
                sublistIndex = []
                for i in range(len(sublist)):
                    j = input_dict["R"].index(sublist[i])
                    sublistIndex.append(j)
                break
        input_dict["RG"].append(sublist)   
        input_dict["RGi"].append(sublistIndex)   
    '--- Set of Days ---'  
    nDays = int(parameters["Planning Days"].values[0])
    input_dict["nDays"]= nDays
    input_dict["Di"]=[d for d in range(nDays)]

# ----- Reading/Creating Parameters ----- #
    input_dict["F"]     =   float(parameters["Flexible Share"].values[0])           #Flexible Share             F
    input_dict["E"]     =   int(parameters["Extended Time"].values[0])              #Extended time              E
    input_dict["TC"]    =   int(parameters["Cleaning Time"].values[0])              #Cleaning Time              T^C
    input_dict["I"]     =   int(parameters["Cycles in PP"].values[0])               #Cycles in Planning Period  I
    input_dict["B"]     =   read_matrix(parameters,"B",nDays)                       #Bedward Capacity           B_(w,d)
    input_dict["H"]     =   read_list(parameters, "Opening Hours")                  #Opening hours              H_(d)
    input_dict["K"]     =   read_matrix(parameters,"K",nDays)                       #Team Capacity per day      K_(s,d)
    input_dict["L"]     =   read_list(parameters,"Surgery Duration")                #Surgery uration            L_(g)
    input_dict["U"]     =   read_list(parameters,"Max Extended Days")               #Max long days              U_(s)
    
    input_dict["N"]     =   []                                                      #Open ORs each days         N_(d)
    for day in range(1,len(input_dict["Di"])+1):
        if day%7 == 0 or day%7 == 6:
            input_dict["N"].append(0) 
        else:
            input_dict["N"].append(len(input_dict["R"]))
    input_dict["T"]           =   read_list(parameters,"Target Throughput")               #Target troughput           T_(g)
    input_dict["Co"]          =   [element+input_dict["TC"] for element in input_dict["L"]]                           #Cost                       C_(g)
    input_dict["J"]            =   read_list(parameters,"Max LOS",True)                    #Maximum LOS at the wards   J_(w)
    input_dict["P"]            =   read_3d([MC, IC], "J", max(input_dict["J"]))                          #Probabilies                P_(g,w,d)
    return input_dict

def generate_scenarios(input_dict, nScenarios, seed):
        groups                  =   input_dict["G"]
        groups_index            =   input_dict["Gi"]
        targetTroughput         =   input_dict["T"]
        input_dict["nScenarios"]=   nScenarios
        input_dict["seed"]      =   seed
        input_dict["Ci"]        =   [c for c in range(nScenarios)]                             
        input_dict["Pi"]        =   [1/nScenarios]*nScenarios

        scenarioMatrix=[]
        np.random.seed(seed)
        for i in range(nScenarios):
            randVec             =   np.random.rand(1,len(groups))
            scenarioPre         =   poisson.ppf(randVec, targetTroughput)
            scenario            =   []
            for group in groups_index:
                scenario.append(int(scenarioPre[0][group]))
            scenarioMatrix.append(scenario)  
        
        transposed_matrix       =   list(map(list, np.transpose(scenarioMatrix))) 
        input_dict["Q"]         =   transposed_matrix
        
        return input_dict