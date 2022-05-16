import random as rand
import gurobipy as gp
from gurobipy import GRB
import os.path
import time
from model_mip import *
from functions_input import *
from functions_output import *
from functions_heuristic import *
import pickle

def heuristic_second_stage_mip(model_file_name, warm_start_file_name, excel_file, input_dict, last_output, time_limit, start_temperature, alpha, iter_max, end_temperature, print_optimizer = False,MIPgap_limit=False,MIPgap_value=0.01):
    input                       =   input_dict
    start_time                  =   time.time()
    best_sol                    =   last_output
    m                           =   gp.read(model_file_name)
    m.update()
    
    if not print_optimizer:
        m.Params.LogToConsole   =   0
    m.setParam("TimeLimit", time_limit)
    if MIPgap_limit:
        m.setParam("MIPGap",MIPgap_value)
    m.update()
    print("\n"*3)

    run_new_warmstart           =   False
    global_iter                 =   1
    swap_types                  =   ['fix', 'ext', 'flex']
    levels                      =   math.ceil(np.log(end_temperature)/np.log(alpha))
    
    m, result_dict, best_sol    =   run_swap_fixed_with_flexible_UR_KA_EN(m, input, warm_start_file_name, excel_file, best_sol, start_time)
    
    print("\n\nHeuristic starts now.\n\n")
    print_heuristic_iteration_header()
    
    #----- Looping through temperature levels ----- 
    level                       =   1
    temperature                 =   copy.deepcopy(start_temperature)
    global_best_sol             =   copy.deepcopy(best_sol)
    
    while temperature >= (end_temperature * start_temperature):
        iter                    =   1
        #----- Looping through through iterations at temperature level -----
        while iter <= iter_max:
            extended            =   False
            swap_type           =   np.random.choice(swap_types)
            if swap_type == "ext":
                swap_found, getting_slot, giving_slot           =   swap_extension(input_dict, best_sol, print_swap = False)
            elif swap_type == "fix":
                swap_found, getting_slot, giving_slot           =   swap_fixed(input_dict, best_sol, print_swap = False)
            elif swap_type == "flex":
                swap_found, getting_slot, giving_slot, extended =   swap_fixed_with_flexible(input_dict, best_sol, print_swap = False)
            
            #----- Changing variable bound to evaluate candidate -----
            m                   =   change_bound_second_stage_mip(m, swap_found, getting_slot, giving_slot, swap_type, extended)
            
            if os.path.exists('new_warmstart.mst') and run_new_warmstart:
                m.read('new_warmstart.mst')
            else:
                m.read(warm_start_file_name)
            m.optimize()

            result_dict         =   save_results_pre(m)
            
            if result_dict["status"] == "INFEASIBLE":
                print('Swap is infeasible!')
                print('MSS before swap')
                print_MSS(input, best_sol)
                m               =   change_bound_second_stage_mip(m, swap_found, getting_slot, giving_slot, swap_type, extended, swap_back = True)
                m.update()
                print('Swapped back')
                continue
            
                #----- Granting more time if no feasible solution is found or swapping back -----
            nSolutions          =   m.SolCount
            if nSolutions==0:
                if result_dict["given_more_time"]==False and result_dict["status"] != "INFEASIBLE":
                    print('Did not find feasible solution within time limit of %i' %time_limit)
                    more_time                       =   3*time_limit
                    print('Try with new time limit of %i' %more_time)
                    m.setParam("TimeLimit", more_time)
                    #m.setParam("MIPFocus", 1) #finding solutions quickly
                    m.optimize()
                    result_dict                     =   save_results_pre(m)
                    result_dict["given_more_time"]  = True
                    
                    if result_dict["status"] == "INFEASIBLE":
                        print('Swap is infeasible! - found after giving more time')
                    nSolutions=m.SolCount
                    if nSolutions==0:
                        print('still did not find any solutions')
                        m               =   change_bound_second_stage_mip(m, swap_found, getting_slot, giving_slot, swap_type, extended, swap_back = True)
                        m.update()
                        print('Swapped back')
                        
                    else:
                        print('found %i solutions this time',nSolutions)
                else:
                    m = change_bound_second_stage_mip(m, swap_found, getting_slot, giving_slot, swap_type, extended, swap_back = True)
                    m.update()

                #----- Comparing candidate performance to best solution -----
            else:
                #----- Storing entire solution if a new best solution is found -----
                pick_worse_obj  =   rand.random()
                delta           =   result_dict["obj"] - best_sol["obj"]
                try:
                    exponential =   math.exp(-delta/temperature)
                except:
                    exponential =   0
                    
                if (result_dict["obj"]+0.1 < best_sol["obj"]) or (pick_worse_obj < exponential):

                    if result_dict["obj"] < global_best_sol["obj"]: 
                        global_best_sol             =   copy.deepcopy(result_dict)
                        global_best_sol["runtime"]  =   time.time() - start_time
                    
                    if result_dict["obj"]+0.1 < best_sol["obj"]:
                        action                      =   "MOVE"
                    else:
                        action                      =   "MOVE*"
                
                    m.write('new_warmstart.mst')
                    run_new_warmstart           = True
                    
                    best_sol                    = save_results(m, input, result_dict)
                    best_sol                    = categorize_slots(input, best_sol)
                    write_to_excel_model(excel_file,input,best_sol)

                else:
                    # ----- Copying the desicion variable values to result dictionary -----
                    result_dict                 =   save_results(m, input, result_dict)
                    write_to_excel_model(excel_file,input,result_dict)
                    action                      =   "NO MOVE"
                    m                           =   change_bound_second_stage_mip(m, swap_found, getting_slot, giving_slot, swap_type, extended, swap_back = True)
                    m.update()
            
            # ----- Printing iteration to console -----
            current_time        =   (time.time()-start_time)
            print_heuristic_iteration(best_sol["obj"], result_dict["obj"], swap_type, action, current_time, global_iter, level, levels, iter, iter_max, result_dict["MIPGap"])
            write_to_excel_heuristic(excel_file, input, best_sol["obj"], result_dict["obj"], action, current_time, global_iter, level, iter, result_dict["MIPGap"])
            iter               += 1
            global_iter        += 1 
        
        level              +=   1    
        temperature         =   update_temperature(temperature, alpha)
        best_sol["runtime"] =   time.time() - start_time  
    return best_sol, global_best_sol

def run_swap_fixed_with_flexible_UR_KA_EN(m, input, warm_start_file_name, excel_file, best_sol, start_time,print_swap=False):
    #----- Looping through and making all possible swap_fixed_with_flexible_UR_KA_EN swaps -----
    if print_swap:
        print("\n\nThe following changes are made due to swap_fixed_with_flexible_UR_KA_EN:\n\n")
    
    swap_ever_found = False
    days_in_cycle = int(input["nDays"]/input["I"])
    for d in range(days_in_cycle):
        swap_found, getting_slot, giving_slot, extended = swap_fixed_with_flexible_UR_KA_EN(d, input, best_sol, print_swap)
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
    #print_MSS(input, best_sol)
    
    #print_heuristic_iteration_header(False)

    if swap_ever_found:
        action = "MOVE"
    else:
        action = "NO MOVE"
    
    if print_swap:
        print_heuristic_iteration(best_sol["obj"], result_dict["obj"], action, "flex", time.time()-start_time, current_gap = result_dict["MIPGap"])
    write_to_excel_heuristic(excel_file, input, best_sol["obj"], result_dict["obj"], action,time.time()-start_time, 0, 0, 0, result_dict["MIPGap"])
    
    return m, result_dict, best_sol

def change_bound_second_stage_mip(m, swap_found, getting_slot, giving_slot, swap_type, extended, swap_back = False):

    if swap_type == "ext":
        var_name = "lambda"
    elif swap_type == "fix":
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

def run_second_stage_mip(beta: float, output_file_name:str ,flexibility: float, nGroups: int, nScenarios: int, seed: int, EVS_time: int,first_fix_time: int, obj_estimation_time: int, temperature, alpha, iter_max, end_temperature,MIPgap_limit=False,MIPgap_value=0.01):
    print("\n")
    run_or_create_fast_start    = False
    
    input_file_name =   choose_correct_input_file(nGroups)
    input           =   read_input(input_file_name)     
    
    excel_file      =   output_file_name   
    if not os.path.exists(excel_file):
        initiate_excel_book(excel_file,input)
    
    #---- Increasing the capacity of bed wards to normal level
    """if nGroups ==25:
        input           =   change_ward_capacity(input, "MC",72.4*beta,56*beta)
        input           =   change_ward_capacity(input, "IC",14.5*beta,6.1*beta) 
    elif nGroups ==9:
        input           =   change_ward_capacity(input, "MC",60*beta,49*beta)
        input           =   change_ward_capacity(input, "IC",11*beta,6*beta)  
    elif nGroups ==5:
        input           =   change_ward_capacity(input, "MC",50.5*beta,42*beta)
        input           =   change_ward_capacity(input, "IC",9.1*beta,5.6*beta)"""
    
    input           =   change_ward_capacity(input, "MC",60*beta,49*beta)
    input           =   change_ward_capacity(input, "IC",11*beta,6*beta)  

        
    #----- Try to load initial model run from earlier ----  
    if run_or_create_fast_start:
        model_run_exists = False
        if os.path.exists("model_solution.pkl"):
            with open("model_solution.pkl","rb") as f:
                saved_values    = pickle.load(f)
            input_saved             =   saved_values["input"]
            nScenarios_saved        =   input_saved["nScenarios"]
            nGroups_saved           =   input_saved["nGroups"]
            seed_saved              =   input_saved["seed"]
            flexibility_saved       =   input_saved["F"]
            if os.path.exists('model.mps') and nScenarios == nScenarios_saved and nGroups == nGroups_saved and seed == seed_saved and flexibility == flexibility_saved:
                model_run_exists = True   
        if model_run_exists:     
            input = saved_values["input"]
            results = saved_values["results"]
            results = categorize_slots(input, results)
            print_MSS(input, results)
            print_solution_performance(input, results)
            
            write_new_run_header_to_excel(excel_file,input,sheet_number=0)
            write_to_excel_model(excel_file,input,results)
            write_new_run_header_to_excel(excel_file,input,sheet_number=2)
            write_to_excel_MSS(excel_file,input,results,initial_MSS=True)
            #----- Begin Heuristic ---- 
            print("------------------------------------------------------------------------------------------------------------------")
            print("INITIATING HEURISTIC SEARCH FROM EVS - USING EXISTING MPS-FILE")
            print("------------------------------------------------------------------------------------------------------------------")
            write_new_run_header_to_excel(excel_file,input,sheet_number=1)
            if MIPgap_limit:
                results, global_best_sol = heuristic_second_stage_mip('model.mps', 'warmstart.mst',excel_file, input, results, obj_estimation_time, temperature, alpha, iter_max, end_temperature,MIPgap_limit=True,MIPgap_value=0.01) # --- swap is called inside 
            else:
                results, global_best_sol = heuristic_second_stage_mip('model.mps', 'warmstart.mst',excel_file, input, results, obj_estimation_time, temperature, alpha, iter_max, end_temperature,MIPgap_limit=False) # --- swap is called inside 
            print_solution_performance(input, results)
            results =   categorize_slots(input, results)

            write_to_excel_MSS(excel_file,input,results,initial_MSS=False)

    #----- If initial model run is not found, run as usual -----   
    else:
        #----- Find EVS as initial MSS ----  
        print("------------------------------------------------------------------------------------------------------------------")
        print("RUNNING MIP-MODEL TO FIND EVS")
        print("------------------------------------------------------------------------------------------------------------------")
        results, input  =   run_model_mip(input, flexibility, EVS_time, expected_value_solution = True, print_optimizer = False)
        print()
        print_solution_performance(input, results)
        #results         =   categorize_slots(input, results)
        #print_MSS(input, results)
        if results["status"]==0:
            print('No solutions found in given runtime')
            return
        print()
        
        #----- Creating model and fixed first-stage solution to EVS  ---- 
        print("------------------------------------------------------------------------------------------------------------------")
        print("RUNNING FIXED FIRST-STAGE TO EVALUATE EVS PERFORMANCE")
        print("------------------------------------------------------------------------------------------------------------------") 
        input           = generate_scenarios(input, nScenarios, seed)
        results         = run_model_mip_fixed(input,results,first_fix_time, print_optimizer=False,create_model_and_warmstart_file = True) # --- 'model.mps' and 'warmstart.mst' are created
        print()
        print_solution_performance(input, results)
        write_new_run_header_to_excel(excel_file,input,sheet_number=0)
        write_new_run_header_to_excel(excel_file,input,sheet_number=2)
        results =   categorize_slots(input, results)
        write_to_excel_MSS(excel_file,input,results,initial_MSS=True)
        print()
        
        #--- Saving solution in pickle ---
        if run_or_create_fast_start:
            saved_values            =   {}
            saved_values["input"]   =   input
            saved_values["results"] =   results
            with open("model_solution.pkl","wb") as f:
                pickle.dump(saved_values,f)
        
        #----- Begin Heuristic ----  
        print("------------------------------------------------------------------------------------------------------------------")
        print("INITIATING HEURISTIC SEARCH FROM EVS")
        print("------------------------------------------------------------------------------------------------------------------")
        write_new_run_header_to_excel(excel_file,input,sheet_number=1)
        string_to_write= ['EVS preformance:  obj: ' + str(results['obj']) + 'best bound: '+str(results['best_bound']) + 'MIPgap: '+str(results['MIPGap'])+'runtime : ' + str(results['runtime'])]
        write_string_to_excel(excel_file,input,string_to_write,sheet_number=1)
        results, global_best_sol = heuristic_second_stage_mip('model.mps', 'warmstart.mst',excel_file, input, results, obj_estimation_time, temperature, alpha, iter_max, end_temperature) # --- swap is called inside 
        print_solution_performance(input, results)
        write_to_excel_MSS(excel_file,input,results,initial_MSS=False)
        
    return results, global_best_sol, input
