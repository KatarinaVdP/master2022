
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

def generate_scenarios(groups, targetTroughput, nScenarios, seed):
        scenarioMatrix=[]
        np.random.seed(seed)
        for i in range(nScenarios):
            randVec=np.random.rand(1,len(groups))
            scenarioPre=poisson.ppf(randVec, targetTroughput)
            scenario=[]
            for group in range(len(groups)):
                scenario.append(int(scenarioPre[0][group]))
            scenarioMatrix.append(scenario)
        Ci  =   [c for c in range(nScenarios)] #DemandQ_(g,c)
        Pi  =   [1/nScenarios]*nScenarios                                                                   #Probability of scenario    PI_(c)
        transposed_matrix = list(map(list, np.transpose(scenarioMatrix))) 
        return transposed_matrix, Ci, Pi


class old_model:
    def __init__(self):
        '--- Sets ---'
        self.W      =   []
        self.Wi     =   []
        self.S      =   []
        self.Si     =   []
        self.G      =   []
        self.Gi     =   []
        self.GW     =   []
        self.GWi    =   []
        self.GS     =   []
        self.GSi    =   []
        self.R      =   []
        self.Ri     =   []
        self.RSi    =   []
        self.RG     =   []
        self.RGi    =   []
        self.Di     =   []
        self.Ci     =   []
        '--- Parameters ---'
        self.F      =   0
        self.E      =   0
        self.TC     =   0
        self.I      =   0
        self.B      =   []
        self.H      =   []
        self.K      =   []
        self.L      =   []
        self.U      =   []
        self.N      =   []
        self.T      =   []
        self.Co     =   []
        self.J      =   []
        self.P      =   []
        self.Q      =   []
        self.Pi     =   []
        
        '--- others ---'
        self.nDays       =   0
        self.nSpecialties =  0
        self.nGroups     =   0
        self.nRooms      =   0
        
        # Skriv om så matrisene ikke er hardkodet
        self.fixedSlot   =   []
        self.flexSlot    =   []
        self.extSlot     =   []
        self.unassSlot   =   []
        
        '--- Last solution ---'
        self.gamm_sol    = []
        self.delt_sol    = []
        self.lamb_sol    = []
        self.x_sol       = []
        self.a_sol       = []
        self.v_sol       = []
        
    def read_input(self,file_name):
        file        =   file_name
        parameters  =   pd.read_excel(file, sheet_name='Parameters')
        sets        =   pd.read_excel(file, sheet_name='Sets')
        MC          =   pd.read_excel(file, sheet_name='MC')    
        IC          =   pd.read_excel(file, sheet_name='IC')  
                            
    # ----- Reading/Creating sets -----
        '--- Set of Wards ---'
        self.W     =   read_list(sets, "Wards")
        self.nWards =  len(self.W)
        self.Wi    =   [i for i in range(self.nWards)]    
        '--- Set of Specialties ---'
        self.S     =   read_list(sets, "Specialties")
        self.nSpecialties = len(self.S)
        self.Si    =   [i for i in range(self.nSpecialties)]              
        '--- Set of Surgery Groups ---'
        self.G     =   read_list(sets, "Surgery Groups")
        self.nGroups = len(self.G)             
        self.Gi    =   [i for i in range(self.nGroups)]
        '--- Subset of Groups in Wards ---'
        GroupWard           =   read_matrix(sets,"Gr",self.nGroups)
        self.GW , self.GWi    =   read_subset(GroupWard,self.G,self.W)                         
        '--- Subset of Groups in Specialties ---'    
        GroupSpecialty      =   read_matrix(sets,"G",self.nGroups)
        self.GS, self.GSi     =   read_subset(GroupSpecialty,self.G,self.S)
        '--- Set of Rooms ---'   
        self.R     =   read_list(sets, "Operating Rooms") 
        self.nRooms=    len(self.R)
        self.Ri    =   [i for i in range(self.nRooms)]                             
        '--- Subset of Rooms in Specialties ---' 
        RoomSpecialty       =   read_matrix(sets,"R",self.nRooms) 
        self.RS, self.RSi     =   read_subset(RoomSpecialty,self.R,self.S)                 
        '--- Subset of Rooms for Groups ---'     
        for g in range(len(self.G)):
            sublist = []
            for s in range(len(self.S)):
                if self.G[g] in self.GS[s]:
                    sublist=self.RS[s]
                    sublistIndex = []
                    for i in range(len(sublist)):
                        j = self.R.index(sublist[i])
                        sublistIndex.append(j)
                    break
            self.RG.append(sublist)   
            self.RGi.append(sublistIndex)
        '--- Set of Days ---'  
        self.nDays = int(parameters["Planning Days"].values[0])
        self.Di=[d for d in range(self.nDays)]

    # ----- Reading/Creating Parameters ----- #
        self.F     =   float(parameters["Flexible Share"].values[0])           #Flexible Share             F
        self.E     =   int(parameters["Extended Time"].values[0])              #Extended time              E
        self.TC    =   int(parameters["Cleaning Time"].values[0])              #Cleaning Time              T^C
        self.I     =   int(parameters["Cycles in PP"].values[0])               #Cycles in Planning Period  I
        self.B     =   read_matrix(parameters,"B",self.nDays)                       #Bedward Capacity           B_(w,d)
        self.H     =   read_list(parameters, "Opening Hours")                  #Opening hours              H_(d)
        self.K     =   read_matrix(parameters,"K",self.nDays)                       #Team Capacity per day      K_(s,d)
        self.L     =   read_list(parameters,"Surgery Duration")                #Surgery uration            L_(g)
        self.U     =   read_list(parameters,"Max Extended Days")               #Max long days              U_(s)
                                                            #Open ORs each days         N_(d)
        for day in range(1,self.nDays+1):
            if day%7 == 0 or day%7 == 6:
                self.N.append(0) 
            else:
                self.N.append(self.nRooms)
        self.T           =   read_list(parameters,"Target Throughput")               #Target troughput           T_(g)
        self.Co          =   [element+self.TC for element in self.L]                           #Cost                       C_(g)
        self.J            =   read_list(parameters,"Max LOS",True)                    #Maximum LOS at the wards   J_(w)
        self.P            =   read_3d([MC, IC], "J", max(self.J))                          #Probabilies                P_(g,w,d)

    """def cathegorize_slots(self):
        daysInCycle = int(self.nDays/self.I)
        for r in self.Ri:
            dayInCycle=0
            for d in self.Di:
                dayInCycle=dayInCycle+1
                if dayInCycle>daysInCycle:
                    dayInCycle=1
                if sum(self.delt[s][r][d][c] for s in self.Si for c in self.Ci)>0.5:
                    self.flexSlot[r][d]=1
                    for dd in self.Di:
                        if (dd % daysInCycle) == dayInCycle:
                            self.flexSlot[r][dd]=1
                if sum(self.gamm[s][r][d] for s in self.Si)>0.5:
                    self.fixedSlot[r][d]=1
                    if sum(self.lamb[s][r][d] for s in self.Si)>0.5:
                        self.extSlot[r][d]=1
                if (self.fixedSlot[r][d]<0.5) and (self.flexSlot[r][d]<0.5):
                    self.unassSlot[r][d]=1"""
            
    def run_model(self, nScenarios, seed, time_limit):
    
        # ----- Scenario generation ----- #
        self.Q, self.Ci, self.Pi  =   generate_scenarios(self.G, self.T, nScenarios, seed)                 #Demand                     Q_(c,g) 
        print("Scenarios Created")
        
        #----- Model ----- #
        m = gp.Model("mss_mip")
        m.setParam("TimeLimit", time_limit)
        
        #----- Sets ----- #  
        Wi  =   self.Wi
        Si  =   self.Si
        Gi  =   self.Gi
        GWi =   self.GWi
        GSi =   self.GSi   
        Ri  =   self.Ri
        RSi =   self.RSi
        RGi =   self.RGi
        Di  =   self.Di
        Ci  =   self.Ci

        #----- Parameter ----- #  
        F   =   self.F
        E   =   self.E
        TC  =   self.TC
        I   =   self.I
        B   =   self.B
        H   =   self.H
        K   =   self.K
        L   =   self.L
        U   =   self.U
        N   =   self.N
        T   =   self.T
        Co  =   self.Co
        J   =   self.J
        P   =   self.P
        Pi  =   self.Pi
        Q   =   self.Q
        nDays = self.nDays


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
            (quicksum(lamb[s,r,d]for r in RSi[s] for d in Di) <= U[s] for s in Si),
            name = "Con_LongDaysCap",
        )
        print('still Creating Model-0')
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
            (quicksum((L[g]+TC) * x[g,r,d,c] for g in GSi[s]) - H[d] * (gamm[s,r,d] + delt[s,r,d,c]) - E*lamb[s,r,d]<= 0 for r in RSi[s] for s in Si for d in Di for c in Ci),
            name = "Con_AvalibleTimeInRoom",        # burde disse bytte plass?
        )
        print('still Creating Model0')
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
        print('still Creating Model1')
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
            (lamb[s,r,d]==lamb[s,r,nDays/I+d] for r in RSi[s] for s in Si for d in range(0,int(nDays-nDays/I))),
        name = "Con_RollingExtendedSlotCycles",
        )
        print('still Creating Model2')

        '''v=m.getVars()
        print(v)'''
        m.write("formulation.rlp")
        m.optimize()
        
        self.flexSlot = [[0]*self.nDays]*self.nRooms
        self.fixedSlot = [[0]*self.nDays]*self.nRooms     
        self.extSlot = [[0]*self.nDays]*self.nRooms
        self.unassSlot = [[0]*self.nDays]*self.nRooms
                    
        self.gamm_sol    = [[[0]*self.nDays]*self.nRooms]*self.nSpecialties
        self.lamb_sol    = [[[0]*self.nDays]*self.nRooms]*self.nSpecialties
        self.delt_sol    = [[[[0]*nScenarios]*self.nDays]*self.nRooms]*self.nSpecialties
        self.x_sol       = [[[[0]*nScenarios]*self.nDays]*self.nRooms]*self.nGroups
        self.a_sol       = [[0]*nScenarios]*self.nGroups
        self.v_sol       = [[0]*self.nDays]*self.nWards
        
        for s in self.Si:
            for r in self.Ri:
                for d in self.Di:
                    self.gamm_sol[s][r][d] = gamm[s,r,d].X
                    self.lamb_sol[s][r][d] = lamb[s,r,d].X
                    for c in self.Ci:
                        self.delt_sol[s][r][d][c] = delt[s,r,d,c].X
        
        print("Printing Gurobi-variables within run_model():")
        for g in self.Gi:
            for r in self.Ri:
                for d in self.Di:
                    for c in self.Ci:
                        if x[g,r,d,c].X > 0.5:
                            print("x[%d,%d,%d,%d] = %d" % (g,r,d,c,x[g,r,d,c].X))
                            self.x_sol[g][r][d][c] = x[g,r,d,c].X
        
        """for g in self.Gi:
            for r in self.Ri:
                for d in self.Di:
                    for c in self.Ci:
                        if self.x_sol[g][r][d][c] > 0:
                            print("x[%d][%d][%d][%d] = %d" % (g,r,d,c,self.x_sol[g][r][d][c]))"""
        
        for g in self.Gi:
            for c in self.Ci:
                self.a_sol[g][c] = a[g,c].X
        for w in self.Wi:
            for d in self.Di:
                self.v_sol[w][d] = v[w,d].X
        return {x.varName: x.X}

def categorize_slots(objekt):
        daysInCycle = int(objekt.nDays/objekt.I)
        for r in objekt.Ri:
            dayInCycle=0
            for d in objekt.Di:
                dayInCycle=dayInCycle+1
                if dayInCycle>daysInCycle:
                    dayInCycle=1
                if sum(objekt.delt_sol[s][r][d][c] for s in objekt.Si for c in objekt.Ci)>0.5:
                    objekt.flexSlot[r][d]=1
                    for dd in objekt.Di:
                        if (dd % daysInCycle) == dayInCycle:
                            objekt.flexSlot[r][dd]=1
                if sum(objekt.gamm_sol[s][r][d] for s in objekt.Si)>0.5:
                    objekt.fixedSlot[r][d]=1
                    if sum(objekt.lamb_sol[s][r][d] for s in objekt.Si)>0.5:
                        objekt.extSlot[r][d]=1
                if (objekt.fixedSlot[r][d]<0.5) and (objekt.flexSlot[r][d]<0.5):
                    objekt.unassSlot[r][d]=1


def main(file_name, nScenarios, seed, time_limit, new_input=True):
    
    oldModel = old_model()
    
    oldModel.read_input(file_name)
    print("Input has been read")
    
    x = oldModel.run_model(nScenarios, seed, time_limit)
    print("Model run finished")
    
    print("Printing output dictionary")
    print(x)
    
    """print("Copying x-values and printing outside run_model():")
    for g in oldModel.Gi:
        for r in oldModel.Ri:
            for d in oldModel.Di:
                for c in oldModel.Ci:
                    if x[g,r,d,c] > 0.5:
                        print("x[%d][%d][%d][%d] = %d" % (g,r,d,c,oldModel.x_sol[g][r][d][c]))"""
    
    
    """tryfor g in oldModel.Gi:
        for c in oldModel.Ci:
            print(oldModel.a_sol[g][c])  
    
    
    
    print("These gamma-values survived:")    
    for s in oldModel.Si:
        for r in oldModel.Ri:
            for d in oldModel.Di:
                val = oldModel.gamm_sol[s][r][d]
                if val > 0.5:
                    print("gamma[%d][%d][%d] = %d" % (s,r,d,val))
                    
    print("These delta-values survived:")    
    for s in oldModel.Si:
        for r in oldModel.Ri:
            for d in oldModel.Di:
                for c in oldModel.Ci:
                        val = oldModel.delt_sol[s][r][d][c]
                        if val > 0.5:
                            print("delta[%d][%d][%d][%d] = %d" % (s,r,d,c,val))"""
  
    """try:
        with open("file.pkl","rb") as f:
            variablesSaved = pickle.load(f)
            
            print(variablesSaved.Ri)
            print(variablesSaved.Di)
            print(variablesSaved.flexSlot)
            print(variablesSaved.fixedSlot)
            print(variablesSaved.extSlot)
            print(variablesSaved.unassSlot)
            print()
            print("Trying to categorize slots:")
            categorize_slots(variablesSaved)
            print(variablesSaved.flexSlot)
            print(variablesSaved.fixedSlot)
            print(variablesSaved.extSlot)
            print()
            print("Printing gammas:")
            print(variablesSaved.gamm_sol)
            print("Printing a:")
            print(variablesSaved.a_sol)"""
            
            
    """except IOError:
        oldModel = old_model()
    
        oldModel.read_input(file_name)
        print("Input has been read")
        
        oldModel.run_model(nScenarios, seed, time_limit)
        print("Model run finished")
        
        for g in oldModel.Gi:
            for c in oldModel.Ci:
                print(oldModel.a_sol[g][c])
        
        with open("file.pkl","wb") as f:
            pickle.dump(oldModel,f)
        print("Do you see the pickle?")"""
        


main("Old Model/Input/model_input.xlsx",10,1,15)