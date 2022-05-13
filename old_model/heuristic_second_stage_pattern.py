import random as rand
from gurobipy import GRB
from model_mip import *
from functions_input import *
from functions_output import *
from functions_heuristic import *
from heuristic_greedy_construction import *
import pickle 

def heuristic_second_stage_pattern(excel_file, input_dict, results, start_temperature, alpha, iter_max, end_temperature):
    input=input_dict
    start_time = time.time()
    best_sol = copy.deepcopy(results)
    global_iter = 1
    swap_types = ["fix", "ext", "flex"]
    levels = math.ceil(np.log(end_temperature)/np.log(alpha))
    
    #----- Looping through and making all possible swap_fixed_with_flexible_UR_KA_EN swaps -----
    print("\n\nThe following changes are made due to swap_fixed_with_flexible_UR_KA_EN:\n\n")
    swap_ever_found = False
    days_in_cycle = int(input["nDays"]/input["I"])
    for d in range(days_in_cycle):
        swap_found, getting_slot, giving_slot, extended = swap_fixed_with_flexible_UR_KA_EN(d, input_dict, best_sol, print_swap = False)
        if swap_found:
            swap_ever_found = True
            swap_type = "flex"
            results = change_bound_second_stage_pattern(results, swap_found, getting_slot, giving_slot, swap_type, extended)
            results = run_greedy_construction_heuristic(input, results)
            results = translate_heristic_results(input,results)
            results = categorize_slots(input, results)
            
    if swap_ever_found:
        action = "MOVE"
    else:
        action = "NO MOVE" 
        
    best_sol = copy.deepcopy(results)
    print("\nPerformance of initial solution:  %d" % best_sol["obj"])
    write_to_excel_model(excel_file,input,best_sol)
    write_to_excel_heuristic(excel_file, input, best_sol["obj"], results["obj"], action, start_time - time.time(), 0, 0, 0)
    '''print()
    print_MSS(input, results)
    print()'''
    print_heuristic_iteration_header(True, False)
    
    #----- Looping through temperature levels ----- 
    level = 1
    temperature = copy.deepcopy(start_temperature)
    global_best_sol = copy.deepcopy(best_sol)
    
    while temperature >= end_temperature * start_temperature:
        iter = 1
        #----- Looping through iterations at temperature level -----
        while iter <= iter_max:
            
            extended = False
            swap_type = np.random.choice(swap_types)
            if swap_type == "ext":
                swap_found, getting_slot, giving_slot = swap_extension(input_dict, best_sol, print_swap = False)
            elif swap_type == "fix":
                swap_found, getting_slot, giving_slot = swap_fixed(input_dict, best_sol, print_swap = False)
            elif swap_type == "flex":
                swap_found, getting_slot, giving_slot, extended = swap_fixed_with_flexible(input_dict, best_sol, print_swap = False)
            
            #----- Changing variable bound to evaluate candidate -----
            results = change_bound_second_stage_pattern(results, swap_found, getting_slot, giving_slot, swap_type, extended)
            results = run_greedy_construction_heuristic(input, results)
            
            #----- Storing entire solution if a new best solution is found -----
            pick_worse_obj = rand.random()
            delta = results["obj"] - best_sol["obj"]
            try:
                exponential = math.exp(-delta/temperature)
            except:
                exponential = 0
            if delta == 0:
                exponential = 0
                
            if results["obj"]+0.1 < best_sol["obj"] or pick_worse_obj < exponential:
                
                if results["obj"] < global_best_sol["obj"]: 
                    global_best_sol = copy.deepcopy(results)
                    global_best_sol["runtime"] = time.time() - start_time  
                
                if results["obj"]+0.1 < best_sol["obj"]:
                    action = "MOVE"
                else:
                    action = "MOVE*"
            
                best_sol = copy.deepcopy(results)
                write_to_excel_model(excel_file,input,best_sol)
            else:
                # ----- Copying the desicion variable values to result dictionary -----
                write_to_excel_model(excel_file,input,results)
                action = "NO MOVE"
                results = change_bound_second_stage_pattern(results, swap_found, getting_slot, giving_slot, swap_type, extended, swap_back = True)
            
            # ----- Printing iteration to console -----
            current_time = (time.time()-start_time)
            print_heuristic_iteration(best_sol["obj"], results["obj"], swap_type, action, current_time, global_iter, level, levels, iter, iter_max)
            write_to_excel_heuristic(excel_file, input, best_sol["obj"], results["obj"], action, current_time, global_iter, level, iter, results["MIPGap"])
            iter += 1
            global_iter += 1 
            
        level += 1    
        temperature = update_temperature(temperature, alpha)
        
    best_sol["runtime"] = time.time() - start_time  
    return best_sol, global_best_sol

def heuristic_second_stage_pattern_param_tuning(input_dict, results, start_temperature, alpha, iter_max, end_temperature):
    input=input_dict
    start_time = time.time()
    best_sol = copy.deepcopy(results)
    global_iter = 1
    swap_types = ["fix", "ext", "flex"]
    levels = math.ceil(np.log(end_temperature)/np.log(alpha))
    
    #----- Looping through and making all possible swap_fixed_with_flexible_UR_KA_EN swaps -----
    print("\n\nThe following changes are made due to swap_fixed_with_flexible_UR_KA_EN:\n\n")
    swap_ever_found = False
    days_in_cycle = int(input["nDays"]/input["I"])
    for d in range(days_in_cycle):
        swap_found, getting_slot, giving_slot, extended = swap_fixed_with_flexible_UR_KA_EN(d, input_dict, best_sol, print_swap = False)
        if swap_found:
            swap_ever_found = True
            swap_type = "flex"
            results = change_bound_second_stage_pattern(results, swap_found, getting_slot, giving_slot, swap_type, extended)
            results = run_greedy_construction_heuristic(input, results)
            results = translate_heristic_results(input,results)
            results = categorize_slots(input, results)
            
    if swap_ever_found:
        action = "MOVE"
    else:
        action = "NO MOVE" 
    best_sol = copy.deepcopy(results)
    
    #----- Looping through temperature levels ----- 
    level = 1
    temperature = copy.deepcopy(start_temperature)
    global_best_sol = copy.deepcopy(best_sol)
    
    while temperature >= end_temperature * start_temperature:
        iter = 1
        #----- Looping through iterations at temperature level -----
        while iter <= iter_max:
            
            extended = False
            swap_type = np.random.choice(swap_types)
            if swap_type == "ext":
                swap_found, getting_slot, giving_slot = swap_extension(input_dict, best_sol, print_swap = False)
            elif swap_type == "fix":
                swap_found, getting_slot, giving_slot = swap_fixed(input_dict, best_sol, print_swap = False)
            elif swap_type == "flex":
                swap_found, getting_slot, giving_slot, extended = swap_fixed_with_flexible(input_dict, best_sol, print_swap = False)
            
            #----- Changing variable bound to evaluate candidate -----
            results = change_bound_second_stage_pattern(results, swap_found, getting_slot, giving_slot, swap_type, extended)
            results = run_greedy_construction_heuristic(input, results)
            
            #----- Storing entire solution if a new best solution is found -----
            pick_worse_obj = rand.random()
            delta = results["obj"] - best_sol["obj"]
            try:
                exponential = math.exp(-delta/temperature)
            except:
                exponential = 0
            if delta == 0:
                exponential = 0
                
            if results["obj"]+0.1 < best_sol["obj"] or pick_worse_obj < exponential:
                
                if results["obj"] < global_best_sol["obj"]: 
                    global_best_sol = copy.deepcopy(results)
                    global_best_sol["runtime"] = time.time() - start_time  
                
                if results["obj"]+0.1 < best_sol["obj"]:
                    action = "MOVE"
                else:
                    action = "MOVE*"
            
                best_sol = copy.deepcopy(results)
            else:
                # ----- Copying the desicion variable values to result dictionary -----
                action = "NO MOVE"
                results = change_bound_second_stage_pattern(results, swap_found, getting_slot, giving_slot, swap_type, extended, swap_back = True)
            
            # ----- Printing iteration to console -----
            current_time = (time.time()-start_time)
            print_heuristic_iteration(best_sol["obj"], results["obj"], swap_type, action, current_time, global_iter, level, levels, iter, iter_max)
            iter += 1
            global_iter += 1 
            
        level += 1    
        temperature = update_temperature(temperature, alpha)
        
    best_sol["runtime"] = time.time() - start_time  
    return best_sol, global_best_sol

def change_bound_second_stage_pattern(results, swap_found, getting_slot, giving_slot, swap_type, extended, swap_back = False):
    
    if swap_type == "ext":
        var_name = "lamb"
    elif swap_type == "fix":
        var_name = "gamm"
    
    if swap_back:
        getting_val = 0
        giving_val = 1
    else:
        getting_val = 1
        giving_val = 0
    
    if swap_type == "fix":
        if swap_found:
            for i in range(getting_slot["size"]):
                s=getting_slot["s"][i]
                r=getting_slot["r"][i]
                d=getting_slot["d"][i]
                results[var_name][s][r][d] = getting_val
                if not swap_back:
                    results["specialty_in_slot"][r][d] = s
            for i in range(giving_slot["size"]):
                s=giving_slot["s"][i]
                r=giving_slot["r"][i]
                d=giving_slot["d"][i]
                results[var_name][s][r][d] = giving_val
                if swap_back:
                    results["specialty_in_slot"][r][d] = s
        else:
            print("Swap not found")
    elif swap_type == "ext":
        if swap_found:
            for i in range(getting_slot["size"]):
                s=getting_slot["s"][i]
                r=getting_slot["r"][i]
                d=getting_slot["d"][i]
                results[var_name][s][r][d] = getting_val
                results["extSlot"][r][d] = getting_val
            for i in range(giving_slot["size"]):
                s=giving_slot["s"][i]
                r=giving_slot["r"][i]
                d=giving_slot["d"][i]
                results[var_name][s][r][d] = giving_val
                results["extSlot"][r][d] = giving_val
        else:
            print("Swap not found")
    elif swap_type == "flex":
        if swap_found:
            var_name_1 = "gamm"
            var_name_2 = "lamb"
            for i in range(getting_slot["size"]):
                s=getting_slot["s"][i]
                r=getting_slot["r"][i]
                d=getting_slot["d"][i]
                results[var_name_1][s][r][d] = getting_val
                if not swap_back:
                    results["specialty_in_slot"][r][d] = s
                if extended:
                    results[var_name_2][s][r][d] = getting_val
                    results["extSlot"][r][d] = getting_val
            for i in range(giving_slot["size"]):
                s=giving_slot["s"][i]
                r=giving_slot["r"][i]
                d=giving_slot["d"][i]
                results[var_name_1][s][r][d] = giving_val
                if not swap_back:
                    results["specialty_in_slot"][r][d] = -1
                else:
                    results["specialty_in_slot"][r][d] = s
                if extended:
                    results[var_name_2][s][r][d] = giving_val
                    results["extSlot"][r][d] = giving_val
        else:
            print("Swap not found")
    else:
        print("Invalid swap type passed to pattern_change_bound().")
    return results

def run_second_stage_pattern_param_tuning(flexibility: float, number_of_groups: int, nScenarios: int, seed: int, time_limit: int, temperature, alpha, iter_max, end_temperature, new_input=True,parameter_tuning=False):
    print("\n\n")
    input_file_name =   choose_correct_input_file(number_of_groups)
    input           =   read_input(input_file_name)

    #----- If initial model run is not found, run as usual -----   
    #----- Find EVS as initial MSS ----  
    print("RUNNING MIP-MODEL TO FIND EVS")
    results, input  =   run_model_mip(input, flexibility, time_limit, expected_value_solution = True, print_optimizer = False)
    if results["status"]==0:
        print('No solutions found in given runtime')
        return
    results         = categorize_slots(input, results)
    input           = generate_scenarios(input, nScenarios, seed)
    #--- Saving solution in pickle ---
    saved_values            =   {}
    saved_values["input"]   =   input
    saved_values["results"] =   results
    with open("model_solution.pkl","wb") as f:
        pickle.dump(saved_values,f)
    
    #----- Begin Heuristic ----  
    print("INITIATING GREEDY HEURISTIC SEARCH FROM EVS")
    
    results, global_best_sol = heuristic_second_stage_pattern_param_tuning(input, results, temperature, alpha, iter_max, end_temperature)
    return results, global_best_sol

def run_second_stage_pattern(beta: float,output_file_name: str, flexibility: float, number_of_groups: int, nScenarios: int, seed: int, time_limit: int, temperature, alpha, iter_max, end_temperature, new_input=True,parameter_tuning=False):
    print("\n\n")
    run_or_create_fast_start = False
    input_file_name =   choose_correct_input_file(number_of_groups)
    excel_file      =   output_file_name
    input           =   read_input(input_file_name)

    #---- Increasing the capacity of bed wards to normal level
    if number_of_groups ==25:
        input           =   change_ward_capacity(input, "MC",72.4*beta,56*beta)
        input           =   change_ward_capacity(input, "IC",14.5*beta,6.1*beta) 
    elif number_of_groups ==9:
        input           =   change_ward_capacity(input, "MC",60*beta,49*beta)
        input           =   change_ward_capacity(input, "IC",11*beta,6*beta)  
    elif number_of_groups ==5:
        input           =   change_ward_capacity(input, "MC",50.5*beta,42*beta)
        input           =   change_ward_capacity(input, "IC",9.1*beta,5.6*beta)
    
    
    if not os.path.exists(excel_file):
        initiate_excel_book(excel_file,input)
    #----- Try to load initial model run from earlier ----  
    if run_or_create_fast_start:
        model_run_exists = False
        if os.path.exists("model_solution.pkl"):
            with open("model_solution.pkl","rb") as f:
                saved_values    = pickle.load(f)
            input_saved             =   saved_values["input"]
            nScenarios_saved        =   input_saved["nScenarios"]
            number_of_groups_saved  =   input_saved["number_of_groups"]
            seed_saved              =   input_saved["seed"]
            flexibility_saved       =   input_saved["F"]

            if nScenarios == nScenarios_saved and number_of_groups == number_of_groups_saved and seed == seed_saved and flexibility == flexibility_saved:
                model_run_exists = True
        if model_run_exists:     
            input = saved_values["input"]
            results = saved_values["results"]
            print("------------------------------------------------------------------------------------------------------------------")
            print("PICKLED RESULTS OF EVS (DETERMINISTIC)")
            print("------------------------------------------------------------------------------------------------------------------")
            print_solution_performance(input, results)
            print_MSS(input, results)
            
            write_new_run_header_to_excel(excel_file,input,sheet_number=0)
            write_to_excel_model(excel_file,input,results)
            write_to_excel_MSS(excel_file,input,results,initial_MSS=True)
            print('\n' * 5)

            print("------------------------------------------------------------------------------------------------------------------")
            print("INITIATING GREEDY HEURISTIC SEARCH FROM EVS - USING PICKLED RESULTS")
            print("------------------------------------------------------------------------------------------------------------------")
            print()
            write_new_run_header_to_excel(excel_file,input,sheet_number=1)
            write_new_run_header_to_excel(excel_file,input,sheet_number=2)
            results, global_best_sol = heuristic_second_stage_pattern(excel_file, input, results, temperature, alpha, iter_max, end_temperature) # --- swap is called inside 
            results = translate_heristic_results(input,results)
            results =   categorize_slots(input, results)
            
            print("\nGlobally best found solution:")
            print(global_best_sol["obj"])
            
            print_solution_performance(input, results)
            print_MSS(input, results)
            write_to_excel_MSS(excel_file,input,results,initial_MSS=False)

    #----- If initial model run is not found, run as usual -----   
    else:
        #----- Find EVS as initial MSS ----  
        print("------------------------------------------------------------------------------------------------------------------")
        print("RUNNING MIP-MODEL TO FIND EVS")
        print("------------------------------------------------------------------------------------------------------------------")
        results, input  =   run_model_mip(input, flexibility, time_limit, expected_value_solution = True, print_optimizer = False)
        if results["status"]==0:
            print('No solutions found in given runtime')
            return
        results         = categorize_slots(input, results)
        print_solution_performance(input, results)
        #print_MSS(input, results)
    
        
        input           = generate_scenarios(input, nScenarios, seed)
        #--- Saving solution in pickle ---
        if run_or_create_fast_start:
            saved_values            =   {}
            saved_values["input"]   =   input
            saved_values["results"] =   results
            with open("model_solution.pkl","wb") as f:
                pickle.dump(saved_values,f)
        print('\n')
        
        #----- Begin Heuristic ----  
        print("------------------------------------------------------------------------------------------------------------------")
        print("INITIATING GREEDY HEURISTIC SEARCH FROM EVS")
        print("------------------------------------------------------------------------------------------------------------------")
        write_new_run_header_to_excel(excel_file,input,sheet_number=1)
        write_new_run_header_to_excel(excel_file,input,sheet_number=2)
        
        results, global_best_sol = heuristic_second_stage_pattern(excel_file, input, results, temperature, alpha, iter_max, end_temperature)
        results = translate_heristic_results(input,results)
        results = categorize_slots(input, results)
        
        #print("\nGlobally best found solution:")
        #print(global_best_sol["obj"])
        
        #print_MSS(input, results)
        write_to_excel_MSS(excel_file,input,results,initial_MSS=False)
    return results, global_best_sol, input
    

