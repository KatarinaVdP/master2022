from functions_input import *
from functions_output import *
from heuristic_greedy_construction import *
from model_mip import *
import pickle
import copy

def main(number_of_groups: int,flexibility: float, nScenarios: int, seed: int):
    file_name               =   choose_correct_input_file(number_of_groups)
    input                   =   read_input(file_name)

    
    try:
        with open("solution_saved.pkl","rb") as f:
            saved_values        =   pickle.load(f)
        input                   =   saved_values["input"]
        results                 =   saved_values["results"]
        input_h = copy.deepcopy(input)
        input_m = copy.deepcopy(input)
        results_h = copy.deepcopy(results)
        results_m = copy.deepcopy(results)
        print_MSS(input,results)
    except FileNotFoundError:
        file_name               =   choose_correct_input_file(number_of_groups)
        input                   =   read_input(file_name)
        input                   =   generate_scenarios(input, nScenarios, seed)
        results, input          =   run_model_mip(input,flexibility,20,expected_value_solution=False,print_optimizer = True)
        results                 =   categorize_slots(input,results)
        
        print_MSS(input,results)
        #print_expected_bed_util_percent(input, results)
        #print_expected_que(input, results)
        #--- Saving solution in pickle --- #
        saved_values            =   {}
        saved_values["input"]   =   input
        saved_values["results"] =   results
        input_h = copy.deepcopy(input)
        input_m = copy.deepcopy(input)
        results_h = copy.deepcopy(results)
        results_m = copy.deepcopy(results)
        with open("solution_saved.pkl","wb") as f:
            pickle.dump(saved_values,f)
    
    #print_MSS(input_m, results_m)
    #print_MSS(input_h, results_h)
    results_m=run_model_mip_fixed(input_m,results_m,10)
    print(results_m["obj"])
    print(results_m["best_bound"])
    print(results_h["obj"])
    results_h=run_greedy_construction_heuristic(input_h,results_h,debug=True) 
    #results_h=translate_heristic_results(input,results_h)
    #print_expected_que(input,results_h)
    #results = translate_heristic_results(input,results)
    #print_MSS(input,results)
    #print_expected_bed_util_percent(input, results)
    #print_expected_que(input, results)
    

main(9,0.05,2,8)