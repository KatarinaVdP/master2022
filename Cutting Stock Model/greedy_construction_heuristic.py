from input_functions import *

def update_non_ext_patterns(input_dict, MSnxi, Q_rem,s,c):
    for m in MSnxi:
        for g in input_dict["GSi"][s]:
            if (input_dict["A"][g][c] > Q_rem[g][c]):
                MSnxi.remove(m)
    return MSnxi

def update_ext_patterns(input_dict, MSxi, Q_rem,s,c):
    for m in MSxi:
        for g in input_dict["GSi"][s]:
            if (input_dict["A"][g][c] > Q_rem[g][c]):
                MSxi.remove(m)
    return MSxi

def construct_second_stage_sol(input, first_stage):
    Q_rem = input["Q"]
    unoperated = []
    for c in input["Ci"]:
        for s in input["Si"]:
            MSnxi = update_non_ext_patterns(input["MSnxi"])
            MSxi = update_ext_patterns(input["MSxi"])

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
    slot            =   [[0 for _ in range(nDays)] for _ in range(nRooms)]
    obj             =   sum(Pi[c]*Q[g][c] for c in Ci for g in Gi)
    for s in Si:
        for c in Ci:
            MSnxi = update_non_ext_patterns(input_dict,MSnxi,Q,s,c)
    
    
    

def main(number_of_groups: int, nScenarios:int, seed:int):
    file_name   = choose_correct_input_file(number_of_groups)
    input       = read_input(file_name)
    input       = generate_scenarios(input, nScenarios, seed)
    input       = edit_input_to_number_of_groups(file_name)
    