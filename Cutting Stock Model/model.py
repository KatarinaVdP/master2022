from scipy.stats import poisson
import gurobipy as gp
from gurobipy import GRB
from gurobipy import GurobiError
from gurobipy import quicksum
from patterns import generate_pattern_data

def run_model(input, number_of_groups, flexibility, time_limit):
    
    #----- Sets ----- #  
    nDays           =   input["nDays"]
    nWards          =   input["nWards"]
    nScenarios      =   input["nScenarios"]
    nGroups         =   input["nGroups"]
    nSpecialties    =   input["nSpecialties"]
    nRooms          =   input["nRooms"]
    

    Wi      =   input["Wi"]
    Si      =   input["Si"]
    Gi      =   input["Gi"]
    GWi     =   input["GWi"]
    GSi     =   input["GSi"]    
    Ri      =   input["Ri"]
    RSi     =   input["RSi"]
    RGi     =   input["RGi"]
    Di      =   input["Di"]
    Ci      =   input["Ci"]

    #----- Parameter ----- #  
    F   =   flexibility
    input["F"]  = flexibility
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
    Pi  =   input["Pi"]
    Q   =   input["Q"]
    P   =   input["P"]
    Y   =   input["Y"]
    
    input = generate_pattern_data(input)
    
    # Parameters and sets specific to cutting stock model
    A       =   input["A"]
    Psum    =   input["Psum"]
    Mi      =   input["Mi"]
    Mnxi    =   input["Mnxi"]
    Mxi     =   input["Mxi"]
    MSi     =   input["MSi"]

 
    #----- Model ----- #
    m = gp.Model("mss_mip")
    m.setParam("TimeLimit", time_limit)
    
    '--- Variables ---'
    gamm    =   m.addVars(Si, Ri, Di, vtype=GRB.BINARY, name="gamma")
    lamb    =   m.addVars(Si, Ri, Di, vtype=GRB.BINARY, name="lambda")
    delt    =   m.addVars(Si, Ri, Di, Ci, vtype=GRB.BINARY, name="delta")
    pat     =   m.addVars(Mi, Ri, Di, Ci, vtype=GRB.BINARY, name="pat")
    a       =   m.addVars(Gi, Ci, vtype=GRB.INTEGER, name="a")
    """v       =   m.addVars(Wi, Di, vtype=GRB.CONTINUOUS, name="v")"""

    for s in Si:
        for r in (list(set(Ri)^set(RSi[s]))):
            for d in Di:
                gamm[s,r,d].lb=0
                gamm[s,r,d].ub=0
                lamb[s,r,d].lb=0
                lamb[s,r,d].ub=0
                for c in Ci:
                    delt[s,r,d,c].lb=0
                    delt[s,r,d,c].ub=0
    """for s in Si:
        for m in MSi[s]:
            for r in (list(set(Ri)^set(RSi[s]))):
                for d in Di:
                    for c in Ci:
                        pat[m,r,d,c].lb=0
                        pat[m,r,d,c].ub=0   """         
    
    '--- Objective ---' 
    m.setObjective(
                quicksum(Pi[c] * Co[g] * a[g,c] for g in Gi for c in Ci)
    )
    m.ModelSense = GRB.MINIMIZE 
    '--- Constraints ---'
    m.addConstr(
        quicksum( quicksum(gamm[s,r,d] for r in RSi[s]) for s in Si for d in Di) - (1-F) * quicksum(N[d] for d in Di)  >= 0,
        name = "Con_PercentFixedRooms"
        )
    for s in Si:
        m.addConstrs(
            (lamb[s,r,d] <= gamm[s,r,d] 
            for r in RSi[s] for d in Di), 
            name = "Con_RollingFixedSlotCycles"+ str(s),
            )
    m.addConstrs(
        (quicksum(lamb[s,r,d] for r in RSi[s] for d in Di) <= U[s] 
        for s in Si),
        name = "Con_LongDaysCap",
    )
    print('still Creating Model 30%')
    m.addConstrs(
        (quicksum(gamm[s,r,d]+delt[s,r,d,c] for s in Si)<= 1 
        for r in Ri for d in Di for c in Ci),
        name= "Con_NoRoomDoubleBooking",
    )
    m.addConstrs(
        (quicksum(gamm[s,r,d]+delt[s,r,d,c] for r in RSi[s]) <= K[s][d] 
        for s in Si for d in Di for c in Ci),
        name= "Con_NoTeamDoubleBooking",
    )
    m.addConstrs(
        (quicksum(gamm[s,r,d]+delt[s,r,d,c] for s in Si for r in Ri) <= N[d] 
        for d in Di for c in Ci),
        name= "Con_TotalRoomsInUse",
    )
    m.addConstrs(
        (quicksum(pat[m,r,d,c] for m in MSi[s]) <= gamm[s,r,d]+delt[s,r,d,c]
        for s in Si for r in Ri for d in Di for c in Ci),
        name = "Con_CorrectPatternForSpecialty",
    )
    m.addConstrs(
        (2*quicksum(pat[m,r,d,c] for m in Mxi) + quicksum(pat[m,r,d,c] for m in Mnxi) <= quicksum(gamm[s,r,d] + delt[s,r,d,c]+lamb[s,r,d] for s in Si)
        for r in Ri for d in Di for c in Ci),
        name = "Con_AvalibleTimeInRoom", 
    )   
    m.addConstrs(
        (quicksum(A[m][g]*pat[m,r,d,c] for m in Mi for r in RGi[g] for d in Di) + a[g,c] ==  Q[g][c] 
        for g in Gi for c in Ci),
        name= "Con_Demand",
    )
    m.addConstrs(
        (quicksum(A[m][g]*pat[m,r,d,c] for m in Mnxi for g in Gi) >= quicksum(delt[s,r,d,c] for s in Si) 
        for r in Ri for d in Di for c in Ci),
        name= "Con_OnlyAssignIfNecessary",
    )
    print('still Creating Model 60%')
    m.addConstrs(
        (quicksum(Psum[m][w][d-dd] * pat[m,r,dd,c] for m in Mi for r in Ri for dd in range(max(0,d+1-J[w]),d+1)) <= B[w][d] - Y[w][d] 
        for w in Wi for d in Di for c in Ci),
    name = "Con_BedOccupationCapacity",
    )
    """m.addConstrs(
        (quicksum(Psum[m][w][d-dd] * pat[m,r,dd,c] for m in Mi for r in Ri for dd in range(max(0,d+1-J[w]),d+1)) <= B[w][d] - v[w,d] 
        for w in Wi for d in Di for c in Ci),
    name = "Con_BedOccupationCapacity",
    )
    print('still Creating Model 90%')
    for w in Wi:
        m.addConstrs(
            (quicksum(Pi[c] * quicksum(Psum[m][w][d+nDays-dd] * pat[m,r,dd,c] for m in Mi for r in Ri for dd in range(d+nDays+1-J[w],nDays)) for c in Ci) == v[w,d] 
            for d in range(J[w]-1)),
        name = "Con_BedOccupationBoundaries" + str(w),
        )"""
    for s in Si:
        m.addConstrs(
            (gamm[s,r,d]==gamm[s,r,nDays/I+d] 
            for r in RSi[s] for d in range(0,int(nDays-nDays/I))),
        name = "Con_RollingFixedSlotCycles" + str(s),
        )
    for s in Si:   
        m.addConstrs(
            (lamb[s,r,d]==lamb[s,r,nDays/I+d]  
            for r in RSi[s] for d in range(0,int(nDays-nDays/I))),
        name = "Con_RollingExtendedSlotCycles" + str(s),
        )
    print('Model Created 100%')

    m.optimize()
    
    # ----- Copying the desicion variable values to result dictionary -----
    result_dict =   {}
    result_dict["gamm"] = [[[0 for _ in range(input["nDays"])] for _ in range(input["nRooms"])] for _ in range(input["nSpecialties"])]
    result_dict["lamb"] = [[[0 for _ in range(input["nDays"])] for _ in range(input["nRooms"])] for _ in range(input["nSpecialties"])]
    result_dict["delt"] = [[[[0 for _ in range(input["nScenarios"])] for _ in range(input["nDays"])] for _ in range(input["nRooms"])] for _ in range(input["nSpecialties"])]
    result_dict["x"]    = [[[[0 for _ in range(input["nScenarios"])] for _ in range(input["nDays"])] for _ in range(input["nRooms"])] for _ in range(input["nGroups"])]
    result_dict["phi"]  = [[[[0 for _ in range(input["nScenarios"])] for _ in range(input["nDays"])] for _ in range(input["nRooms"])] for _ in range(len(Mi))]
    result_dict["a"]    = [[0 for _ in range(input["nScenarios"])] for _ in range(input["nGroups"])]
    result_dict["v"]    = [[0 for _ in range(input["nDays"])] for _ in range(input["nWards"])]
    
    for s in input["Si"]:
        for r in input["Ri"]:
            for d in input["Di"]:    
                if gamm[s,r,d].X > 0:
                    result_dict["gamm"][s][r][d] = gamm[s,r,d].X
                if lamb[s,r,d].X > 0:
                    result_dict["lamb"][s][r][d] = lamb[s,r,d].X
                for c in input["Ci"]:
                    if delt[s,r,d,c].X > 0:
                        result_dict["delt"][s][r][d][c] = delt[s,r,d,c].X                     
        
    for g in input["Gi"]:
        for r in input["Ri"]:
            for d in input["Di"]:    
                for c in input["Ci"]:
                    val = sum(A[m][g]*pat[m,r,d,c].X for m in Mi)
                    if val > 0:
                        result_dict["x"][g][r][d][c] = val
    """for m in Mi:
        for r in Ri:
            for d in Di:
                for c in Ci:
                    val = pat[m,r,d,c].X
                    if val > 0:
                        result_dict["phi"][m][r][d][c] = val"""
                        
                        
    for g in input["Gi"]:
        for c in input["Ci"]:
            if a[g,c].X > 0:
                result_dict["a"][g][c] = a[g,c].X
    """for w in input["Wi"]:
        for d in input["Di"]:
            if v[w,d].X > 0:
                result_dict["v"][w][d] = v[w,d].X"""
                    
    return result_dict, input
    