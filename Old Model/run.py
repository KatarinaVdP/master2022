from input_functions import *
from model import *
from output_functions import *
import pickle
from typing import IO

def main(file_name, flexibility, nScenarios, seed, time_limit, new_input=True):
    print("\n\n")
    
    try:
        with open("Old Model/file.pkl","rb") as f:
            results_saved = pickle.load(f)
        print("loading pickle")
        print()
        input           = read_input(file_name)
        input_update    = generate_scenarios(input,nScenarios,seed)
        results_update  = categorize_slots(input_update, results_saved)
        print_MSS(input_update, results_update)
        print_expected_operations(input_update, results_update)    
        #print_expected_bed_util(input_update, results_update)       
                
    except IOError:
        input = read_input(file_name)
        print("Input has been read")

        input_update = generate_scenarios(input,nScenarios,seed)

        results, input_update_update = run_model(input_update, flexibility, time_limit)
        results_update  = categorize_slots(input_update_update, results)
        print_MSS(input_update, results_update)
        print_expected_operations(input_update, results_update)  

        with open("Old Model/file.pkl","wb") as f:
            pickle.dump(results,f)

main("Old Model/Input/model_input_9groups.xlsx",0.1, 10,1,30)