from functions_input import *
from functions_output import *
from heuristic_greedy_construction import *

def main(number_of_groups: int,flexibility: float, nScenarios: int, seed: int):
    try:
        with open("solution_saved.pkl","rb") as f:
            saved_values    = pickle.load(f)
        input   =   saved_values["input"]
        results =   saved_values["results"]
        print_MSS(input,results)
    except FileNotFoundError:
        file_name   = choose_correct_input_file(number_of_groups)
        input       = read_input(file_name)
        input       = generate_scenarios(input, nScenarios, seed)
        results, input = run_model(input,flexibility,100,expected_value_solution=False,print_optimizer = True)
        results = categorize_slots(input,results)
        print_MSS(input,results)
        print_expected_bed_util_percent(input, results)
        print_expected_que(input, results)
        #--- Saving solution in pickle ---
        saved_values            =   {}
        saved_values["input"]   =   input
        saved_values["results"] =   results
        with open("solution_saved.pkl","wb") as f:
            pickle.dump(saved_values,f)
    run_greedy_construction_heuristic(input,results,debug=False)
    results = translate_heristic_results(input,results)
    print_MSS(input,results)
    print_expected_bed_util_percent(input, results)
    print_expected_que(input, results)
    

main(9,0.1,10,10)