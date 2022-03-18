from urllib.parse import quote_from_bytes
from input_functions import *
from scipy.stats import poisson
import gurobipy as gp
from gurobipy import GRB
from gurobipy import GurobiError
from gurobipy import quicksum
import numpy as np
from output_functions import *
import pickle

def run_model(input_dict, flexibility, time_limit, expected_value_solution = False, print_optimizer = False):    
    #----- Sets ----- #  
    nDays           =   input_dict["nDays"]
    nWards          =   input_dict["nWards"]
    nGroups         =   input_dict["nGroups"]
    nSpecialties    =   input_dict["nSpecialties"]
    nRooms          =   input_dict["nRooms"]
    
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
    m.setParam("MIPFocus", 3) 
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
    #result_dict["max_runtime"] = time_limit

    nSolutions=m.SolCount
    if nSolutions==0:
        result_dict["status"]=0
    else:
        result_dict =  save_results(m, input_dict, result_dict)

    return result_dict, input_dict

def categorize_slots2(input_dict, output_dict):
    
    fixed_slots = [[0 for _ in range(input_dict["nDays"])] for _ in range(input_dict["nRooms"])]
    flex_slot = [[0 for _ in range(input_dict["nDays"])] for _ in range(input_dict["nRooms"])]
    specialty_in_slot = [[0 for _ in range(input_dict["nDays"])] for _ in range(input_dict["nRooms"])]
    ext_slot = [[0 for _ in range(input_dict["nDays"])] for _ in range(input_dict["nRooms"])]
    
    days_in_cycle = int(input_dict["nDays"]/input_dict["I"])
    flex_count = 0
    fixed_count = 0
    
    for r in input_dict["Ri"]:
        day_in_cycle=0
        for d in range(input_dict["nDays"]):
            if day_in_cycle >= days_in_cycle:
                    day_in_cycle=0
            if sum(output_dict["delt"][s][r][d][c] for s in input_dict["Si"] for c in input_dict["Ci"])>0.5:
                flex_slot[r][d] = 1
                flex_count += 1
                for dd in range(input_dict["nDays"]):
                        if (dd % days_in_cycle) == day_in_cycle:
                            flex_slot[r][dd]=1
                            specialty_in_slot[r][d] = -1
            for s in input_dict["SRi"][r]:
                if output_dict["gamm"][s][r][d]>0.5:
                    specialty_in_slot[r][d] = s
                    fixed_count += 1
                    
            if sum(output_dict["lamb"][s][r][d] for s in input_dict["Si"])>0.5:
                    ext_slot[r][d]=1
            day_in_cycle += 1
    
    output_dict["fixedSlot"]    = fixed_slots
    output_dict["flexSlot"]     = flex_slot
    output_dict["extSlot"]      = ext_slot
    output_dict["specialty_in_slot"] = specialty_in_slot
    return output_dict    

def update_patterns_list(GSi,A, MS_i, Q_rem,s,c):
    for m in MS_i[s]:
        for g in GSi[s]:
            if A[m][g] > Q_rem[g][c]:
                MS_i[s].remove(m)
    return MS_i 

def sort_list_by_another(list_to_sort,list_to_sort_by, decending=True):
    list_to_sort  =   [x for _,x in sorted(zip(list_to_sort_by,list_to_sort))]
    list_to_sort_by.sort(reverse=decending)
    list_to_sort.reverse()
    return list_to_sort, list_to_sort_by

def sort_MS_after_duration(input_dict,MSi,MSi_dur,decending=True):
    for s in input_dict["Si"]:
        MSi_sorted_s, MSi_dur_sorted_s  =   sort_list_by_another(MSi[s],MSi_dur[s],decending=True)
        MSi[s]=MSi_sorted_s
        MSi_dur[s]=MSi_dur_sorted_s
    return MSi, MSi_dur

def construct_dur_to_MSi(input_dict, MSi_set):
    MSi_dur                     =   [[] for _ in range(len(input_dict["Si"]))]
    for s in input_dict["Si"]:
        for m in MSi_set[s]:
            duration            = sum(input_dict["A"][m][g]*(input_dict["L"][g]+input_dict["TC"]) for g in input_dict["Gi"])
            MSi_dur[s].append(duration)
    return MSi_dur

def construct_dur_to_Mi(input_dict, Mi_set):
    Mi_dur                     =   []
    for m in Mi_set:
        duration            = sum(input_dict["A"][m][g]*(input_dict["L"][g]+input_dict["TC"]) for g in input_dict["Gi"])
        Mi_dur.append(duration)
    return Mi_dur

def calculate_total_bed_occupation(input_dict, current_bed_occ, pattern ,current_day, scenario):
    nDays   =   input_dict["nDays"]
    Wi      =   input_dict["Wi"]
    J       =   input_dict["J"]
    Psum    =   input_dict["Psum"]
    B       =   input_dict["B"]
    illegal_move = False
    for w in Wi:
        for d in range(current_day,min(nDays,current_day+J[w])):
            Psum[pattern][w][d]=1
            current_bed_occ[scenario][d][w] += Psum[pattern][w][d]
            if current_bed_occ[scenario][d][w]> B[w][d]:
                illegal_move = True
                break
        if illegal_move:
            break
    return current_bed_occ, illegal_move

def run_greedy_construction_heuristic(input_dict,result_dict,flexibility,nScenarios,seed):
    #----- Sets ----- #  
    nDays           =   input_dict["nDays"]
    nWards          =   input_dict["nWards"]
    nScenarios      =   input_dict["nScenarios"]
    nGroups         =   input_dict["nGroups"]
    nSpecialties    =   input_dict["nSpecialties"]
    nRooms          =   input_dict["nRooms"]
    
    Wi              =   input_dict["Wi"]
    Si              =   input_dict["Si"]
    Gi              =   input_dict["Gi"]
    GWi             =   input_dict["GWi"]
    GSi             =   input_dict["GSi"]    
    Ri              =   input_dict["Ri"]
    RSi             =   input_dict["RSi"]
    RGi             =   input_dict["RGi"]
    Di              =   input_dict["Di"]
    Ci              =   input_dict["Ci"]
    
    WSi             =   input_dict["WSi"]
    SRi             =   input_dict["SRi"]

    #----- Parameter ----- #  
    F               =   flexibility
    input_dict["F"] = flexibility
    E               =   input_dict["E"]
    TC              =   input_dict["TC"]
    I               =   input_dict["I"]
    B               =   input_dict["B"]
    H               =   input_dict["H"]
    K               =   input_dict["K"]
    L               =   input_dict["L"]
    U               =   input_dict["U"]
    N               =   input_dict["N"]
    T               =   input_dict["T"]
    Co              =   input_dict["Co"]
    J               =   input_dict["J"]
    Pi              =   input_dict["Pi"]
    Q               =   input_dict["Q"]
    P               =   input_dict["P"]
    Y               =   input_dict["Y"]
    
    #----- Patterns extention ----- # 
    A               =   input_dict["A"]
    Psum            =   input_dict["Psum"]
    Mi              =   input_dict["Mi"]
    Mnxi            =   input_dict["Mnxi"]
    Mxi             =   input_dict["Mxi"]
    MSi             =   input_dict["MSi"]
    MSnxi           =   input_dict["MSnxi"]
    MSxi            =   input_dict["MSxi"]
    pattern_dur     =   input_dict["pattern_dur"]
                
    #----- initializing ----- # 
    MSnxi_dur       =   construct_dur_to_MSi(input_dict,MSnxi)
    MSxi_dur        =   construct_dur_to_MSi(input_dict,MSxi) 
    Mi_dur          =   construct_dur_to_Mi(input_dict,Mi)     
    MSnxi, MSnxi_dur=   sort_MS_after_duration(input_dict,MSnxi,MSnxi_dur)
    MSxi, MSxi_dur  =   sort_MS_after_duration(input_dict,MSxi,MSxi_dur)
    slot            =   [[[0 for _ in Ci] for _ in Di] for _ in Ri]
    
    fixed_slots     = result_dict["fixedSlot"]
    flex_slot       = result_dict["flexSlot"]
    ext_slot        = result_dict["extSlot"]
    specialty_in_slot = result_dict["specialty_in_slot"]
    
    bed_occ = [[[0 for _ in Wi] for _ in Di] for _ in Ci]
    
    Q_rem           =   Q
    MSnxi_c         =   []
    MSxi_c          =   []
    for c in Ci:
        MSnxi_c.append(MSnxi)
        MSxi_c.append(MSxi)
    for s in Si:
        for c in Ci:
            MSnxi_c[c] =   update_patterns_list(GSi, A, MSnxi_c[c], Q_rem, s, c)
            MSxi_c[c]  =   update_patterns_list(GSi, A, MSxi_c[c], Q_rem, s, c)
            
    #----- Begin Heuristic ----- # 
    for d in Di:
        for r in Ri:
            s = specialty_in_slot[r][d] 
            #----- Pack fixed and extended slots ----- #
            if s>-0.5:
                if ext_slot[r][d]> 0.5:
                    '---pack ext slots---'
                    for c in Ci:
                        if len(MSxi_c[c][s])>0.5:
                            '---pack w/ remaining ext patterns---'
                            i=0
                            illegal_move = False
                            while not illegal_move and i<len(MSxi_c[c][s]):
                                new_bed_occ, illegal_move = calculate_total_bed_occupation(input_dict,bed_occ ,MSxi_c[c][s][i],d,c)
                                if illegal_move:
                                    i+=1
                            if not illegal_move:
                                bed_occ = new_bed_occ
                                slot[r][d][c] = MSxi_c[c][s][i]
                                for g in GSi[s]:
                                    Q_rem[g][c] -= A[MSxi_c[c][s][i]][g]
                                MSxi_c[c] =   update_patterns_list(GSi, A, MSxi_c[c], Q_rem, s, c)
                        else:
                            '---pack w/ non-ext patterns if no ext patterns remain---'
                            if len(MSnxi_c[c][s])>0.5:
                                slot[r][d][c] = MSnxi_c[s][0]
                                for g in GSi[s]:
                                    Q_rem[g][c] -= A[MSnxi_c[c][s][0]][g]
                                MSnxi_c[c]  =   update_patterns_list(GSi, A, MSnxi_c[c], Q_rem, s, c)
                            
                else:
                    '---pack non-ext slots---'
                    for c in Ci:
                        if len(MSnxi_c[c][s])>0.5:
                            slot[r][d][c] = MSnxi_c[c][s][0]
                            for g in GSi[s]:
                                Q_rem[g][c] -= A[MSnxi_c[c][s][0]][g]
                            MSnxi_c[c]  =   update_patterns_list(GSi, A, MSnxi_c[c], Q_rem, s, c)
            #----- Pack flexible slots ----- #
            else:
                flex_pack_temp  =   [[[[0 for _ in Ci] for _ in Di] for _ in Ri] for s in Si]
                total = [0 for _ in Si]
                '---finding best specialty---'
                for s in SRi[r]:
                    for c in Ci:
                        if len(MSnxi_c[c][s])>0.5:
                            total[s] += Mi_dur[MSnxi_c[c][s][0]]*Pi[c]
                            flex_pack_temp[s][r][d][c] = MSnxi_c[s][0]
                best_spec = total.index(max(total))
                '---assigning specialty and update values---'
                for g in GSi[best_spec]:
                    if len(MSnxi_c[c][s])>0.5:
                        Q_rem[g][c] -= A[MSnxi_c[c][best_spec][0]][g]
                for c in Ci:
                    slot[r][d][c]   =   flex_pack_temp[best_spec][r][d][c]
                    MSnxi_c[c]      =   update_patterns_list(GSi, A, MSnxi, Q_rem, best_spec, c)
    #----- Calculate objective -----#
    obj = sum(Pi[c]*Q_rem[g][c] for c in Ci for g in Gi)            
    print(obj)
    return obj, slot           
            
def main(number_of_groups: int,flexibility: float, nScenarios: int, seed: int):
    try:
        with open("solution_saved.pkl","rb") as f:
            saved_values    = pickle.load(f)
        input   =   saved_values["input"]
        results =   saved_values["results"]
    except FileNotFoundError:
        file_name   = choose_correct_input_file(number_of_groups)
        input       = read_input(file_name)
        input       = generate_scenarios(input, nScenarios, seed)
        results, input = run_model(input,flexibility,20,expected_value_solution=False,print_optimizer = True)
        results = categorize_slots2(input,results)
        #--- Saving solution in pickle ---
        saved_values            =   {}
        saved_values["input"]   =   input
        saved_values["results"] =   results
        with open("solution_saved.pkl","wb") as f:
            pickle.dump(saved_values,f)
    run_greedy_construction_heuristic(input,results, flexibility,nScenarios,seed)

main(9,0.1,10,1)