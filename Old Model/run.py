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
        print_GammSlots(input_update, results_update)
        print("Printing only fixed slots:")
        print_FixedSlots(input_update, results_update)
        print("Printing only flexible slots:")
        print_FlexSlots(input_update, results_update)                    
                
    except IOError:
        input = read_input(file_name)
        print("Input has been read")

        input_update = generate_scenarios(input,nScenarios,seed)

        results, input_update_update = run_model(input_update, flexibility, time_limit)
        results_update  = categorize_slots(input_update_update, results)
        print(results_update["fixedSlot"])

        with open("Old Model/file.pkl","wb") as f:
            pickle.dump(results,f)

main("Old Model/Input/model_input_9groups.xlsx",0.1, 10,1,30)