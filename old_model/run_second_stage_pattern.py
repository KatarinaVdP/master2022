import pickle
import os.path
from typing import IO
from model_mip import *
from functions_input import *
from functions_output import *
from heuristic_second_stage_pattern import *


def run_second_stage_pattern(flexibility: float, number_of_groups: int, nScenarios: int, seed: int, time_limit: int, temperature, alpha, iter_max, end_temperature, new_input=True,parameter_tuning=False):
    print("\n\n")
    run_or_create_fast_start = False
    input_file_name =   choose_correct_input_file(number_of_groups)
    excel_file      =   "input_output/" + "results.xlsx"
    input           =   read_input(input_file_name)
    
    #---- Increasing the capacity of bed wards to normal level
    """input = change_ward_capacity(input, "MC", 60, 49)
    input = change_ward_capacity(input, "IC", 11, 6)"""

    #----- OBS! Dersom number_of_groups ikke er 9 eller 25 så vil funksjonen under vil gjøre det
    #----- trangt på wards uavhengig av om change_ward_capacity har blitt brukt til å relaksere
    input           =   edit_input_to_number_of_groups(input, number_of_groups)
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
        print_MSS(input, results)
    
        
        
        input           = generate_scenarios(input, nScenarios, seed)
        #--- Saving solution in pickle ---
        if run_or_create_fast_start:
            saved_values            =   {}
            saved_values["input"]   =   input
            saved_values["results"] =   results
            with open("model_solution.pkl","wb") as f:
                pickle.dump(saved_values,f)
        print('\n' * 5)
        
        #----- Begin Heuristic ----  
        print("------------------------------------------------------------------------------------------------------------------")
        print("INITIATING GREEDY HEURISTIC SEARCH FROM EVS")
        print("------------------------------------------------------------------------------------------------------------------")
        write_new_run_header_to_excel(excel_file,input,sheet_number=1)
        write_new_run_header_to_excel(excel_file,input,sheet_number=2)
        results, global_best_sol = heuristic_second_stage_pattern(excel_file, input, results, temperature, alpha, iter_max, end_temperature)
        results = translate_heristic_results(input,results)
        results = categorize_slots(input, results)
        
        print("\nGlobally best found solution:")
        print(global_best_sol["obj"])
        
        print_MSS(input, results)
        write_to_excel_MSS(excel_file,input,results,initial_MSS=False)
    return results, global_best_sol

"""start_temperature = 100
alpha = 0.5
iter_max = 25
end_temperature = 0.1

results, global_best_sol = run_second_stage_pattern(0.2, 9, 250, 1, 60, start_temperature, alpha, iter_max, end_temperature)"""

    
