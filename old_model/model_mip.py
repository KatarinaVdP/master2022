import gurobipy as gp
from gurobipy import GRB
from gurobipy import GurobiError
from gurobipy import quicksum
import numpy as np
from functions_output import *

def save_results(m, input_dict, result_dict): 
    # ----- Copying the desicion variable values to result dictionary -----
    result_dict["gamm"] = [[[0 for _ in range(input_dict["nDays"])] for _ in range(input_dict["nRooms"])] for _ in range(input_dict["nSpecialties"])]
    result_dict["lamb"] = [[[0 for _ in range(input_dict["nDays"])] for _ in range(input_dict["nRooms"])] for _ in range(input_dict["nSpecialties"])]
    result_dict["delt"] = [[[[0 for _ in range(input_dict["nScenarios"])] for _ in range(input_dict["nDays"])] for _ in range(input_dict["nRooms"])] for _ in range(input_dict["nSpecialties"])]
    result_dict["x"]    = [[[[0 for _ in range(input_dict["nScenarios"])] for _ in range(input_dict["nDays"])] for _ in range(input_dict["nRooms"])] for _ in range(input_dict["nGroups"])]
    result_dict["a"]    = [[0 for _ in range(input_dict["nScenarios"])] for _ in range(input_dict["nGroups"])]
    result_dict["v"]    = [[0 for _ in range(input_dict["nDays"])] for _ in range(input_dict["nWards"])]
    
    for s in input_dict["Si"]:
        for r in input_dict["Ri"]:
            for d in input_dict["Di"]:
                name = (f"gamma[{s},{r},{d}]")
                var= m.getVarByName(name)    
                result_dict["gamm"][s][r][d] = var.X
                name = (f"lambda[{s},{r},{d}]")
                var= m.getVarByName(name) 
                result_dict["lamb"][s][r][d] = var.X
                
                for c in input_dict["Ci"]:
                    name = (f"delta[{s},{r},{d},{c}]")
                    var= m.getVarByName(name)  
                    result_dict["delt"][s][r][d][c] = var.X        
    for g in input_dict["Gi"]:
        for r in input_dict["Ri"]:
            for d in input_dict["Di"]:    
                for c in input_dict["Ci"]:
                    name = (f"x[{g},{r},{d},{c}]")
                    var= m.getVarByName(name)
                    result_dict["x"][g][r][d][c] = var.X
    for g in input_dict["Gi"]:
        for c in input_dict["Ci"]:
            name = (f"a[{g},{c}]")
            var= m.getVarByName(name)
            result_dict["a"][g][c] = var.X
                
    for w in input_dict["Wi"]:
        for d in range(input_dict["J"][w]-1):
            result_dict["v"][w][d] = sum(input_dict["Pi"][c] * sum(input_dict["P"][w][g][d+input_dict["nDays"]-dd] * result_dict["x"][g][r][dd][c] for g in input_dict["GWi"][w] for r in input_dict["Ri"] for dd in range(d+input_dict["nDays"]+1-input_dict["J"][w],input_dict["nDays"])) for c in input_dict["Ci"]) 
    
    result_dict["bed_occupation_wdc"]   =   [[[0 for _ in range(input_dict["nScenarios"])] for _ in range(input_dict["nDays"])] for _ in range(input_dict["nWards"])]
    result_dict["bed_occupation"]       =   [[0 for _ in range(input_dict["nDays"])] for _ in range(input_dict["nWards"])]
    for w in input_dict["Wi"]:
        for d in input_dict["Di"]:
            for c in input_dict["Ci"]:
                result_dict["bed_occupation_wdc"][w][d][c]  =   sum(input_dict["P"][w][g][d-dd] * result_dict["x"][g][r][dd][c] for g in input_dict["GWi"][w] for r in input_dict["Ri"] for dd in range(max(0,d+1-input_dict["J"][w]),d+1)) + input_dict["Y"][w][d]
    for w in input_dict["Wi"]:
            for d in input_dict["Di"]:
                result_dict["bed_occupation"][w][d]         =   sum(result_dict["bed_occupation_wdc"][w][d][c]*input_dict["Pi"][c] for c in input_dict["Ci"])
    
    return result_dict

def run_model_mip(input_dict, flexibility, time_limit, expected_value_solution = False, print_optimizer = False):    
    #----- Sets ----- #  
    nDays =   input_dict["nDays"]
    Wi  =   input_dict["Wi"]
    Si  =   input_dict["Si"]
    Gi  =   input_dict["Gi"]
    GWi =   input_dict["GWi"]
    GSi =   input_dict["GSi"]    
    Ri  =   input_dict["Ri"]
    RSi =   input_dict["RSi"]
    RGi =   input_dict["RGi"]
    Di  =   input_dict["Di"]

    #----- Parameter ----- #  
    F   =   flexibility
    input_dict["F"]  = flexibility
    E   =   input_dict["E"]
    TC  =   input_dict["TC"]
    I   =   input_dict["I"]
    B   =   input_dict["B"]
    H   =   input_dict["H"]
    K   =   input_dict["K"]
    L   =   input_dict["L"]
    U   =   input_dict["U"]
    N   =   input_dict["N"]
    T   =   input_dict["T"]
    Co  =   input_dict["Co"]
    J   =   input_dict["J"]
    P   =   input_dict["P"]
    Y   =   input_dict["Y"]
    nFixed = int(np.ceil((1-F) * sum(N[d] for d in Di)/I)*I)
    input_dict["nFixed"] = nFixed
    #----- EVS configuration ----- #  
    if expected_value_solution:
        nScenarios          =   1
        Ci                  =   [c for c in range(nScenarios)]
        Pi                  =   [1/nScenarios]*nScenarios
        Q                   =   [[0 for _ in range(nScenarios)] for _ in range(input_dict["nGroups"])]
        for c in Ci:
            for g in Gi:
                Q[g][c] = int(T[g])
        input_dict["Ci"]         =   Ci                           
        input_dict["Pi"]         =   [1/nScenarios]*nScenarios
        input_dict["nScenarios"] =   nScenarios
        input_dict["Q"]          =   Q
        input_dict["seed"]       =   "T"
    else:
        nScenarios          =   input_dict["nScenarios"]
        Pi                  =   input_dict["Pi"]
        Q                   =   input_dict["Q"]
        Ci                  =   input_dict["Ci"]
    
    #----- Model ----- #
    m = gp.Model("mss_mip")
    m.setParam("TimeLimit", time_limit)
    # m.setParam("MIPFocus", 3) 
    # finding feasible solutions quickly:1
    # no trouble finding good quality solutions, more attention on proving optimality: 2 
    # If the best objective bound is moving very slowly (or not at all)and want to focus on the bound:3
    if not print_optimizer:
        m.Params.LogToConsole = 0

    '--- Variables ---'
    gamm    =   m.addVars(Si, Ri, Di, vtype=GRB.BINARY, name="gamma")
    lamb    =   m.addVars(Si, Ri, Di, vtype=GRB.BINARY, name="lambda")
    delt    =   m.addVars(Si, Ri, Di, Ci, vtype=GRB.BINARY, name="delta")
    x       =   m.addVars(Gi, Ri, Di, Ci, vtype=GRB.INTEGER, name="x")
    a       =   m.addVars(Gi, Ci, vtype=GRB.INTEGER, name="a")
    
    for s in Si:
        for r in (list(set(Ri)^set(RSi[s]))):
            for d in Di:
                gamm[s,r,d].lb=0
                gamm[s,r,d].ub=0
                """lamb[s,r,d].lb=0
                lamb[s,r,d].ub=0    look at this later!"""
                for c in Ci:
                    delt[s,r,d,c].lb=0
                    delt[s,r,d,c].ub=0  
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
    m.addConstr(
        quicksum( quicksum(gamm[s,r,d] for r in RSi[s]) for s in Si for d in Di) ==  nFixed ,
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
    print('Creating model (1/3)', end= "")
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
    print(' (2/3)', end="")
    m.addConstrs(
        (quicksum(P[w][g][d-dd] * x[g,r,dd,c] for g in GWi[w] for r in Ri for dd in range(max(0,d+1-J[w]),d+1)) <= B[w][d] - Y[w][d] 
        for w in Wi for d in Di for c in Ci),
    name = "Con_BedOccupationCapacity",
    )
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
    print(' (3/3)')

    m.optimize()
    result_dict = save_results_pre(m)

    nSolutions=m.SolCount
    if nSolutions==0:
        result_dict["status"]=0
    else:
        result_dict =  save_results(m, input_dict, result_dict)

    return result_dict, input_dict

def run_model_mip_fixed_manual(input_dict, time_limit, print_optimizer = False, create_model_and_warmstart_file=True,MIPgap_limit=False): 
    #----- Sets ----- #  
    nDays           =   input_dict["nDays"]
    Wi  =   input_dict["Wi"]
    Si  =   input_dict["Si"]
    Gi  =   input_dict["Gi"]
    GWi =   input_dict["GWi"]
    GSi =   input_dict["GSi"]    
    Ri  =   input_dict["Ri"]
    RSi =   input_dict["RSi"]
    RGi =   input_dict["RGi"]
    Di  =   input_dict["Di"]
    Ci  =   input_dict["Ci"]

    #----- Parameter ----- #  
    F   =   input_dict["F"]
    E   =   input_dict["E"]
    TC  =   input_dict["TC"]
    I   =   input_dict["I"]
    B   =   input_dict["B"]
    H   =   input_dict["H"]
    K   =   input_dict["K"]
    L   =   input_dict["L"]
    U   =   input_dict["U"]
    N   =   input_dict["N"]
    T   =   input_dict["T"]
    Co  =   input_dict["Co"]
    J   =   input_dict["J"]
    P   =   input_dict["P"]
    Pi  =   input_dict["Pi"]
    Q   =   input_dict["Q"]
    Y   =   input_dict["Y"]
    nFixed = int(np.ceil((1-F) * sum(N[d] for d in Di)/I)*I)
    input_dict["nFixed"] = nFixed
    #----- Model ----- #
    m = gp.Model("mss_mip")
    m.setParam("TimeLimit", time_limit)
    if MIPgap_limit:
        gap_limit=0.001
        m.setParam("MIPGap", gap_limit)
    #m.setParam("MIPFocus", 3) 
    # finding feasible solutions quickly:1
    # no trouble finding good quality solutions, more attention on proving optimality: 2 
    # If the best objective bound is moving very slowly (or not at all)and want to focus on the bound:3
    if not print_optimizer:
        m.Params.LogToConsole = 0
    
    '--- Variables ---'
    gamm    =   m.addVars(Si, Ri, Di, vtype=GRB.BINARY, name="gamma")
    lamb    =   m.addVars(Si, Ri, Di, vtype=GRB.BINARY, name="lambda")
    delt    =   m.addVars(Si, Ri, Di, Ci, vtype=GRB.BINARY, name="delta")
    x       =   m.addVars(Gi, Ri, Di, Ci, vtype=GRB.INTEGER, name="x")
    a       =   m.addVars(Gi, Ci, vtype=GRB.INTEGER, name="a")
    
    """for s in Si:
        for r in Ri:
            for d in Di:
                gamm[s,r,d].lb=output_dict["gamm"][s][r][d]
                gamm[s,r,d].ub=output_dict["gamm"][s][r][d]
                lamb[s,r,d].lb=output_dict["lamb"][s][r][d]
                lamb[s,r,d].ub=output_dict["lamb"][s][r][d]"""
    #day1
    
    gamm[2,1,0].lb=1
    gamm[2,2,0].lb=1
    gamm[1,3,0].lb=1
    gamm[0,4,0].lb=1
    gamm[2,5,0].lb=1
    gamm[0,6,0].lb=1
    #day2
    gamm[2,0,1].lb=1
    gamm[4,1,1].lb=1
    gamm[2,2,1].lb=1
    gamm[1,3,1].lb=1
    gamm[1,4,1].lb=1
    gamm[2,5,1].lb=1
    gamm[0,6,1].lb=1
    #day3
    gamm[4,0,2].lb=1
    gamm[4,1,2].lb=1
    gamm[2,2,2].lb=1
    gamm[0,3,2].lb=1
    gamm[1,4,2].lb=1
    gamm[2,5,2].lb=1
    gamm[0,6,2].lb=1
    #day4
    gamm[4,0,3].lb=1
    gamm[4,1,3].lb=1
    gamm[2,2,3].lb=1
    gamm[1,3,3].lb=1
    gamm[0,4,3].lb=1
    gamm[2,5,3].lb=1
    gamm[0,6,3].lb=1
    #day5   
    gamm[4,0,4].lb=1
    gamm[2,1,4].lb=1
    gamm[2,2,4].lb=1
    gamm[1,3,4].lb=1
    gamm[0,4,4].lb=1
    gamm[2,5,4].lb=1
    gamm[0,6,4].lb=1
    #weekend
    
    #day8
    gamm[4,0,7].lb=1
    gamm[4,1,7].lb=1
    gamm[2,2,7].lb=1
    gamm[1,3,7].lb=1
    gamm[0,4,7].lb=1
    gamm[2,5,7].lb=1
    gamm[0,6,7].lb=1
    #day9    
    gamm[4,0,8].lb=1
    gamm[2,1,8].lb=1
    gamm[2,2,8].lb=1
    gamm[1,3,8].lb=1
    gamm[0,4,8].lb=1
    gamm[2,5,8].lb=1
    
    #day10    
    gamm[4,0,9].lb=1
    
    gamm[2,2,9].lb=1
    gamm[0,3,9].lb=1
    gamm[0,4,9].lb=1
    gamm[2,5,9].lb=1
    gamm[1,6,9].lb=1
    #day11
    gamm[2,0,10].lb=1

    gamm[2,2,10].lb=1
    gamm[0,3,10].lb=1

    gamm[2,5,10].lb=1
    gamm[1,6,10].lb=1
    #day12


    gamm[2,2,11].lb=1
    gamm[0,3,11].lb=1
    gamm[1,4,11].lb=1
    gamm[2,5,11].lb=1
    gamm[0,6,11].lb=1
    
    #lambda
    #day1
    
    
    
    
    
    
    
    #day2



    lamb[1,3,1].lb=1
    lamb[1,4,1].lb=1


    #day3
    lamb[4,0,2].lb=1
    
    lamb[2,2,2].lb=1
    lamb[0,3,2].lb=1
    lamb[1,4,2].lb=1
    lamb[2,5,2].lb=1
    lamb[0,6,2].lb=1
    #day4







    #day5   
    lamb[4,0,4].lb=1
    
    
    
    
    lamb[2,5,4].lb=1
    
    #weekend
    
    #day8








    #day9    



    lamb[1,3,8].lb=1
    lamb[0,4,8].lb=1

    
    #day10    







    #day11



    lamb[0,3,10].lb=1

    
    lamb[1,6,10].lb=1
    #day12





    

    
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
    m.addConstr(
        quicksum( quicksum(gamm[s,r,d] for r in RSi[s]) for s in Si for d in Di) ==  nFixed ,
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
    print('Creating model (1/3)', end ="")
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
    print(' (2/3)',end="")
    m.addConstrs(
        (quicksum(P[w][g][d-dd] * x[g,r,dd,c] for g in GWi[w] for r in Ri for dd in range(max(0,d+1-J[w]),d+1)) <= B[w][d] - Y[w][d] 
        for w in Wi for d in Di for c in Ci),
    name = "Con_BedOccupationCapacity",
    )
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
    print(' (3/3)')

    m.optimize()
    result_dict = save_results_pre(m)

    nSolutions=m.SolCount
    if nSolutions==0:
        result_dict["status"]=0
        print('Did not find any feasible initial solution in read_model_fixed()')
        return
    else:
        if create_model_and_warmstart_file:
            m.write('model.mps')
            m.write('warmstart.mst')               
        result_dict =  save_results(m, input_dict, result_dict)
    return result_dict

def run_model_mip_fixed(input_dict,output_dict, time_limit, print_optimizer = False, create_model_and_warmstart_file=True,MIPgap_limit=False): 
    #----- Sets ----- #  
    nDays           =   input_dict["nDays"]
    Wi  =   input_dict["Wi"]
    Si  =   input_dict["Si"]
    Gi  =   input_dict["Gi"]
    GWi =   input_dict["GWi"]
    GSi =   input_dict["GSi"]    
    Ri  =   input_dict["Ri"]
    RSi =   input_dict["RSi"]
    RGi =   input_dict["RGi"]
    Di  =   input_dict["Di"]
    Ci  =   input_dict["Ci"]

    #----- Parameter ----- #  
    F   =   input_dict["F"]
    E   =   input_dict["E"]
    TC  =   input_dict["TC"]
    I   =   input_dict["I"]
    B   =   input_dict["B"]
    H   =   input_dict["H"]
    K   =   input_dict["K"]
    L   =   input_dict["L"]
    U   =   input_dict["U"]
    N   =   input_dict["N"]
    T   =   input_dict["T"]
    Co  =   input_dict["Co"]
    J   =   input_dict["J"]
    P   =   input_dict["P"]
    Pi  =   input_dict["Pi"]
    Q   =   input_dict["Q"]
    Y   =   input_dict["Y"]
    nFixed = int(np.ceil((1-F) * sum(N[d] for d in Di)/I)*I)
    input_dict["nFixed"] = nFixed
    #----- Model ----- #
    m = gp.Model("mss_mip")
    m.setParam("TimeLimit", time_limit)
    if MIPgap_limit:
        gap_limit=0.001
        m.setParam("MIPGap", gap_limit)
    #m.setParam("MIPFocus", 3) 
    # finding feasible solutions quickly:1
    # no trouble finding good quality solutions, more attention on proving optimality: 2 
    # If the best objective bound is moving very slowly (or not at all)and want to focus on the bound:3
    if not print_optimizer:
        m.Params.LogToConsole = 0
    
    '--- Variables ---'
    gamm    =   m.addVars(Si, Ri, Di, vtype=GRB.BINARY, name="gamma")
    lamb    =   m.addVars(Si, Ri, Di, vtype=GRB.BINARY, name="lambda")
    delt    =   m.addVars(Si, Ri, Di, Ci, vtype=GRB.BINARY, name="delta")
    x       =   m.addVars(Gi, Ri, Di, Ci, vtype=GRB.INTEGER, name="x")
    a       =   m.addVars(Gi, Ci, vtype=GRB.INTEGER, name="a")
    
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
    m.addConstr(
        quicksum( quicksum(gamm[s,r,d] for r in RSi[s]) for s in Si for d in Di) ==  nFixed ,
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
    print('Creating model (1/3)', end ="")
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
    print(' (2/3)',end="")
    m.addConstrs(
        (quicksum(P[w][g][d-dd] * x[g,r,dd,c] for g in GWi[w] for r in Ri for dd in range(max(0,d+1-J[w]),d+1)) <= B[w][d] - Y[w][d] 
        for w in Wi for d in Di for c in Ci),
    name = "Con_BedOccupationCapacity",
    )
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
    print(' (3/3)')

    m.optimize()
    result_dict = save_results_pre(m)

    nSolutions=m.SolCount
    if nSolutions==0:
        result_dict["status"]=0
        print('Did not find any feasible initial solution in read_model_fixed()')
        return
    else:
        if create_model_and_warmstart_file:
            m.write('model.mps')
            m.write('warmstart.mst')               
        result_dict =  save_results(m, input_dict, result_dict)
    return result_dict

