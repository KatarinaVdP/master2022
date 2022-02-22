
from typing import IO
from matplotlib.cbook import delete_masked_points
import pandas as pd
import math
import numpy as np
from scipy.stats import poisson
import gurobipy as gp
from gurobipy import GRB
from gurobipy import GurobiError
from gurobipy import quicksum
from sympy import gammasimp
import pickle
import abc
#from output_functions import categorize_slots


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
    return input_dict                  #Probabilies                P_(g,w,d)

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
            
def run_model(input_dict, time_limit):
    input = input_dict
    
    #----- Sets ----- #  
    nDays           =   input["nDays"]
    nWards          =   input["nWards"]
    nScenarios      =   input["nScenarios"]
    nGroups         =   input["nGroups"]
    nSpecialties    =   input["nSpecialties"]
    nRooms          =   input["nRooms"]
    
    Wi  =   input["Wi"]
    Si  =   input["Si"]
    Gi  =   input["Gi"]
    GWi =   input["GWi"]
    GSi =   input["GSi"]    
    Ri  =   input["Ri"]
    RSi =   input["RSi"]
    RGi =   input["RGi"]
    Di  =   input["Di"]
    Ci  =   input["Ci"]

    #----- Parameter ----- #  
    F   =   input["F"]
    E   =   input["E"]
    TC  =   input["TC"]
    I   =   input["I"]
    B   =   input["B"]
    H   =   input["H"]
    K   =   input["K"]
    L   =   input["L"]
    U   =   input["U"]
    N   =   input["N"]
    T   =   input["T"]
    Co  =   input["Co"]
    J   =   input["J"]
    P   =   input["P"]
    Pi  =   input["Pi"]
    Q   =   input["Q"]
    
    #----- Model ----- #
    m = gp.Model("mss_mip")
    m.setParam("TimeLimit", time_limit)
    
    '--- Variables ---'
    gamm    =   m.addVars(Si, Ri, Di, vtype=GRB.BINARY, name="gamma")
    lamb    =   m.addVars(Si, Ri, Di, vtype=GRB.BINARY, name="lambda")
    delt    =   m.addVars(Si, Ri, Di, Ci, vtype=GRB.BINARY, name="delta")
    x       =   m.addVars(Gi, Ri, Di, Ci, vtype=GRB.INTEGER, name="x")
    a       =   m.addVars(Gi, Ci, vtype=GRB.INTEGER, name="a")
    v       =   m.addVars(Wi, Di, vtype=GRB.CONTINUOUS, name="v")
    
    for s in Si:
        for r in (list(set(Ri)^set(RSi[s]))):
            for d in Di:
                gamm[s,r,d].lb=0
                gamm[s,r,d].ub=0
                for c in Ci:
                    delt[s,r,d,c].lb=0
                    delt[s,r,d,c].lb=0
    '--- Objective ---' 
    m.setObjective(
                quicksum(Pi[c] * Co[g] * a[g,c] for g in Gi for c in Ci)
    )
    m.ModelSense = GRB.MINIMIZE 
    '--- Constraints ---'
    m.addConstr(
        quicksum(gamm[s,r,d] for s in Si for r in RSi[s] for d in Di) - (1-F) * quicksum(N[d] for d in Di)  >= 0,
        name = "Con_PercentFixedRooms"
        )
    m.addConstrs(
        (lamb[s,r,d] <= gamm[s,r,d] for s in Si for r in Ri for d in Di), 
        name = "Con_RollingFixedSlotCycles",
        )
    m.addConstrs(
        (quicksum(lamb[s,r,d] for r in RSi[s] for d in Di) <= U[s] for s in Si),
        name = "Con_LongDaysCap",
    )
    print('still Creating Model 30%')
    m.addConstrs(
        (quicksum(gamm[s,r,d]+delt[s,r,d,c] for s in Si)<= 1 for r in Ri for d in Di for c in Ci),
        name= "Con_NoRoomDoubleBooking",
    )
    m.addConstrs(
        (quicksum(gamm[s,r,d]+delt[s,r,d,c] for r in RSi[s]) <= K[s][d] for s in Si for d in Di for c in Ci),
        name= "Con_NoTeamDoubleBooking",
    )
    m.addConstrs(
        (quicksum(gamm[s,r,d]+delt[s,r,d,c] for s in Si for r in Ri) <= N[d] for d in Di for c in Ci),
        name= "Con_TotalRoomsInUse",
    )
    m.addConstrs(
        (quicksum((L[g]+TC) * x[g,r,d,c] for g in GSi[s]) - H[d] * (gamm[s,r,d] + delt[s,r,d,c]) - E*lamb[s,r,d]<= 0 for s in Si for r in RSi[s] for d in Di for c in Ci),
        name = "Con_AvalibleTimeInRoom", 
    )
    print('still Creating Model 60%')
    m.addConstrs(
        (quicksum(x[g,r,d,c] for r in Ri for d in Di) + a[g,c] ==  Q[g][c] for g in Gi for c in Ci),
        name= "Con_Demand",
    )
    m.addConstrs(
        (quicksum(delt[s,r,d,c] for s in Si) <=
        quicksum(x[g,r,d,c] for g in Gi) for r in Ri for d in Di for c in Ci),
        name= "Con_OnlyAssignIfNecessary",
    )
    m.addConstrs(
        (quicksum(P[w][g][d-dd] * x[g,r,dd,c] for g in GWi[w] for r in Ri for dd in range(max(0,d+1-J[w]),d+1)) <= B[w][d] - v[w,d] for w in Wi for d in Di for c in Ci),
    name = "Con_BedOccupationCapacity",
    )
    print('still Creating Model 90%')
    m.addConstrs(
        (quicksum(Pi[c] * quicksum(P[w][g][d+nDays-dd] * x[g,r,dd,c] for g in GWi[w] for r in Ri for dd in range(d+nDays+1-J[w],nDays)) for c in Ci) 
        == v[w,d] for w in Wi for d in range(J[w]-1)),
    name = "Con_BedOccupationBoundaries",
    )
    m.addConstrs(
        (gamm[s,r,d]==gamm[s,r,nDays/I+d] for s in Si for r in RSi[s] for d in range(0,int(nDays-nDays/I))),
    name = "Con_RollingFixedSlotCycles",
    )   
    m.addConstrs(
        (lamb[s,r,d]==lamb[s,r,nDays/I+d] for s in Si for r in RSi[s] for d in range(0,int(nDays-nDays/I))),
    name = "Con_RollingExtendedSlotCycles",
    )
    print('Model Created 100%')

    m.optimize()
            
    result_dict =   {}
    result_dict["gamm"] = {k:v.X for k,v in gamm.items()}
    result_dict["lamb"] = {k:v.X for k,v in lamb.items()}
    result_dict["delt"] = {k:v.X for k,v in delt.items()}
    result_dict["x"]    = {k:v.X for k,v in x.items()}
    result_dict["a"]    = {k:v.X for k,v in a.items()}
    result_dict["v"]    = {k:v.X for k,v in v.items()}

    return result_dict
    
def categorize_slots(input_dict, output_dict):
        
        fixedSlot   =   [[0]*input_dict["nDays"]]*input_dict["nRooms"]
        flexSlot    =   [[0]*input_dict["nDays"]]*input_dict["nRooms"]
        extSlot     =   [[0]*input_dict["nDays"]]*input_dict["nRooms"]
        unassSlot   =   [[0]*input_dict["nDays"]]*input_dict["nRooms"]

        daysInCycle = int(input_dict["nDays"]/input_dict["I"])
        
        for r in input_dict["Ri"]:
            dayInCycle=0
            for d in input_dict["Di"]:
                dayInCycle=dayInCycle+1
                if dayInCycle>daysInCycle:
                    dayInCycle=1
                if sum(output_dict["delt"][(s,r,d,c)] for s in input_dict["Si"] for c in input_dict["Ci"])>0.5:
                    flexSlot[r][d]=1
                    for dd in input_dict["Di"]:
                        if (dd % daysInCycle) == dayInCycle:
                            flexSlot[r][dd]=1
                if sum(output_dict["gamm"][(s,r,d)] for s in input_dict["Si"])>0.5:
                    fixedSlot[r][d]=1
                    if sum(output_dict["lamb"][(s,r,d)] for s in input_dict["Si"])>0.5:
                        extSlot[r][d]=1
                if (fixedSlot[r][d]<0.5) and (flexSlot[r][d]<0.5):
                    unassSlot[r][d]=1
        
        output_dict["fixedSlot"]    = fixedSlot
        output_dict["flexSlot"]     = flexSlot
        output_dict["extSlot"]      = extSlot
        output_dict["unassSlot"]    = unassSlot
        return output_dict

def main(file_name, nScenarios, seed, time_limit, new_input=True):
    
    try:
        with open("file.pkl","rb") as f:
            results_saved = pickle.load(f)
        print("loading pickle")
        input           = read_input(file_name)
        input_update    = generate_scenarios(input,nScenarios,seed)
        results_update  = categorize_slots(input_update, results_saved )
        
        print(results_update["fixedSlot"])
        print(results_update["flexSlot"])
        """print("outside run_model():")
        x_sol = results_saved["x"]
        for g in input_update["Gi"]:
            for r in input_update["Ri"]:
                for d in input_update["Di"]:
                    for c in input_update["Ci"]:     
                        if x_sol[(g,r,d,c)]>0:
                            print("key", (g,r,c,d))
                            print("value",x_sol[(g,r,d,c)])"""
                    
                
    except IOError:
        input = read_input(file_name)
        print("Input has been read")

        input_update = generate_scenarios(input,nScenarios,seed)

        results = run_model(input_update,time_limit)
        print("Model run finished")

        print("outside run_model():")
        x_sol = results["x"]
        for g in input_update["Gi"]:
            for r in input_update["Ri"]:
                for d in input_update["Di"]:
                    for c in input_update["Ci"]:     
                        if x_sol[(g,r,d,c)]>0:
                            print("key", (g,r,c,d))
                            print("value",x_sol[(g,r,d,c)])
        with open("file.pkl","wb") as f:
            pickle.dump(results,f)

main("Old Model/Input/model_input.xlsx",10,1,15)