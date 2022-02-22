from scipy.stats import poisson
import gurobipy as gp
from gurobipy import GRB
from gurobipy import GurobiError
from gurobipy import quicksum


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
    
    print("inside run_model(): gamm")
    for s in input["Si"]:
        for r in input["Ri"]:
            for d in input["Di"]:    
                if gamm[s,r,d].X>0:
                    print("key", (s,r,d))
                    print("value",gamm[s,r,d].X)
                    
    print("inside model from dictionary")
    gamm_sol = result_dict["gamm"]
    for s in input["Si"]:
        for r in input["Ri"]:
            for d in input["Di"]:    
                if gamm_sol[s,r,d]>0:
                    print("key", (s,r,d))
                    print("value",gamm_sol[s,r,d])

    return result_dict
    