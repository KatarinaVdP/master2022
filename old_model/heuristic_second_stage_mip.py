import random as rand
import gurobipy as gp
from gurobipy import GRB
from model_mip import *
from functions_input import *
from functions_output import *
import os.path
from functions_heuristic import *

def heuristic_second_stage_mip(model_file_name, warm_start_file_name, excel_file, input_dict, last_output, time_limit, print_optimizer = False):
    input=input_dict
    
    best_sol = last_output
    m = gp.read(model_file_name)
    m.update()
    if not print_optimizer:
        m.Params.LogToConsole = 0
    m.setParam("TimeLimit", time_limit)
    m.update()
    print("\n"*3)

    run_new_warmstart = False
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
            m = change_bound_second_stage_mip(m, swap_found, getting_slot, giving_slot, swap_type, extended)
            
    m.read(warm_start_file_name)
    m.optimize()
    result_dict = save_results_pre(m)
    m.write('warmstart.mst')

    best_sol = save_results(m, input, result_dict)
    write_to_excel_model(excel_file,input,best_sol)
    best_sol = categorize_slots(input, best_sol)
    print()
    print_MSS(input, best_sol)
    
    print_heuristic_iteration_header(False)

    if swap_ever_found:
        action = "MOVE"
    else:
        action = "NO MOVE"
    print_heuristic_iteration(best_sol["obj"], result_dict["obj"], action, current_gap = result_dict["MIPGap"])
    write_to_excel_heuristic(excel_file, input, best_sol["obj"], result_dict["obj"], action, 0, 0, 0, result_dict["MIPGap"])
        
    print("\n\nHeuristic starts now.\n\n")
    
    print_heuristic_iteration_header()
    
    #----- Looping through temperature levels ----- 
    temperature = 1
    for level in levels:
        iter = 1
        temperature = update_temperature(temperature)
        
        #----- Looping through through iterations at temperature level -----
        while iter <= level_iters[level-1]:
            
            extended = False
            swap_type = "ext" 
            if swap_type == "ext":
                swap_found, getting_slot, giving_slot = swap_extension(input_dict, best_sol, print_swap = True)
            elif swap_type == "fixed":
                swap_found, getting_slot, giving_slot = swap_fixed_smart(input_dict, best_sol, print_swap = True)
            elif swap_type == "flex":
                swap_found, getting_slot, giving_slot, extended = swap_fixed_with_flexible_GN_GO(input_dict, best_sol, print_swap = True)
            
            #----- Changing variable bound to evaluate candidate -----
            m = change_bound_second_stage_mip(m, swap_found, getting_slot, giving_slot, swap_type, extended)
            
            if os.path.exists('new_warmstart.mst') and run_new_warmstart:
                m.read('new_warmstart.mst')
            else:
                m.read(warm_start_file_name)
            m.optimize()

            result_dict = save_results_pre(m)
            
            if result_dict["status"] == "INFEASIBLE":
                print('Swap is infeasible!')
                print('MSS before swap')
                print_MSS(input, best_sol)
                m = change_bound_second_stage_mip(m, swap_found, getting_slot, giving_slot, swap_type, extended, swap_back = True)
                m.update()
                print('Swapped back')
                continue
            
                #----- Granting more time if no feasible solution is found or swapping back -----
            nSolutions=m.SolCount
            if nSolutions==0:
                if result_dict["given_more_time"]==False and result_dict["status"] != "INFEASIBLE":
                    print('Did not find feasible solution within time limit of %i' %time_limit)
                    more_time = 3*time_limit
                    print('Try with new time limit of %i' %more_time)
                    #start = time.time()
                    m.setParam("TimeLimit", more_time)
                    #m.setParam("MIPFocus", 1) #finding solutions quickly
                    m.optimize()
                    #end = time.time()
                    #print(f"Runtime of new optimizer is {end - start}")
                    
                    result_dict = save_results_pre(m)
                    result_dict["given_more_time"] = True
                    if result_dict["status"] == "INFEASIBLE":
                        print('Swap is infeasible! - found after giving more time')
                    nSolutions=m.SolCount
                    if nSolutions==0:
                        print('still did not find any solutions')
                    else:
                        print('found %i solutions this time',nSolutions)
                else:
                    m = change_bound_second_stage_mip(m, swap_found, getting_slot, giving_slot, swap_type, extended, swap_back = True)
                    m.update()

                #----- Comparing candidate performance to best solution -----
            else:
                #----- Storing entire solution if a new best solution is found -----
                pick_worse_obj = rand.random()
                delta = result_dict["obj"] - best_sol["obj"]
                try:
                    exponential = math.exp(-delta/temperature)
                except:
                    exponential = 0
                    
                if result_dict["obj"] < best_sol["obj"] or pick_worse_obj < exponential:
                    
                    if result_dict["obj"] < best_sol["obj"]:
                        action = "MOVE"
                    else:
                        action = "MOVE*"
                
                    m.write('new_warmstart.mst')
                    run_new_warmstart = True
                    
                    best_sol = save_results(m, input, result_dict)
                    write_to_excel_model(excel_file,input,best_sol)
                    best_sol = categorize_slots(input, best_sol)
                    #print_MSS(input, best_sol)
                else:
                    # ----- Copying the desicion variable values to result dictionary -----
                    result_dict =  save_results(m, input, result_dict)
                    write_to_excel_model(excel_file,input,result_dict)
                    action = "NO MOVE"
                    m = change_bound_second_stage_mip(m, swap_found, getting_slot, giving_slot, swap_type, extended, swap_back = True)
                    m.update()
            
            # ----- Printing iteration to console -----
            print_heuristic_iteration(best_sol["obj"], result_dict["obj"], action, global_iter, level, levels, iter, level_iters, result_dict["MIPGap"])
            write_to_excel_heuristic(excel_file, input, best_sol["obj"], result_dict["obj"], action, global_iter, level, iter, result_dict["MIPGap"])
            iter += 1
            global_iter += 1 
        
    return best_sol

def change_bound_second_stage_mip(m, swap_found, getting_slot, giving_slot, swap_type, extended, swap_back = False):
    if swap_type == "ext":
        var_name = "lambda"
    elif swap_type == "fixed":
        var_name = "gamma"
    
    if swap_back:
        getting_val = 0
        giving_val = 1
    else:
        getting_val = 1
        giving_val = 0
    
    if swap_type != "flex":
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
    return m