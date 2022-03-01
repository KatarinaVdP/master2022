from input_functions import *
from model import *
from output_functions import *
import pickle
from typing import IO


def print_MSS_minutes(input_dict, output_dict):

    print("Planning period modified MSS")
    print("-----------------------------")
    for i in range(1,input_dict["I"]+1):
        print("Cycle: ", i)
        print("        ", end="")
        nDaysInCycle = int(input_dict["nDays"]/input_dict["I"])
        firstDayInCycle = int(nDaysInCycle*(i-1)+1)
        for d in range(firstDayInCycle,firstDayInCycle+nDaysInCycle):
            day = "{0:<5}".format(str(d))
            print(day, end="")
        print()
        print("        ", end="")
        for d in range(firstDayInCycle,firstDayInCycle+nDaysInCycle):
            print("-----",end="")
        print()
        for r in input_dict["Ri"]:
            room = "{0:>8}".format(input_dict["R"][r]+"|")
            print(room, end="")
            for d in range(firstDayInCycle-1,firstDayInCycle+nDaysInCycle-1):
                if input_dict["N"][d] == 0:
                    print("{0:<5}".format("-"), end="")
                else:
                    minutes= sum((input_dict["L"][g]+input_dict["TC"]) * output_dict["x"][g][r][d][5] for g in input_dict["Gi"])
            
                    print("{0:<5}".format(int(minutes)), end="")
            print()
        print("        ", end="")
        for d in range(firstDayInCycle,firstDayInCycle+nDaysInCycle):
            print("-----",end="")
        print()
        print()
        print()
        print()

def main(flexibility: float, number_of_groups: int, nScenarios: int, seed: int, time_limit: int, new_input=True):
    print("\n\n")
    
    #----- choosing correct input file ----
    if number_of_groups in [4, 5, 12, 13]:
        num_specialties="_2or3spec"
    else:
        num_specialties="_5spec"  
            
    if number_of_groups in [4, 5, 9]:
        num_max_groups= "_9groups"
    elif number_of_groups in [12, 13, 25]:
        num_max_groups= "_25groups"
    else:
        print("Invalid number of groups")    
        return
    file_name= "Old Model/Input/" + "model_input" + num_max_groups + num_specialties + ".xlsx"
    
    try:
        with open("Old Model/file.pkl","rb") as f:
            saved_values = pickle.load(f)
        print("loading pickle")
        print()
        input           = saved_values["input"]
        results         = saved_values["results"]  
    except IOError:
        input           =   read_input(file_name)
        input           =   generate_scenarios(input,nScenarios,seed)
        results, input  =   run_model(input, number_of_groups, flexibility, time_limit)
        results         =   categorize_slots(input, results)
        
        saved_values            =   {}
        saved_values["input"]   =   input
        saved_values["results"] =   results
        with open("Old Model/file.pkl","wb") as f:
            pickle.dump(saved_values,f)

    print_MSS(input, results)
    print_expected_operations(input, results)    
    print_expected_bed_util(input, results)   
    print_MSS_minutes(input, results)
    print_que(input, results)
    
    print(input["P"])
            
main(0,9, 10,1,60)
