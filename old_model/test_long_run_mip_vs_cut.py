from random import seed
from functions_input import *
from functions_output import *
from model_cutting_stock import *
from model_mip import *


nGroups         = 9
nScenarios      = 250
seed            = 1
flex            = [0, 0.05, 0.15, 0.20, 0.25, 0.30, 0.10]
time_limit      = 46800
beta            = 1.0

excel_output_name = 'MIP_vs_CS_long_run.xlsx'


input_file_name =   choose_correct_input_file(nGroups)
input           =   read_input(input_file_name)
    
input           =   change_ward_capacity(input, "MC",60*beta,49*beta)
input           =   change_ward_capacity(input, "IC",11*beta,6*beta)  

input           =   generate_scenarios(input, nScenarios, seed)
initiate_excel_book(excel_output_name,input)

for f in flex:
    print('MIP MODEL BEGIN RUN:')
    results, input  =   run_model_mip(input, f, time_limit, expected_value_solution = False, print_optimizer = True)
    write_to_excel_model(excel_output_name,input,results)
    print('MIP model results:')
    print("nGroups: %i  nScenarios: %i  flex: %.2f  bed_cap_factor: %.2f  primal: %.1f  dual: %.1f MIPgap: %.3f runtime: %.1f " %(nGroups,nScenarios,f,beta, results["obj"], results["best_bound"], results["MIPGap"],results["runtime"]) )
    
    print('CS MODEL BEGIN RUN:')
    results, input  =   run_model_cutting_stock(input, f, time_limit, print_optimizer = True)
    write_to_excel_model(excel_output_name,input,results)
    print('CS model results:')
    print("nGroups: %i  nScenarios: %i  flex: %.2f  bed_cap_factor: %.2f  primal: %.1f  dual: %.1f MIPgap: %.3f runtime: %.1f " %(nGroups,nScenarios,f,beta, results["obj"], results["best_bound"], results["MIPGap"],results["runtime"]) )
