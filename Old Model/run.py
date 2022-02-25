from input_functions import *
from model import *
from output_functions import *
import pickle
from typing import IO

def main(flexibility: float, number_of_groups: int, nScenarios: int, seed: int, time_limit: int, new_input=True):
    print("\n\n")
    
    #----- choosing correct input file ----
    if number_of_groups==4 or number_of_groups==5:
        num_specialties="_2or3spec"
    else:
        num_specialties="_5spec"              
    if number_of_groups==4 or number_of_groups==5 or number_of_groups==9:
        num_max_groups= "_9groups"
    elif number_of_groups==12 or number_of_groups==13 or number_of_groups==25:
        num_max_groups= "_25groups"
    else:
        print("Invalid number of groups")    
        return
    file_name= "Old Model/Input/" + "model_input" + num_max_groups + num_specialties + ".xlsx"
    
    try:
        with open("Old Model/file.pkl","rb") as f:
            results_saved = pickle.load(f)
        print("loading pickle")
        print()
        input           = read_input(file_name)
        input    = generate_scenarios(input,nScenarios,seed)
        results  = categorize_slots(input, results_saved)
        print_MSS(input, results)

        print_expected_operations(input, results)    
        print_expected_bed_util(input, results)       
                
    except IOError:
        input = read_input(file_name)
        print("Input has been read")

        input = generate_scenarios(input,nScenarios,seed)

        results, input = run_model(input, number_of_groups, flexibility, time_limit)
        results  = categorize_slots(input, results)

        print_MSS(input, results)
        print_expected_operations(input, results)
        
        with open("Old Model/file.pkl","wb") as f:
            pickle.dump(results,f)
main(0,4, 10,3,60)