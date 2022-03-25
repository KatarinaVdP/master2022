import random as rand
import gurobipy as gp
from gurobipy import GRB
from model_mip import *
from functions_input import *
from functions_output import *
import os.path
from functions_heuristic import *
from heuristic_greedy_construction import *
import pickle

"""flexibility = 0.3
number_of_groups = 9
nScenarios = 50
seed = 1"""

def heuristic_second_stage_pattern(model_file_name, warm_start_file_name, excel_file, input_dict, results, time_limit, print_optimizer = False):
    input=input_dict
    
    #####################################
    """try:
        with open("solution_saved.pkl","rb") as f:
            saved_values        =   pickle.load(f)
        input                   =   saved_values["input"]
        results                 =   saved_values["results"]
        print_MSS(input,results)
    except FileNotFoundError:
        file_name               =   choose_correct_input_file(number_of_groups)
        input                   =   read_input(file_name)
        input                   =   generate_scenarios(input, nScenarios, seed)
        results, input          =   run_model_mip(input,flexibility,40,expected_value_solution=False,print_optimizer=print_optimizer)
        results                 =   categorize_slots(input,results)
        print_MSS(input,results)
        #print_expected_bed_util_percent(input, results)
        #print_expected_que(input, results)
        #--- Saving solution in pickle ---
        saved_values            =   {}
        saved_values["input"]   =   input
        saved_values["results"] =   results
        with open("solution_saved.pkl","wb") as f:
            pickle.dump(saved_values,f)"""
    #####################################

    best_sol = copy.deepcopy(results)

    global_iter = 1
    levels = list(range(1, 4)) #levels blir følgende: levels = [1,2,3]
    level_iters = [10,10,10]
    
    #----- Looping through and making all possible swap_fixed_with_flexible_UR_KA_EN swaps -----
    print("\n\nThe following changes are made due to swap_fixed_with_flexible_UR_KA_EN:\n\n")
    
    swap_ever_found = False
    days_in_cycle = int(input["nDays"]/input["I"])
    for d in range(days_in_cycle):
        swap_found, getting_slot, giving_slot, extended = swap_fixed_with_flexible_UR_KA_EN(d, input_dict, best_sol, print_swap = True)
        if swap_found:
            swap_ever_found = True
            swap_type = "flex"
            results = change_bound_second_stage_pattern(results, swap_found, getting_slot, giving_slot, swap_type, extended)
            
    results = run_greedy_construction_heuristic(input, results)
    
    best_sol = copy.deepcopy(results)
    #write_to_excel_model(excel_file,input,best_sol)
    best_sol = categorize_slots(input, best_sol)
    print()
    print_MSS(input, best_sol)
    
    print_heuristic_iteration_header()

    if swap_ever_found:
        action = "MOVE"
    else:
        action = "NO MOVE"
    print_heuristic_iteration(0, 1, [1], 1, [1], best_sol["obj"], results["obj"], 1.23456, action)
    #write_to_excel_heuristic(excel_file, input, 0, 1, 1, best_sol["obj"], result_dict["obj"], result_dict["MIPGap"], action)
        
    print("\n\nHeuristic starts now.\n\n")
    
    print_heuristic_iteration_header()
    
    #----- Looping through temperature levels ----- 
    temperature = 1
    for level in levels:
        iter = 1
        temperature = update_temperature(temperature)
        
        #----- Looping through iterations at temperature level -----
        while iter <= level_iters[level-1]:
            
            extended = False
            swap_type = "fixed" 
            if swap_type == "ext":
                swap_found, getting_slot, giving_slot = swap_extension(input_dict, best_sol, print_swap = True)
            elif swap_type == "fixed":
                swap_found, getting_slot, giving_slot = swap_fixed_smart(input_dict, best_sol, print_swap = True)
            elif swap_type == "flex":
                swap_found, getting_slot, giving_slot, extended = swap_fixed_with_flexible_GN_GO(input_dict, best_sol, print_swap = True)
            
            #----- Changing variable bound to evaluate candidate -----
            results = change_bound_second_stage_pattern(results, swap_found, getting_slot, giving_slot, swap_type, extended)
            
            results = run_greedy_construction_heuristic(input, results)
            
            #----- Storing entire solution if a new best solution is found -----
            """pick_worse_obj = rand.random()
            delta = results["obj"] - best_sol["obj"]
            try:
                exponential = math.exp(-delta/temperature)
            except:
                exponential = 0"""
                
            if results["obj"] < best_sol["obj"]: #or pick_worse_obj < exponential:
                
                if results["obj"] < best_sol["obj"]:
                    action = "MOVE"
                else:
                    action = "MOVE*"
            
                best_sol = copy.deepcopy(results)
                #write_to_excel_model(excel_file,input,best_sol)
                best_sol = categorize_slots(input, best_sol)
                print_MSS(input, best_sol)
            else:
                # ----- Copying the desicion variable values to result dictionary -----
                #write_to_excel_model(excel_file,input,results)
                action = "NO MOVE"
                results = change_bound_second_stage_pattern(results, swap_found, getting_slot, giving_slot, swap_type, extended, swap_back = True)
            
            # ----- Printing iteration to console -----
            print_heuristic_iteration(global_iter, level, levels, iter, level_iters, best_sol["obj"], results["obj"], 123, action)
            #write_to_excel_heuristic(excel_file,input ,global_iter, level, iter, best_sol["obj"], result_dict["obj"], result_dict["MIPGap"], action)
            iter += 1
            global_iter += 1 
        
    return best_sol

def change_bound_second_stage_pattern(results, swap_found, getting_slot, giving_slot,swap_type, extended, swap_back = False):
    if swap_type == "ext":
        var_name = "lamb"
    elif swap_type == "fixed":
        var_name = "gamm"
    
    if swap_back:
        getting_val = 0
        giving_val = 1
    else:
        getting_val = 1
        giving_val = 0
    
    if swap_type == "fixed":
        if swap_found:
            for i in range(getting_slot["size"]):
                s=getting_slot["s"][i]
                r=getting_slot["r"][i]
                d=getting_slot["d"][i]
                results[var_name][s][r][d] = getting_val
                results["specialty_in_slot"][r][d] = s
            for i in range(giving_slot["size"]):
                s=giving_slot["s"][i]
                r=giving_slot["r"][i]
                d=giving_slot["d"][i]
                results[var_name][s][r][d] = giving_val
        else:
            print("Swap not found")
    elif swap_type == "ext":
        if swap_found:
            for i in range(getting_slot["size"]):
                s=getting_slot["s"][i]
                r=getting_slot["r"][i]
                d=getting_slot["d"][i]
                results[var_name][s][r][d] = getting_val
                results["extSlot"][r][d] = 1
            for i in range(giving_slot["size"]):
                s=giving_slot["s"][i]
                r=giving_slot["r"][i]
                d=giving_slot["d"][i]
                results[var_name][s][r][d] = giving_val
                results["extSlot"][r][d] = 0
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
                results["specialty_in_slot"][r][d] = s
                if extended:
                    results[var_name_2][s][r][d] = getting_val
                    results["extSlot"][r][d] = 1
            for i in range(giving_slot["size"]):
                s=giving_slot["s"][i]
                r=giving_slot["r"][i]
                d=giving_slot["d"][i]
                results[var_name_1][s][r][d] = giving_val
                results["specialty_in_slot"][r][d] = -1
                if extended:
                    results[var_name_2][s][r][d] = giving_val
                    results["extSlot"][r][d] = 0
        else:
            print("Swap not found")
    else:
        print("Invalid swap type passed to pattern_change_bound().")
    return results

"""def change_bound(m, swap_found, getting_slot, giving_slot, swap_type, extended, swap_back = False):
    if swap_type == "ext":
        var_name = "lambda"
    elif swap_type == "fixed":
        var_name = "gamma"
    
    if swap_type != "flex":
        if swap_back:
            getting_val = 0
            giving_val = 1
        else:
            getting_val = 1
            giving_val = 0
        
        if swap_found:
            for i in range(getting_slot["size"]):
                s=getting_slot["s"][i]
                r=getting_slot["r"][i]
                d=getting_slot["d"][i]
                name = f"{var_name}[{s},{r},{d}]"
                var = m.getVarByName(name)
                var.lb=getting_val
                var.ub=getting_val
            for i in range(giving_slot["size"]):
                s=giving_slot["s"][i]
                r=giving_slot["r"][i]
                d=giving_slot["d"][i]
                name = f"{var_name}[{s},{r},{d}]"
                var = m.getVarByName(name)
                var.lb=giving_val
                var.ub=giving_val
        else:
            print("Swap not found")
    else:
        if swap_back:
            getting_val = 0
            giving_val = 1
        else:
            getting_val = 1
            giving_val = 0
        
        if swap_found:
            var_name_1 = "gamma"
            var_name_2 = "lambda"
            for i in range(getting_slot["size"]):
                s=getting_slot["s"][i]
                r=getting_slot["r"][i]
                d=getting_slot["d"][i]
                name = f"{var_name_1}[{s},{r},{d}]"
                var = m.getVarByName(name)
                var.lb=getting_val
                var.ub=getting_val
                if extended:
                    name = f"{var_name_2}[{s},{r},{d}]"
                    var = m.getVarByName(name)
                    var.lb=getting_val
                    var.ub=getting_val
            for i in range(giving_slot["size"]):
                s=giving_slot["s"][i]
                r=giving_slot["r"][i]
                d=giving_slot["d"][i]
                name = f"{var_name_1}[{s},{r},{d}]"
                var = m.getVarByName(name)
                var.lb=giving_val
                var.ub=giving_val
                if extended:
                    name = f"{var_name_2}[{s},{r},{d}]"
                    var = m.getVarByName(name)
                    var.lb=giving_val
                    var.ub=giving_val
        else:
            print("Swap not found")
    return m"""