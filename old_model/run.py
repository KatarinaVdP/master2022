from model_mip import *
import pickle
from typing import IO
from functions_input import *
from functions_output import *
from heuristic_second_stage_mip import *
import os.path


def main(flexibility: float, number_of_groups: int, nScenarios: int, seed: int, time_limit: int, new_input=True):
    print("\n\n")
    
    input_file_name =   choose_correct_input_file(number_of_groups)
    excel_file      =   "input_output/" + "results.xlsx"
    input           =   read_input(input_file_name)
    
    #---- Increasing the capacity of bed wards to normal level
    input = change_ward_capacity(input, "MC", 60, 49)
    input = change_ward_capacity(input, "IC", 11, 6)
    
    #---- Adjusting the number of ORs available
    input = change_number_of_rooms_available(input, 6,6,6,6,6)

    #----- OBS! Funksjonen under vil gi gjøre det trangt på wards uavhengig av om
    #----- change_ward_capacity har blitt brukt til å relaksere
    input           =   edit_input_to_number_of_groups(input, number_of_groups)
    if not os.path.exists(excel_file):
        initiate_excel_book(excel_file,input)
    initiate_excel_book(excel_file,input)
    #----- Try to load initial model run from earlier ----  
    model_run_exists = False
    if os.path.exists("model_solution.pkl"):
        with open("model_solution.pkl","rb") as f:
            saved_values    = pickle.load(f)
        input_saved             =   saved_values["input"]
        nScenarios_saved        =   input_saved["nScenarios"]
        number_of_groups_saved  =   input_saved["number_of_groups"]
        seed_saved              =   input_saved["seed"]
        flexibility_saved       =   input_saved["F"]
        if os.path.exists('model.mps') and nScenarios == nScenarios_saved and number_of_groups == number_of_groups_saved and seed == seed_saved and flexibility == flexibility_saved:
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
        obj_estimation_time = 20
        results = heuristic_second_stage_mip('model.mps', 'warmstart.mst',excel_file, input, results, obj_estimation_time) # --- swap is called inside 
        print_solution_performance(input, results)
        results =   categorize_slots(input, results)
        print_MSS(input, results)
        write_to_excel_MSS(excel_file,input,results,initial_MSS=False)



    
    #----- If initial model run is not found, run as usual -----   
    else:
        #----- Find EVS as initial MSS ----  
        print("------------------------------------------------------------------------------------------------------------------")
        print("RUNNING MIP-MODEL TO FIND EVS")
        print("------------------------------------------------------------------------------------------------------------------")
        results, input  =   run_model_mip(input, flexibility, time_limit, expected_value_solution = True, print_optimizer = False)
        print()
        print_solution_performance(input, results)
        if results["status"]==0:
            print('No solutions found in given runtime')
            return
        print('\n' * 5)
        
        #----- Creating model and fixed first-stage solution to EVS  ----   
        print("------------------------------------------------------------------------------------------------------------------")
        print("RUNNING FIXED FIRST-STAGE TO EVALUATE EVS PERFORMANCE")
        print("------------------------------------------------------------------------------------------------------------------") 
        input           = generate_scenarios(input, nScenarios, seed)
        results         = run_model_mip_fixed(input,results,time_limit, print_optimizer=False) # --- 'model.mps' and 'warmstart.mst' are created
        results         = categorize_slots(input, results)
        print_solution_performance(input, results)
        write_new_run_header_to_excel(excel_file,input,sheet_number=0)
        write_new_run_header_to_excel(excel_file,input,sheet_number=2)
        write_to_excel_MSS(excel_file,input,results,initial_MSS=True)
        
        print()
        write_to_excel_MSS(excel_file,input,results,initial_MSS=True)
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
        write_new_run_header_to_excel(excel_file,input,sheet_number=1)
        obj_estimation_time = 20
        results = heuristic_second_stage_mip('model.mps', 'warmstart.mst',excel_file, input, results, obj_estimation_time) # --- swap is called inside 
        print_solution_performance(input, results)
        results =   categorize_slots(input, results)
        
        print_MSS(input, results)
        write_to_excel_MSS(excel_file,input,results,initial_MSS=False)

main(0.3, 9, 50, 1, 60)

    
