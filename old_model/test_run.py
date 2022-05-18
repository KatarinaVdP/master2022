from random import seed
from functions_input import *
from functions_output import *
from model_cutting_stock import *
from model_mip import *


nGroups         = 9
nScenarios      = 5
seed            = 1
flex            = 0.1
time_limit      = 10

beta            = 1.0

input_file_name =   choose_correct_input_file(nGroups)
input           =   read_input(input_file_name)

"""if nGroups ==25:
        input           =   change_ward_capacity(input, "MC",72.4*beta,56*beta)
        input           =   change_ward_capacity(input, "IC",14.5*beta,6.1*beta) 
    elif nGroups ==9:
        input           =   change_ward_capacity(input, "MC",60*beta,49*beta)
        input           =   change_ward_capacity(input, "IC",11*beta,6*beta)  
    elif nGroups ==5:
        input           =   change_ward_capacity(input, "MC",50.5*beta,42*beta)
        input           =   change_ward_capacity(input, "IC",9.1*beta,5.6*beta)"""
    
input           =   change_ward_capacity(input, "MC",60*beta,49*beta)
input           =   change_ward_capacity(input, "IC",11*beta,6*beta)  

input           =   generate_scenarios(input, nScenarios, seed)
results, input  =   run_model_mip(input, flex, time_limit, expected_value_solution = False, print_optimizer = True)
print("nGroups: %i  nScenarios: %i  flex: %.2f  bed_cap_factor: %.2f  primal: %.1f  dual: %.1f MIPgap: %.3f runtime: %.1f " %(nGroups,nScenarios,flex,beta, results["obj"], results["best_bound"], results["MIPGap"],results["runtime"]) )
#results, input  =   run_model_mip_fixed_manual(input, time_limit, print_optimizer = True)
results         =   run_model_mip_fixed(input,results, time_limit, print_optimizer = True, create_model_and_warmstart_file=False,MIPgap_limit=False,MIPgap_value=0.01) 
print("nGroups: %i  nScenarios: %i  flex: %.2f  bed_cap_factor: %.2f  primal: %.1f  dual: %.1f MIPgap: %.3f runtime: %.1f " %(nGroups,nScenarios,flex,beta, results["obj"], results["best_bound"], results["MIPGap"],results["runtime"]) )
#results, input  =   run_model_cutting_stock(input, flex, time_limit, print_optimizer = True)

"""results         =   categorize_slots(input, results)
print_MSS(input, results)
print_expected_minutes(input,results)
print_expected_bed_util_percent(input,results)
print_expected_que(input,results)
#initiate_excel_book('results_bed_ward_tuning3.xlsx',input)
#write_to_excel_model('results_bed_ward_tuning3.xlsx',input,results)
print("nGroups: %i  nScenarios: %i  flex: %.2f  bed_cap_factor: %.2f  primal: %.1f  dual: %.1f MIPgap: %.3f runtime: %.1f " %(nGroups,nScenarios,flex,beta, results["obj"], results["best_bound"], results["MIPGap"],results["runtime"]) )"""