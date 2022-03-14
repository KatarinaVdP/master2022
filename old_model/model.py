from scipy.stats import poisson
import gurobipy as gp
from gurobipy import GRB
from gurobipy import GurobiError
from gurobipy import quicksum
import numpy as np


def run_model(input_dict, flexibility, time_limit, expected_value_solution = False, print_optimizer = False):
    input = input_dict
    
    #----- Sets ----- #  
    nDays           =   input["nDays"]
    nWards          =   input["nWards"]
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
    P   =   input["P"]
    Y   =   input["Y"]
    
    if expected_value_solution:
        nScenarios          =   1
        Ci                  =   [c for c in range(nScenarios)]
        Pi                  =   [1/nScenarios]*nScenarios
        Q                   =   [[0 for _ in range(nScenarios)] for _ in range(input["nGroups"])]
        for c in Ci:
            for g in Gi:
                Q[g][c] = int(T[g])
        input["Ci"]         =   Ci                           
        input["Pi"]         =   [1/nScenarios]*nScenarios
        input["nScenarios"] =   nScenarios
        input["Q"]          =   Q
    else:
        nScenarios          =   input["nScenarios"]
        Pi                  =   input["Pi"]
        Q                   =   input["Q"]
        Ci                  =   input["Ci"]
    #----- Model ----- #
    m = gp.Model("mss_mip")
    m.setParam("TimeLimit", time_limit)
    if not print_optimizer:
        m.Params.LogToConsole = 0
    
    
    '--- Variables ---'
    gamm    =   m.addVars(Si, Ri, Di, vtype=GRB.BINARY, name="gamma")
    lamb    =   m.addVars(Si, Ri, Di, vtype=GRB.BINARY, name="lambda")
    delt    =   m.addVars(Si, Ri, Di, Ci, vtype=GRB.BINARY, name="delta")
    x       =   m.addVars(Gi, Ri, Di, Ci, vtype=GRB.INTEGER, name="x")
    a       =   m.addVars(Gi, Ci, vtype=GRB.INTEGER, name="a")
    """v       =   m.addVars(Wi, Di, vtype=GRB.CONTINUOUS, name="v")"""
    
    for s in Si:
        for r in (list(set(Ri)^set(RSi[s]))):
            for d in Di:
                gamm[s,r,d].lb=0
                gamm[s,r,d].ub=0
                for c in Ci:
                    delt[s,r,d,c].lb=0
                    delt[s,r,d,c].ub=0  
    for g in Gi:
        for r in (list(set(Ri)^set(RGi[g]))):
            for d in Di:
                for c in Ci:  
                    x[g,r,d,c].lb=0
                    x[g,r,d,c].ub=0             
    

    max_fixed_slots = int(np.ceil((1-F) * sum(N[d] for d in Di)))
    '--- Objective ---' 
    m.setObjective(
                quicksum(Pi[c] * Co[g] * a[g,c] for g in Gi for c in Ci)
    )
        
    m.ModelSense = GRB.MINIMIZE 
    '--- Constraints ---'
    m.addConstr(
        quicksum( quicksum(gamm[s,r,d] for r in RSi[s]) for s in Si for d in Di) ==  max_fixed_slots ,
        name = "Con_PercentFixedRooms"
        )
        
    m.addConstrs(
        (lamb[s,r,d] <= gamm[s,r,d] 
        for s in Si for r in Ri for d in Di), 
        name = "Con_RollingFixedSlotCycles",
        )
    m.addConstrs(
        (quicksum(lamb[s,r,d] for r in RSi[s] for d in Di) <= U[s] 
        for s in Si),
        name = "Con_LongDaysCap",
    )
    print('Creating model (1/3)')
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
    for s in Si:
        m.addConstrs(
            (quicksum((L[g]+TC) * x[g,r,d,c] for g in GSi[s]) <= H[d] * (gamm[s,r,d] + delt[s,r,d,c]) + E*lamb[s,r,d] 
            for r in RSi[s] for d in Di for c in Ci),
        name = "Con_AvalibleTimeInRoom" + str(s), 
        )   
    m.addConstrs(
        (quicksum(x[g,r,d,c] for r in Ri for d in Di) + a[g,c] ==  Q[g][c] 
        for g in Gi for c in Ci),
        name= "Con_Demand",
    )
    m.addConstrs(
        (quicksum(delt[s,r,d,c] for s in Si) <= quicksum(x[g,r,d,c] for g in Gi) 
        for r in Ri for d in Di for c in Ci),
        name= "Con_OnlyAssignIfNecessary",
    )
    print('Creating model (2/3)')
    m.addConstrs(
        (quicksum(P[w][g][d-dd] * x[g,r,dd,c] for g in GWi[w] for r in Ri for dd in range(max(0,d+1-J[w]),d+1)) <= B[w][d] - Y[w][d] 
        for w in Wi for d in Di for c in Ci),
    name = "Con_BedOccupationCapacity",
    )
    """ m.addConstrs(
        (quicksum(P[w][g][d-dd] * x[g,r,dd,c] for g in GWi[w] for r in Ri for dd in range(max(0,d+1-J[w]),d+1)) <= B[w][d] - v[w,d] 
        for w in Wi for d in Di for c in Ci),
    name = "Con_BedOccupationCapacity",
    )
    print('still Creating Model 90%')
    for w in Wi:
        m.addConstrs(
            (quicksum(Pi[c] * quicksum(P[w][g][d+nDays-dd] * x[g,r,dd,c] for g in GWi[w] for r in Ri for dd in range(d+nDays+1-J[w],nDays)) for c in Ci) == v[w,d] 
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
    print('Creating model (3/3)')

    m.optimize()
    
    statuses=[0,"LOADED","OPTIMAL","INFEASIBLE","INF_OR_UNBD","UNBOUNDED","CUTOFF", "ITERATION_LIMIT",
    "NODE_LIMIT", "TIME_LIMIT", "SOLUTION_LIMIT","INTERUPTED","NUMERIC","SUBOPTIMAL", "USES_OBJ_LIMIT","WORK_LIMIT"]
    
    
    result_dict =   {}
    result_dict["status"]=statuses[m.STATUS]
    result_dict["obj"] = m.ObjVal
    result_dict["best_bound"] = m.ObjBound
    result_dict["runtime"] = m.Runtime
    result_dict["max_runtime"] = time_limit
    result_dict["MIPGap"] = m.MIPGap  
    nSolutions=m.SolCount
    if nSolutions==0:
        result_dict["status"]=statuses[0]
    else:
        # ----- Copying the desicion variable values to result dictionary -----
        result_dict["gamm"] = [[[0 for _ in range(input["nDays"])] for _ in range(input["nRooms"])] for _ in range(input["nSpecialties"])]
        result_dict["lamb"] = [[[0 for _ in range(input["nDays"])] for _ in range(input["nRooms"])] for _ in range(input["nSpecialties"])]
        result_dict["delt"] = [[[[0 for _ in range(input["nScenarios"])] for _ in range(input["nDays"])] for _ in range(input["nRooms"])] for _ in range(input["nSpecialties"])]
        result_dict["x"]    = [[[[0 for _ in range(input["nScenarios"])] for _ in range(input["nDays"])] for _ in range(input["nRooms"])] for _ in range(input["nGroups"])]
        result_dict["a"]    = [[0 for _ in range(input["nScenarios"])] for _ in range(input["nGroups"])]
        result_dict["v"]    = [[0 for _ in range(input["nDays"])] for _ in range(input["nWards"])]
        
        for s in input["Si"]:
            for r in input["Ri"]:
                for d in input["Di"]:    
                    result_dict["gamm"][s][r][d] = gamm[s,r,d].getAttr("x")
                    result_dict["lamb"][s][r][d] = lamb[s,r,d].X
                    for c in input["Ci"]:
                        result_dict["delt"][s][r][d][c] = delt[s,r,d,c].X                     
        for g in input["Gi"]:
            for r in input["Ri"]:
                for d in input["Di"]:    
                    for c in input["Ci"]:
                        result_dict["x"][g][r][d][c] = x[g,r,d,c].X
        for g in input["Gi"]:
            for c in input["Ci"]:
                result_dict["a"][g][c] = a[g,c].X
                    
        for w in Wi:
            for d in range(J[w]-1):
                result_dict["v"][w][d] = sum(Pi[c] * sum(P[w][g][d+nDays-dd] * result_dict["x"][g][r][dd][c] for g in GWi[w] for r in Ri for dd in range(d+nDays+1-J[w],nDays)) for c in Ci) 
        
        bed_occupationC =[[[0 for _ in range(input_dict["nScenarios"])] for _ in range(input_dict["nDays"])] for _ in range(input_dict["nWards"])]
        result_dict["bed_occupation"] =[[0 for _ in range(input_dict["nDays"])] for _ in range(input_dict["nWards"])]
        for w in input_dict["Wi"]:
            for d in input_dict["Di"]:
                for c in input_dict["Ci"]:
                    bed_occupationC[w][d][c]= sum(input_dict["P"][w][g][d-dd] * result_dict["x"][g][r][dd][c] for g in input_dict["GWi"][w] for r in input_dict["Ri"] for dd in range(max(0,d+1-input_dict["J"][w]),d+1)) + input_dict["Y"][w][d]
        for w in input_dict["Wi"]:
                for d in input_dict["Di"]:
                    result_dict["bed_occupation"][w][d] = sum(bed_occupationC[w][d][c]*input_dict["Pi"][c] for c in input_dict["Ci"])



    return result_dict, input

def run_model_fixed(input_dict,output_dict, time_limit, print_optimizer = False):
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
    Y   =   input["Y"]
    
    #----- Model ----- #
    m = gp.Model("mss_mip")
    m.setParam("TimeLimit", time_limit)
    if not print_optimizer:
        m.Params.LogToConsole = 0
    
    '--- Variables ---'
    gamm    =   m.addVars(Si, Ri, Di, vtype=GRB.BINARY, name="gamma")
    lamb    =   m.addVars(Si, Ri, Di, vtype=GRB.BINARY, name="lambda")
    delt    =   m.addVars(Si, Ri, Di, Ci, vtype=GRB.BINARY, name="delta")
    x       =   m.addVars(Gi, Ri, Di, Ci, vtype=GRB.INTEGER, name="x")
    a       =   m.addVars(Gi, Ci, vtype=GRB.INTEGER, name="a")
    """v       =   m.addVars(Wi, Di, vtype=GRB.CONTINUOUS, name="v")"""
    
    for s in Si:
        for r in Ri:
            for d in Di:
                gamm[s,r,d].lb=output_dict["gamm"][s][r][d]
                gamm[s,r,d].ub=output_dict["gamm"][s][r][d]
                lamb[s,r,d].lb=output_dict["lamb"][s][r][d]
                lamb[s,r,d].ub=output_dict["lamb"][s][r][d]
    for g in Gi:
        for r in (list(set(Ri)^set(RGi[g]))):
            for d in Di:
                for c in Ci:  
                    x[g,r,d,c].lb=0
                    x[g,r,d,c].ub=0 
                    
    '--- Objective ---' 
    m.setObjective(
                quicksum(Pi[c] * Co[g] * a[g,c] for g in Gi for c in Ci)
    )   
    m.ModelSense = GRB.MINIMIZE 
    '--- Constraints ---'
    max_fixed_slots = int(np.ceil((1-F) * sum(N[d] for d in Di)))
    m.addConstr(
        quicksum( quicksum(gamm[s,r,d] for r in RSi[s]) for s in Si for d in Di) ==  max_fixed_slots ,
        name = "Con_PercentFixedRooms"
        )
    m.addConstrs(
        (lamb[s,r,d] <= gamm[s,r,d] 
        for s in Si for r in Ri for d in Di), 
        name = "Con_RollingFixedSlotCycles",
        )
    m.addConstrs(
        (quicksum(lamb[s,r,d] for r in RSi[s] for d in Di) <= U[s] 
        for s in Si),
        name = "Con_LongDaysCap",
    )
    print('Creating model (1/3)')
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
    for s in Si:
        m.addConstrs(
            (quicksum((L[g]+TC) * x[g,r,d,c] for g in GSi[s]) <= H[d] * (gamm[s,r,d] + delt[s,r,d,c]) + E*lamb[s,r,d] 
            for r in RSi[s] for d in Di for c in Ci),
        name = "Con_AvalibleTimeInRoom" + str(s), 
        )   
    m.addConstrs(
        (quicksum(x[g,r,d,c] for r in Ri for d in Di) + a[g,c] ==  Q[g][c] 
        for g in Gi for c in Ci),
        name= "Con_Demand",
    )
    m.addConstrs(
        (quicksum(delt[s,r,d,c] for s in Si) <= quicksum(x[g,r,d,c] for g in Gi) 
        for r in Ri for d in Di for c in Ci),
        name= "Con_OnlyAssignIfNecessary",
    )
    print('Creating model (2/3)')
    m.addConstrs(
        (quicksum(P[w][g][d-dd] * x[g,r,dd,c] for g in GWi[w] for r in Ri for dd in range(max(0,d+1-J[w]),d+1)) <= B[w][d] - Y[w][d] 
        for w in Wi for d in Di for c in Ci),
    name = "Con_BedOccupationCapacity",
    )
    """ m.addConstrs(
        (quicksum(P[w][g][d-dd] * x[g,r,dd,c] for g in GWi[w] for r in Ri for dd in range(max(0,d+1-J[w]),d+1)) <= B[w][d] - v[w,d] 
        for w in Wi for d in Di for c in Ci),
    name = "Con_BedOccupationCapacity",
    )
    print('still Creating Model 90%')
    for w in Wi:
        m.addConstrs(
            (quicksum(Pi[c] * quicksum(P[w][g][d+nDays-dd] * x[g,r,dd,c] for g in GWi[w] for r in Ri for dd in range(d+nDays+1-J[w],nDays)) for c in Ci) == v[w,d] 
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
    print('Creating model (3/3)')

    m.optimize()

    statuses=[0,"LOADED","OPTIMAL","INFEASIBLE","INF_OR_UNBD","UNBOUNDED","CUTOFF", "ITERATION_LIMIT",
    "NODE_LIMIT", "TIME_LIMIT", "SOLUTION_LIMIT","INTERUPTED","NUMERIC","SUBOPTIMAL", "USES_OBJ_LIMIT","WORK_LIMIT"]
    result_dict =   {}
    result_dict["status"]=statuses[m.STATUS]
    result_dict["obj"] = m.ObjVal
    result_dict["best_bound"] = m.ObjBound
    result_dict["runtime"] = m.Runtime
    result_dict["max_runtime"] = time_limit
    result_dict["MIPGap"] = m.MIPGap  
    nSolutions=m.SolCount
    if nSolutions==0:
        result_dict["status"]=statuses[0]
        print('Did not find any feasible initial solution in read_model_fixed()')
        return
    else:
        m.write('model.mps')
        m.write('warmstart.mst')
        # ----- Copying the desicion variable values to result dictionary -----
        result_dict["gamm"] = [[[0 for _ in range(input["nDays"])] for _ in range(input["nRooms"])] for _ in range(input["nSpecialties"])]
        result_dict["lamb"] = [[[0 for _ in range(input["nDays"])] for _ in range(input["nRooms"])] for _ in range(input["nSpecialties"])]
        result_dict["delt"] = [[[[0 for _ in range(input["nScenarios"])] for _ in range(input["nDays"])] for _ in range(input["nRooms"])] for _ in range(input["nSpecialties"])]
        result_dict["x"]    = [[[[0 for _ in range(input["nScenarios"])] for _ in range(input["nDays"])] for _ in range(input["nRooms"])] for _ in range(input["nGroups"])]
        result_dict["a"]    = [[0 for _ in range(input["nScenarios"])] for _ in range(input["nGroups"])]
        result_dict["v"]    = [[0 for _ in range(input["nDays"])] for _ in range(input["nWards"])]
        
        for s in input["Si"]:
            for r in input["Ri"]:
                for d in input["Di"]:    
                    result_dict["gamm"][s][r][d] = gamm[s,r,d].getAttr("x")
                    result_dict["lamb"][s][r][d] = lamb[s,r,d].X
                    for c in input["Ci"]:
                        result_dict["delt"][s][r][d][c] = delt[s,r,d,c].X                     
        for g in input["Gi"]:
            for r in input["Ri"]:
                for d in input["Di"]:    
                    for c in input["Ci"]:
                        result_dict["x"][g][r][d][c] = x[g,r,d,c].X
        for g in input["Gi"]:
            for c in input["Ci"]:
                result_dict["a"][g][c] = a[g,c].X
                    
        for w in Wi:
            for d in range(J[w]-1):
                result_dict["v"][w][d] = sum(Pi[c] * sum(P[w][g][d+nDays-dd] * result_dict["x"][g][r][dd][c] for g in GWi[w] for r in Ri for dd in range(d+nDays+1-J[w],nDays)) for c in Ci) 
        
        bed_occupationC =[[[0 for _ in range(input_dict["nScenarios"])] for _ in range(input_dict["nDays"])] for _ in range(input_dict["nWards"])]
        result_dict["bed_occupation"] =[[0 for _ in range(input_dict["nDays"])] for _ in range(input_dict["nWards"])]
        for w in input_dict["Wi"]:
            for d in input_dict["Di"]:
                for c in input_dict["Ci"]:
                    bed_occupationC[w][d][c]= sum(input_dict["P"][w][g][d-dd] * result_dict["x"][g][r][dd][c] for g in input_dict["GWi"][w] for r in input_dict["Ri"] for dd in range(max(0,d+1-input_dict["J"][w]),d+1)) + input_dict["Y"][w][d]
        for w in input_dict["Wi"]:
                for d in input_dict["Di"]:
                    result_dict["bed_occupation"][w][d] = sum(bed_occupationC[w][d][c]*input_dict["Pi"][c] for c in input_dict["Ci"])
    return result_dict
        