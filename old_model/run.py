from model import *
import pickle
from typing import IO
from input_functions import *
from output_functions import *
from heuristic import *


def main(flexibility: float, number_of_groups: int, nScenarios: int, seed: int, time_limit: int, new_input=True):
    print("\n\n")
    
    #----- Choose input/output file ----  
    if number_of_groups in [4, 5, 9]:
        num_max_groups= "_9groups"
    elif number_of_groups in [12, 13, 25]:
        num_max_groups= "_25groups"
    else:
        print("Invalid number of groups")    
        return
    file_name= "input_output/" + "model_input" + num_max_groups + ".xlsx"
    excel_file="input_output/" + "results.xlsx"
    input           =   read_input(file_name)
    input           =   edit_input_to_number_of_groups(input, number_of_groups)
    
    variabel = True
    if variabel:
        #----- Begin Heuristic ----  
        print("------------------------------------------------------------------------------------------------------------------")
        print("INITIATING HEURISTIC SEARCH FROM EVS")
        print("------------------------------------------------------------------------------------------------------------------")
        obj_estimation_time = 10
        write_header_to_excel(excel_file,"first_iteration")
        results = heuristic('model.mps', 'warmstart.mst',excel_file, input, results, obj_estimation_time) # --- swap is called inside 
        print_solution_performance(input, results)
        results =   categorize_slots(input, results)
        print_MSS(input, results)
    
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
    
    #----- Begin Heuristic ----  
    print("------------------------------------------------------------------------------------------------------------------")
    print("INITIATING HEURISTIC SEARCH FROM EVS")
    print("------------------------------------------------------------------------------------------------------------------")
    obj_estimation_time = 10
    write_header_to_excel(excel_file,"first_iteration")
    results = heuristic('model.mps', 'warmstart.mst',excel_file, input, results, obj_estimation_time) # --- swap is called inside 
    print_solution_performance(input, results)
    results =   categorize_slots(input, results)
    print_MSS(input, results)


   
    main(0, 9, 40, 1, 30)

    
"""try:
    with open("Old Model/file.pkl","rb") as f:
        saved_values = pickle.load(f)
    input           = saved_values["input"]
    results         = saved_values["results"]  
except IOError:
    input           =   read_input(file_name)
    input           =   generate_scenarios(input,nScenarios,seed)
    input           =   edit_input_to_number_of_groups(input, number_of_groups)
    results, input  =   run_model(input, flexibility, time_limit)
    saved_values            =   {}
    saved_values["input"]   =   input
    saved_values["results"] =   results
    with open("Cutting Stock Model/file.pkl","wb") as f:
        pickle.dump(saved_values,f)"""
    
