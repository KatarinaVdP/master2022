from input_functions import *
from model import *
from output_functions import *
import pickle
from typing import IO

def main(file_name, nScenarios, seed, time_limit, new_input=True):
    
    try:
        with open("Old Model/file.pkl","rb") as f:
            results_saved = pickle.load(f)
        print("loading pickle")
        input           = read_input(file_name)
        input_update    = generate_scenarios(input,nScenarios,seed)
        results_update  = categorize_slots(input_update, results_saved )
    
        print(results_update["fixedSlot"])
        print(results_update["nameFixedSlot"])
        print(results_update["flexSlot"])
        print(results_update["extSlot"])
        print(results_update["unassSlot"])

        """print("outside run_model():")"""
        """x_sol = results_saved["x"]
        for g in input_update["Gi"]:
            for r in input_update["Ri"]:
                for d in input_update["Di"]:
                    for c in input_update["Ci"]:     
                        if x_sol[(g,r,d,c)]>0:
                            print("key", (g,r,d,c))
                            print("value",x_sol[(g,r,d,c)])"""

        """ gamm_sol = results_saved["gamm"]
        for s in input_update["Si"]:
            for r in input_update["Ri"]:
                for d in input_update["Di"]:    
                    if gamm_sol[(s,r,d)]>0:
                        print("key", (s,r,d))
                        print("value",gamm_sol[(s,r,d)])"""
                    
                
    except IOError:
        input = read_input(file_name)
        print("Input has been read")

        input_update = generate_scenarios(input,nScenarios,seed)

        results = run_model(input_update,time_limit)
        results_update  = categorize_slots(input_update, results)
        print(results_update["fixedSlot"])


        """print("outside run_model():")
        
        gamm_sol = results["gamm"]
        for s in input_update["Si"]:
            for r in input_update["Ri"]:
                for d in input_update["Di"]:    
                    if gamm_sol[(s,r,d)]>0:
                        print("key", (s,r,d))
                        print("value",gamm_sol[(s,r,d)])"""
        
        """x_sol = results["x"]
        for g in input_update["Gi"]:
            for r in input_update["Ri"]:
                for d in input_update["Di"]:
                    for c in input_update["Ci"]:     
                        if x_sol[(g,r,d,c)]>0:
                            print("key", (g,r,c,d))
                            print("value",x_sol[(g,r,d,c)])"""
        with open("Old Model/file.pkl","wb") as f:
            pickle.dump(results,f)

main("Old Model/Input/model_input.xlsx",10,1,15)