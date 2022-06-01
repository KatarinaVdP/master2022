from functions_output import *
from heuristic_second_stage_pattern import *
from model_mip import *

################################################################
#------Settings------#
fast_run                    =   True    # True is three times as fast, but no data is saved - only printed to terminal
check_best_solution         =   True    # True = SA-GCH, False = SA-GCH-MIP
GAP_limit                   =   False   # False = Cutoff at default value for gurobi: 1e-4, True = set it your self
GAP_limit_value             =   0.01    # If GAP_limit = True: set cutoff value
time_limit_EVS              =   60      # 
time_limit_last_fix         =   600     # If check_best_solution = True, give time cutoff value
output_file_name            =   'input_output/SA_GCH_MIP_run.xlsx'

#------Problem Instances------#
num_groups                  =   9       #Number of surgery groups to from clustering algorithm
flex                        =   0.1     #Maximum percentage flexible slots in a MSS
num_scenarios               =   250     #Size of scenario tree
seed                        =   1       #Seed to generate num_scenarios from
beta                        =   1.0     #Bed ward capacity factor.

#------SA-Parameters------#
initial_temp                =   1000
alpha                       =   0.9
i_max                       =   50
end_temp                    =   0.01
################################################################


if fast_run:
    end_results, global_best_results, input =   run_second_stage_pattern_param_tuning(beta,flex, num_groups, num_scenarios, seed, time_limit_EVS, initial_temp, alpha, i_max, end_temp)
    if check_best_solution:
        print('----------------------------------')
        print('Solving the second stage for best obtained solution with MIP')
        print('----------------------------------')
        global_best_results =   run_model_mip_fixed(input,global_best_results,time_limit_last_fix,print_optimizer = True,create_model_and_warmstart_file=False)
        string_to_write     =   ['Best_sol_preformance:  obj: ' + str(global_best_results['obj']) + 'best bound: '+str(global_best_results['best_bound']) + 'MIPgap: '+str(global_best_results['MIPGap'])+'runtime : ' + str(global_best_results['runtime'])]
        print(string_to_write)
else:                                                                
    end_results, global_best_results, input =   run_second_stage_pattern(beta,output_file_name,flex, num_groups, num_scenarios, seed, time_limit_EVS, initial_temp, alpha, i_max, end_temp)
    if check_best_solution:
        print('----------------------------------')
        print('Solving the second stage for best obtained solution with MIP')
        print('----------------------------------')
        global_best_results =   run_model_mip_fixed(input,global_best_results,time_limit_last_fix,print_optimizer = True,create_model_and_warmstart_file=False)
        string_to_write     =   ['Best_sol_preformance:  obj: ' + str(global_best_results['obj']) + 'best bound: '+str(global_best_results['best_bound']) + 'MIPgap: '+str(global_best_results['MIPGap'])+'runtime : ' + str(global_best_results['runtime'])]
        print(string_to_write)
        write_string_to_excel(output_file_name,input,string_to_write,sheet_number=1)

global_best_results         =   categorize_slots(input, global_best_results)
print_MSS(input, global_best_results)
print_expected_minutes(input,global_best_results)
print_expected_bed_util_percent(input,global_best_results)
print_expected_que(input,global_best_results)