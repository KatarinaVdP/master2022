
import pandas as pd
import math
import numpy as np
from scipy.stats import poisson
import gurobipy as gp
from gurobipy import GRB
from gurobipy import GurobiError
from gurobipy import quicksum


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

def main(file_name,nScenarios,seed,newInput=True):

    file        =   file_name
    parameters  =   pd.read_excel(file, sheet_name='Parameters')
    sets        =   pd.read_excel(file, sheet_name='Sets')
    MC          =   pd.read_excel(file, sheet_name='MC')    
    IC          =   pd.read_excel(file, sheet_name='IC')  
                        
# ----- Reading/Creting sets -----
    '--- Set of Wards ---'
    W                   =   read_list(sets, "Wards")
    Wi                  =   [i for i in range(len(W))]           
    print("W:=")
    print(W)
    print("Wi:=")
    print(Wi)
    '--- Set of Specialties ---'
    S                   =   read_list(sets, "Specialties")  
    Si                  =   [i for i in range(len(S))]              
    print("S:=")
    print(S)
    print("Si:=")
    print(Si)
    '--- Set of Surgery Groups ---'
    G                   =   read_list(sets, "Surgery Groups")             
    Gi                  =   [i for i in range(len(G))]
    print("G:=")
    print(G)
    print("Gi:=")
    print(Gi)
    '--- Subset of Groups in Wards ---'
    GroupWard           =   read_matrix(sets,"Gr",len(G))
    GW , GWi            =   read_subset(GroupWard,G,W)                         
    print("GW:=")
    print(GW)
    print("GWi:=")
    print(GWi)
    '--- Subset of Groups in Specialties ---'    
    GroupSpecialty      =   read_matrix(sets,"G",len(G))
    GS, GSi             =   read_subset(GroupSpecialty,G,S)
    print("GS:=")
    print(GS)
    print("GSi:=")
    print(GSi)
    '--- Set of Rooms ---'   
    R                   =   read_list(sets, "Operating Rooms") 
    print("R:=")
    print(R)
    Ri                  =   [i for i in range(len(R))]
    print("Ri:=")
    print(Ri)                                      
    '--- Subset of Rooms in Specialties ---' 
    RoomSpecialty       =   read_matrix(sets,"R",len(R)) 
    RS, RSi             =   read_subset(RoomSpecialty,R,S)                 
    print("RS:=")
    print(RS)  
    print("RSi:=")
    print(RSi)    
    '--- Subset of Rooms for Groups ---'     
    RG                  =   []
    RGi                 =   []
    for g in range(len(G)):
        sublist = []
        for s in range(len(S)):
            if G[g] in GS[s]:
                sublist=RS[s]
                sublistIndex = []
                for i in range(len(sublist)):
                    j = R.index(sublist[i])
                    sublistIndex.append(j)
                break
        RG.append(sublist)
        RGi.append(sublistIndex)
    print("RG:=")
    print(RG)
    print("RGi:=")
    print(RGi)
    '--- Set of Days ---'  
    D                   =   []
    Di = []
    nDays = int(parameters["Planning Days"].values[0])
    for d in range(1,nDays+1):
        D.append(d) 
    print("D:=")
    print(D)
    Di=[d for d in range(nDays)]
    print("Di:=")
    print(Di)
    '--- Set of Scenarios ---'
    C                   =   []                                                                                 
    for scenario in range(1,nScenarios+1):
        C.append(scenario)  
    print("C:=")
    print(C)
    Ci=[c for c in range(nScenarios)]
    print("Ci:=")
    print(Ci)   

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
    Q_trans     =   generate_scenarios(G,T,nScenarios,seed)                 #Demand                     Q_(c,g)
    Q           =   list(map(list, np.transpose(Q_trans)))                  #Demand                     Q_(g,c)
    Pi=[]                                                                   #Probability of scenario    PI_(c)
    for c in Ci:
        Pi.append(1/nScenarios)
    
    print("New Instances created")
#----- Model ----- #
    m = gp.Model("mss_mip")
    m.setParam("TimeLimit", 30)
    
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
                quicksum(Pi[c] * Co[g] * a[g,c] 
                for g in Gi 
                for c in Ci)
    )
    m.ModelSense = GRB.MINIMIZE
    
    '--- Constraints ---'
    m.addConstr(
        quicksum(gamm[s,r,d]
            for s in Si
            for r in Ri
            for d in Di) 
        - (1-F) * quicksum(N[d] for d in Di)  
        >= 0,
        name = "Con_PercentFixedRooms")

    m.addConstrs(
        (lamb[s,r,d] <= gamm[s,r,d] 
        for s in Si
        for r in Ri
        for d in Di),
        name = "Con_RollingFixedSlotCycles",
    )

    m.addConstrs(
        (quicksum(lamb[s,r,d]
                for r in RSi[s]
                for d in Di)
        <= U[s] 
        for s in Si),
        name = "Con_LongDaysCap",
    )

    m.addConstrs(
        (quicksum(gamm[s,r,d]+delt[s,r,d,c]
                for s in Si)
        <= 1
        for r in RSi[s]
        for d in Di
        for c in Ci),
        name= "Con_NoRoomDoubleBooking",
    )

    m.addConstrs(
        (quicksum(gamm[s,r,d]+delt[s,r,d,c]
                for r in RSi[s])
        <= K[s][d]
        for s in Si
        for d in Di
        for c in Ci),
        name= "Con_NoTeamDoubleBooking",
    )
    
    m.addConstrs(
        (quicksum(gamm[s,r,d]+delt[s,r,d,c]
                for s in Si
                for r in Ri)
        <= N[d]
        for d in Di
        for c in Ci),
        name= "Con_TotalRoomsInUse",
    )
    
    m.addConstrs(
        (quicksum((L[g]+TC) * x[g,r,d,c] for g in GSi[s]) 
        - H[d] * (gamm[s,r,d] + delt[s,r,d,c]) 
        - E*lamb[s,r,d]
        <= 0
        for r in RSi[s]              # burde disse bytte plass?
        for s in Si                  # burde disse bytte plass?
        for d in Di
        for c in Ci),
        name = "Con_AvalibleTimeInRoom",
    )

    m.addConstrs(
        (quicksum(x[g,r,d,c]
                for r in Ri
                for d in Di)
        +   a[g,c] 
        ==  Q[g][c]
        for g in Gi
        for c in Ci),
        name= "Con_Demand",
    )
    
    m.addConstrs(
        (quicksum(delt[s,r,d,c]
                for s in Si) <=
        quicksum(x[g,r,d,c]
                for g in Gi)
        for r in Ri
        for d in Di
        for c in Ci),
        name= "Con_OnlyAssignIfNecessary",
    )
    print("Wi:=")
    print(Wi)
    print("Di:=")
    print(Di)
    print("Ci:=")
    print(Ci)
    print("GWi:=")
    print(GWi)
    print("Ri:=")
    print(Ri)
    print("nDays:=")
    print(nDays)
    print("J:=")
    print(J)
    print("P:=")
    print(P)
    print(len(P[0]))
    print(len(P[1]))
    print(len(P[0][0]))
    m.addConstrs(
        (quicksum( Pi[c] * quicksum(P[w][g][d-dd+1] * x[g,r,dd,c] 
                                for g in GWi[w]
                                for r in Ri
                                for dd in range(max(0,d+1-J[w]),d+1))
                for c in Ci)
        <= B[w][d] - v[w,d]
        for w in Wi
        for d in Di
        for c in Ci),
    name = "Con_BedOccupationCapacity",
    )

    m.addConstrs(
        (quicksum(P[w][g][d+nDays+1-dd] * x[g,r,dd,c] 
                for g in GWi[w]
                for r in Ri
                for dd in range(d+nDays+1-J[w],nDays)) ==
        v[w,d]
        for w in Wi
        for d in range(J[w])
        for c in Ci),
    name = "Con_BedOccupationBoundaries",
    )
    
    m.addConstrs(
        (gamm[s,r,d]==gamm[s,r,nDays/I+d]
        for s in Si
        for r in RSi[s]
        for d in range(1,nDays-nDays/I)),
    name = "Con_RollingFixedSlotCycles",
    )
        
    m.addConstrs(
        (lamb[s,r,d]==lamb[s,r,nDays/I+d]
        for r in RSi[s]
        for s in Si
        for d in range(1,nDays-nDays/I)),
    name = "Con_RollingFixedSlotCycles",
    )

    m.optimize()
        
"""    m.addConstrs(
        gamm[s,r,d]==0
        for r in (Ri - RSi[s])
        for s in Si
        for d in D)
    name = "Con_FixingIllegalGammas"
    )
    
    m.addConstrs(
        delt[s,r,d,c]==0
        for r in (Ri - RSi[s])
        for s in Si
        for d in D
        for c in C)
    name = "Con_FixingIllegalDeltas"
    )"""
    
    
    
    
    
main("Old Model/Input/model_input.xlsx",10,1,True)

