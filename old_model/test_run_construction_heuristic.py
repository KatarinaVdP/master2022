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
        with open("solution_saved1.pkl","rb") as f:
            saved_values        =   pickle.load(f)
        input                   =   saved_values["input"]
        results                 =   saved_values["results"]
        print_MSS(input,results)
    except FileNotFoundError:
        file_name               =   choose_correct_input_file(number_of_groups)
        input                   =   read_input(file_name)
        input                   =   generate_scenarios(input, 3, seed)
        results, input          =   run_model_mip(input,flexibility,10,expected_value_solution=False,print_optimizer = True)
        results                 =   categorize_slots(input,results)
        
        print_MSS(input,results)
        #--- Saving solution in pickle --- #
        input                   =   generate_scenarios(input, nScenarios, seed)
        saved_values            =   {}
        saved_values["input"]   =   input
        saved_values["results"] =   results
        with open("solution_saved1.pkl","wb") as f:
            pickle.dump(saved_values,f)


    input_h                             = generate_scenarios(input,nScenarios, seed)
    
    results_m                           =   copy.deepcopy(results)
    results_h                           =   copy.deepcopy(results)
    results_h_smart_flex                =   copy.deepcopy(results)
    results_h_smarter_flex              =   copy.deepcopy(results)
    results_h_smart_fix                 =   copy.deepcopy(results)
    results_h_smart_fix_smart_flex      =   copy.deepcopy(results)
    results_h_smart_fix_smarter_flex    =   copy.deepcopy(results)
    results_h_smarter_fix               =   copy.deepcopy(results)
    results_h_smarter_fix_smart_flex    =   copy.deepcopy(results)
    results_h_smarter_fix_smarter_flex  =   copy.deepcopy(results)

    results_h                           =   run_greedy_construction_heuristic(input_h,results_h)
    results_h_smart_flex                =   run_greedy_construction_heuristic_smart_flex(input_h,results_h_smart_flex)
    results_h_smarter_flex              =   run_greedy_construction_heuristic(input_h,results_h_smarter_flex)
    results_h_smart_fix                 =   run_greedy_construction_heuristic_smart_fix(input_h,results_h_smart_fix)
    results_h_smart_fix_smart_flex      =   run_greedy_construction_heuristic_smart_fix_smart_flex(input_h,results_h_smart_fix_smart_flex)
    results_h_smart_fix_smarter_flex    =   run_greedy_construction_heuristic_smart_fix_smarter_flex(input_h,results_h_smart_fix_smarter_flex)
    results_h_smarter_fix               =   run_greedy_construction_heuristic_smarter_fix(input_h,results_h_smarter_fix)
    results_h_smarter_fix_smart_flex    =   run_greedy_construction_heuristic_smarter_fix_smart_flex(input_h,results_h_smarter_fix_smart_flex)
    results_h_smarter_fix_smarter_flex  =   run_greedy_construction_heuristic_smarter_fix_smarter_flex(input_h,results_h_smarter_fix_smarter_flex)
    
    print("best bound MIP:                  " + "{0:<10}".format("{:.1f}".format(results_m["obj"])) )
    print("heur:                            " + "{0:<10}".format("{:.1f}".format(results_h["obj"])) + "time: " + "{0:<5}".format("{:.2f}".format(results_h["heuristic_time"])))
    print("heur_smart_flex:                 " + "{0:<10}".format("{:.1f}".format(results_h_smart_flex["obj"])) + "time: " + "{0:<5}".format("{:.2f}".format(results_h_smart_flex["heuristic_time"])))
    print("heur_smarter_flex:               " + "{0:<10}".format("{:.1f}".format(results_h_smarter_flex["obj"])) + "time: " + "{0:<5}".format("{:.2f}".format(results_h_smarter_flex["heuristic_time"])))
    print("heur_smart_fix:                  " + "{0:<10}".format("{:.1f}".format(results_h_smart_fix["obj"])) + "time: " + "{0:<5}".format("{:.2f}".format(results_h_smart_fix["heuristic_time"])))
    print("heur_smart_fix_smart_flex:       " + "{0:<10}".format("{:.1f}".format(results_h_smart_fix_smart_flex["obj"])) + "time: " + "{0:<5}".format("{:.2f}".format(results_h_smart_fix_smart_flex["heuristic_time"])))
    print("heur_smart_fix_smarter_flex:     " + "{0:<10}".format("{:.1f}".format(results_h_smart_fix_smarter_flex["obj"])) + "time: " + "{0:<5}".format("{:.2f}".format(results_h_smart_fix_smarter_flex["heuristic_time"])))
    print("heur_smarter_fix:                " + "{0:<10}".format("{:.1f}".format(results_h_smarter_fix["obj"])) + "time: " + "{0:<5}".format("{:.2f}".format(results_h_smarter_fix["heuristic_time"])))
    print("heur_smarter_fix_smart_flex:     " + "{0:<10}".format("{:.1f}".format(results_h_smarter_fix_smart_flex["obj"])) + "time: " + "{0:<5}".format("{:.2f}".format(results_h_smarter_fix_smart_flex["heuristic_time"])))
    print("heur_smarter_fix_smarter_flex:   " + "{0:<10}".format("{:.1f}".format(results_h_smarter_fix_smarter_flex["obj"])) + "time: " + "{0:<5}".format("{:.2f}".format(results_h_smarter_fix_smarter_flex["heuristic_time"])))
    
    #results_h=translate_heristic_results(input,results_h)
    #print_expected_que(input,results_h)
    #results = translate_heristic_results(input,results)
    #print_MSS(input,results)
    #print_expected_bed_util_percent(input, results)
    #print_expected_que(input, results)
    #print(results_h["obj"])

main(9,0,30,10)