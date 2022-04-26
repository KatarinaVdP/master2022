from scipy.stats import poisson
import gurobipy as gp
from gurobipy import GRB
from gurobipy import GurobiError
from gurobipy import quicksum
from patterns import *
from functions_output import *

def save_results_cutting_stock(m, input_dict, result_dict):
    #input = copy.deepcopy(input_dict)
    #result_dict = copy.deepcopy(result_dict2)
    
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
                    val = 0
                    for mi in input_dict["Mi"]:
                        name = (f"pat[{mi},{r},{d},{c}]")
                        var= m.getVarByName(name)
                        val += input_dict["A"][mi][g]*var.X
                    if val > 0:
                        result_dict["x"][g][r][d][c] = int(val)
                    
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

def run_model_cutting_stock(input_dict, flexibility, time_limit,print_optimizer=False):
    input=input_dict
    #----- Sets ----- #  
    nDays           =   input["nDays"]
    
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
    I   =   input["I"]
    B   =   input["B"]
    K   =   input["K"]
    U   =   input["U"]
    N   =   input["N"]
    Co  =   input["Co"]
    J   =   input["J"]
    Pi  =   input["Pi"]
    Q   =   input["Q"]
    P   =   input["P"]
    Y   =   input["Y"]
    nFixed = int(np.ceil((1-F) * sum(N[d] for d in Di)/I)*I)
    input["nFixed"] = nFixed
    
    # Parameters and sets specific to cutting stock model
    A       =   input["A"]
    Psum    =   input["Psum"]
    Mi      =   input["Mi"]
    Mnxi    =   input["Mnxi"]
    Mxi     =   input["Mxi"]
    MSi     =   input_dict["MSi_unsorted"]  #standard MSi becomes sorted in read_input, but MSi_unsorted is direct from generate_pattern_data

 
    #----- Model ----- #
    m = gp.Model("mss_mip")
    m.setParam("TimeLimit", time_limit)
    
    if not print_optimizer:
        m.Params.LogToConsole = 0
    
    '--- Variables ---'
    gamm    =   m.addVars(Si, Ri, Di, vtype=GRB.BINARY, name="gamma")
    lamb    =   m.addVars(Si, Ri, Di, vtype=GRB.BINARY, name="lambda")
    delt    =   m.addVars(Si, Ri, Di, Ci, vtype=GRB.BINARY, name="delta")
    pat     =   m.addVars(Mi, Ri, Di, Ci, vtype=GRB.BINARY, name="pat")
    a       =   m.addVars(Gi, Ci, vtype=GRB.INTEGER, name="a")

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
    print('Creating model (2/3)')
    m.addConstrs(
        (quicksum(Psum[m][w][d-dd] * pat[m,r,dd,c] for m in Mi for r in Ri for dd in range(max(0,d+1-J[w]),d+1)) <= B[w][d] - Y[w][d] 
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
    print('Creating model (3/3)')
    m.optimize()
    result_dict = save_results_pre(m)

    nSolutions=m.SolCount
    if nSolutions==0:
        result_dict["status"]=0
    else:
        result_dict =  save_results_cutting_stock(m, input_dict, result_dict)
        
    return result_dict, input    
    """statuses=[0,"LOADED","OPTIMAL","INFEASIBLE","INF_OR_UNBD","UNBOUNDED","CUTOFF", "ITERATION_LIMIT",
    "NODE_LIMIT", "TIME_LIMIT", "SOLUTION_LIMIT","INTERUPTED","NUMERIC","SUBOPTIMAL", "USES_OBJ_LIMIT","WORK_LIMIT"]
    result_dict =   {}
    result_dict["status"]=statuses[m.STATUS]
    if statuses[m.STATUS]==GRB.INFEASIBLE:
        print('Model is proven infeasible!!!!!!!')
        return
    result_dict["obj"] = m.ObjVal
    result_dict["best_bound"] = m.ObjBound
    result_dict["runtime"] = m.Runtime
    result_dict["max_runtime"] = time_limit   
    result_dict["MIPGap"] = m.MIPGap  
    nSolutions=m.SolCount"""
    
    """if nSolutions==0:
        result_dict["status"]=statuses[0]
        print('0 solutions found')
    else:"""
    """# ----- Copying the desicion variable values to result dictionary -----
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
                    val = sum(A[m][g]*pat[m,r,d,c].X for m in Mi)
                    if val > 0:
                        result_dict["x"][g][r][d][c] = val
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
    result_dict["bed_occupation_wdc"] = bed_occupationC
    for w in input_dict["Wi"]:
            for d in input_dict["Di"]:
                result_dict["bed_occupation"][w][d] = sum(bed_occupationC[w][d][c]*input_dict["Pi"][c] for c in input_dict["Ci"])"""
       
