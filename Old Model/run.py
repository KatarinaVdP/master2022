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
        
        
        nFixSlots = sum(results_update["gamm"][s][r][d] for s in input_update["Si"] for r in input_update["Ri"] for d in input_update["Di"])
        
        nFixSlotsCategory = sum(results_update["fixedSlot"][r][d] for r in input_update["Ri"] for d in input_update["Di"])
        nFlexSlotsCategory = sum(results_update["flexSlot"][r][d] for r in input_update["Ri"] for d in input_update["Di"])
        
        print("nFixSlots: %i " % nFixSlotsCategory)
        print("nFlexSlots: %i " % nFlexSlotsCategory)
        
        nSlots = (sum(input_update["N"][d] for d in input_update["Di"]) )
        frac = 1-float(nFixSlots/nSlots)
        print("Flexible share: %.2f" % frac)
        print(input_update["F"])
        print("Printing only gamm slots:")
                 
                
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