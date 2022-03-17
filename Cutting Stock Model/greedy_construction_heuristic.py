from urllib.parse import quote_from_bytes
from input_functions import *

def update_patterns_list(input_dict, MS_i,MS_dur, Q_rem,s,c):
    for m in range(len(MS_i[s])):
        for g in input_dict["GSi"][s]:
            if (input_dict["A"][g][c] > Q_rem[g][c]):
                MS_i[s].remove(m)
                MS_dur[s].remove(m)
    return MS_i,MS_dur

def sort_MS_after_duration(input_dict,pattern_MS_i):
    MSi                         =   [[] for _ in range(len(input_dict["Si"]))]
    MSi_dur                     =   [[] for _ in range(len(input_dict["Si"]))]
    MSi_sorted                  =   [[] for _ in range(len(input_dict["Si"]))]
    MSi_dur_sorted              =   [[] for _ in range(len(input_dict["Si"]))]
    
    for s in input_dict["Si"]:
        for m in pattern_MS_i[s]:
            duration            = sum(input_dict["A"][m][g]*input_dict["L"][g] for g in input_dict["Gi"])
            MSi_dur[s].append(duration)
            
        MSi_sorted[s]           =   [x for _,x in sorted(zip(MSi_dur[s],MSi[s]))]
        MSi_dur_sorted[s]       =   MSi_dur[s].sort(reverse=True)
        MSi_sorted[s]           =   MSi.reverse()
    return MSi_sorted,  MSi_dur_sorted

"""def construct_second_stage_sol(input, first_stage):
    Q_rem = input["Q"]
    unoperated = []
    for c in input["Ci"]:
        for s in input["Si"]:
            MSnxi = update_non_ext_patterns(input["MSnxi"])
            MSxi = update_ext_patterns(input["MSxi"])"""

def run_greedy_construction_heuristic(input_dict,flexibility,nScenarios,seed):
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

    """SRi = [[] for _ in Si]
    for s in Si:
        for r in Ri:
            if r in RSi[s]:
                SRi[s].append(r) 
    print(SRi)"""

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
    print(MSi)
    print(MSnxi)
    print(MSxi)
    MSnxi_sorted, MSnxi_dur_sorted  =   sort_MS_after_duration(input_dict,MSnxi)   
    MSxi_sorted, MSxi_dur_sorted    =   sort_MS_after_duration(input_dict,MSxi) 
    print(MSxi_sorted)
    print(MSxi_dur_sorted)
    slot                            =   [[0 for _ in range(nDays)] for _ in range(nRooms)]
    ext                             =   [[0 for _ in range(nDays)] for _ in range(nRooms)]
    flex                            =   [[0 for _ in range(nDays)] for _ in range(nRooms)]
    obj                             =   sum(Pi[c]*Q[g][c] for c in Ci for g in Gi)
    Q_rem                           =   Q
    
    for s in Si:
        for c in Ci:
            MSnxi_sorted, MSnxi_dur_sorted    =   update_patterns_list(input_dict, MSnxi, MSnxi_dur_sorted, Q_rem, s, c)
            MSxi_sorted, MSxi_dur_sorted      =   update_patterns_list(input_dict, MSxi, MSxi_dur_sorted, Q_rem, s, c)
    
    #----- assign slots greedy, all fixed ----- # 
    """for d in Di:
        for r in Ri:
            for s in SRi[r]:"""
            
    

    
    

def main(number_of_groups: int,flexibility: float, nScenarios: int, seed: int):
    file_name   = choose_correct_input_file(number_of_groups)
    input       = read_input(file_name)
    input       = generate_scenarios(input, nScenarios, seed)
    #input       = edit_input_to_number_of_groups(file_name,number_of_groups)
    run_greedy_construction_heuristic(input,flexibility,nScenarios,seed)

main(25,0,10,1)