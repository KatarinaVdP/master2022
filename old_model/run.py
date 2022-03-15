from model import *
import pickle
from typing import IO
from input_functions import *
from output_functions import *
from heuristic import *
import os.path


def main(flexibility: float, number_of_groups: int, nScenarios: int, seed: int, time_limit: int, new_input=True):
    print("\n\n")
    
    input_file_name =   choose_correct_input_file(number_of_groups)
    excel_file      =   "input_output/" + "results.xlsx"
    input           =   read_input(input_file_name)
    input           =   edit_input_to_number_of_groups(input, number_of_groups)
    
    #----- Try to load initial model run from earlier ----  
    model_run_exists = False
    if os.path.exists("model_solution.pkl"):
        with open("model_solution.pkl","rb") as f:
            saved_values    = pickle.load(f)
        input_saved             =   saved_values["input"]
        nScenarios_saved        =   input_saved["nScenarios"]
        number_of_groups_saved  =   input_saved["number_of_groups"]
        seed_saved              =   input_saved["seed"]
        if os.path.exists('model.mps') and nScenarios == nScenarios_saved and number_of_groups == number_of_groups_saved and seed_saved == seed_saved:
            model_run_exists = True   
    if model_run_exists:     
        input = saved_values["input"]
        results = saved_values["results"]
        results = categorize_slots(input, results)
        print_MSS(input, results)
        #----- Begin Heuristic ---- 
        print("------------------------------------------------------------------------------------------------------------------")
        print("INITIATING HEURISTIC SEARCH FROM EVS - USING EXISTING MPS-FILE")
        print("------------------------------------------------------------------------------------------------------------------")
        obj_estimation_time = 30
        write_header_to_excel(excel_file,"first_iteration")
        results = heuristic('model.mps', 'warmstart.mst',excel_file, input, results, obj_estimation_time) # --- swap is called inside 
        print_solution_performance(input, results)
        results =   categorize_slots(input, results)
        print_MSS(input, results)   
    
    #----- If initial model run is not found, run as usual -----   
    else:
        #----- Find EVS as initial MSS ----  
        print("------------------------------------------------------------------------------------------------------------------")
        print("RUNNING MIP-MODEL TO FIND EVS")
        print("------------------------------------------------------------------------------------------------------------------")
        results, input  =   run_model(input, flexibility, time_limit, expected_value_solution = True, print_optimizer = False)
        print()
        print_solution_performance(input, results)
        if results["status"]==0:
            print('No solutions found in given runtime')
            return
        results =   categorize_slots(input, results)
        print_MSS(input, results)
        print('\n' * 5)
        
        #----- Creating model and fixed first-stage solution to EVS  ----   
        print("------------------------------------------------------------------------------------------------------------------")
        print("RUNNING FIXED FIRST-STAGE TO EVALUATE EVS PERFORMANCE")
        print("------------------------------------------------------------------------------------------------------------------") 
        input           = generate_scenarios(input, nScenarios, seed)
        results         = run_model_fixed(input,results,time_limit, print_optimizer=False) # --- 'model.mps' and 'warmstart.mst' are created
        print()
        print_solution_performance(input, results)
        write_to_excel(excel_file,input,results)
        print('\n' * 5)
        #--- Saving solution in pickle ---
        saved_values            =   {}
        saved_values["input"]   =   input
        saved_values["results"] =   results
        with open("model_solution.pkl","wb") as f:
            pickle.dump(saved_values,f)
        
        #----- Begin Heuristic ----  
        print("------------------------------------------------------------------------------------------------------------------")
        print("INITIATING HEURISTIC SEARCH FROM EVS")
        print("------------------------------------------------------------------------------------------------------------------")
        obj_estimation_time = 30
        write_header_to_excel(excel_file,"first_iteration")
        results = heuristic('model.mps', 'warmstart.mst',excel_file, input, results, obj_estimation_time) # --- swap is called inside 
        print_solution_performance(input, results)
        results =   categorize_slots(input, results)
        print_MSS(input, results)

main(0.2, 9, 20, 1, 20)

    
