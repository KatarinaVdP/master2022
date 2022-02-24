from input_functions import *
from model import *
from output_functions import *
import pickle
from typing import IO

def main(flexibility: float, number_of_groups: int, nScenarios: int, seed: int, time_limit: int, new_input=True):
    print("\n\n")
    
    if number_of_groups==4 or number_of_groups==5 or number_of_groups==9:
        file_name="Old Model/Input/model_input_9groups.xlsx"
    elif number_of_groups==12 or number_of_groups==13 or number_of_groups==25:
        file_name="Old Model/Input/model_input.xlsx"
    else:
        print("Invalid number of groups")    
        return
    
    
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

        results, input_update_update = run_model(input_update, number_of_groups, flexibility, time_limit)
        results_update  = categorize_slots(input_update_update, results)

        print_MSS(input_update_update, results_update)
        print_expected_operations(input_update_update, results_update)
        
        """with open("Old Model/file.pkl","wb") as f:
            pickle.dump(results,f)""" 
main(0,4, 10,3,120)