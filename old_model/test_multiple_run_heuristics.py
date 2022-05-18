from numpy import False_
from functions_input import *
from functions_output import *
from model_cutting_stock import *
from heuristic_second_stage_pattern import *
from heuristic_second_stage_mip import *
from model_mip import *
import random
import time
import pickle

def test_run(temp0:float,alph:float,i:int,temp1:float):
    obj             =   str(temp0)+ " " + str(alph)+ " " + str(i)+ " " + str(temp1) + " obj" + str(random. randint(0,100))
    time_obj        =   random. randint(0,100)
    obj_best        =   str(temp0)+ " " + str(alph)+ " " + str(i)+ " " + str(temp1) + " obj best" + str(random. randint(0,100))
    time_obj_best   =   random. randint(0,100)
    return obj,time_obj,obj_best,time_obj_best
    
def write_to_excel_heuristic_run(excel_file_name: str, num_runs:int ,run: int, initial_temp: int, alpha: float, i_max: int, min_temp: float, objective: float, time_objective: float, best_objective: float, time_best_objective: float):
    try:
        wb = load_workbook(excel_file_name)
        ws = wb.worksheets[0]
    except FileNotFoundError:
        wb  = Workbook()
        ws = wb.create_sheet("parameter_tuning",0)
        wb.save(excel_file_name)
        ws = wb.worksheets[0]
        header_row=[]
        header_row.append("num_runs")
        header_row.append("run")
        header_row.append("T")
        header_row.append("alpha")
        header_row.append("i_max")
        header_row.append("T_min")
        header_row.append("obj")
        header_row.append("obj_time_")
        header_row.append("best_obj_")
        header_row.append("best_obj_time_")
        ws.append(header_row)
        wb.save(excel_file_name) 
    
    wb.save(excel_file_name)
    ws      = wb.worksheets[0]
    new_row =[]
    new_row.append(num_runs)
    new_row.append(run)
    new_row.append(initial_temp)
    new_row.append(alpha)
    new_row.append(i_max)
    new_row.append(min_temp)
    new_row.append(objective)
    new_row.append(time_objective)
    new_row.append(best_objective)
    new_row.append(time_best_objective)
    ws.append(new_row)
    wb.save(excel_file_name) 

def write_string_to_excel_heuristic_run(excel_file_name, string, sheet_number=0):
    wb = load_workbook(excel_file_name)
    ws = wb.worksheets[sheet_number]
    ws.append(string)
    wb.save(excel_file_name)

second_stage_pattern        =   True
fast_run                    =   True

check_end_solution          =   False
check_best_solution         =   True
check_beginning_solution    =   False

GAP_limit                   =   True
GAP_limit_value             =   0.01

save_best_solution_as_pickle=   True
run_best_solution           =   True

num_groups                  =   9
num_scenarios               =   3
flex                        =   0.1
seed                        =   1

time_limit_EVS              =   60
time_limit_first_fix        =   600    # only second_stage_mip
time_limit_iteration        =   20     # only second_stage_mip
time_limit_last_fix         =   600    # only second_stage_mpattern

num_runs                    =   1
beta                        =   1.0
flexibilities               =   [0.0,0.05,0.1,0.15,0.20,0.25,0.3]

if second_stage_pattern:
    excel_file_name_summary     =   'input_output/multiple_run_test_summary_PATTERN_TEST.xlsx'
    output_file_name            =   'input_output/multiple_run_PATTERN_TEST.xlsx'
else:
    excel_file_name_summary     =   'input_output/multiple_run_test_summary_MIP_TEST.xlsx'
    output_file_name            =   'input_output/multiple_run_MIP_TEST.xlsx'


if second_stage_pattern:
    initial_temp                =   1000
    alpha                       =   0.9
    i_max                       =   50
    end_temp                    =   0.01
    
else:
    initial_temp                =   1000
    alpha                       =   0.9
    i_max                       =   25
    end_temp                    =   0.01
    

"""initial_temp                =   10
alpha                       =   0.3
i_max                       =   2
end_temp                    =   0.1"""

if run_best_solution:
    run = 2
    solution_string = 'input_output/best_runs_heuristic/best_solution_' + str(num_groups) + '_' + str(num_scenarios) +  '_' + str(seed) + '_' + str(int(flex*10)) + '_' + str(num_groups) + '_run' + str(run)+ '.pkl'
    if os.path.exists("model_solution.pkl"):
        with open("model_solution.pkl","rb") as f:
            saved_values        =   pickle.load(f)
            input               =   saved_values["input"]
            global_best_results =   saved_values["results"]
            global_best_results =   run_model_mip_fixed(input,global_best_results,time_limit_last_fix,print_optimizer = True,create_model_and_warmstart_file=False)
            string_to_write     =   ['Best_sol_FROM_PICKE_preformance:  obj: ' + str(global_best_results['obj']) + 'best bound: '+str(global_best_results['best_bound']) + 'MIPgap: '+str(global_best_results['MIPGap'])+'runtime : ' + str(global_best_results['runtime'])]
            print(string_to_write)
    else:
        print('no solution found')  
else:
    for flex in flexibilities:
        for run in range(1,num_runs+1):
            #obj, time_obj, best_obj, time_best_obj = test_run(temp0,alph,i,temp1)
            start_time= time.time()
            print("init_temp: %.2f, alpha: %.2f,  iter: %i, end_temp: %.3f, run nr: %i" %(initial_temp, alpha, i_max, end_temp, run))
            if second_stage_pattern:
                if fast_run:
                    end_results, global_best_results, input =   run_second_stage_pattern_param_tuning(beta,flex, num_groups, num_scenarios, seed, time_limit_EVS, initial_temp, alpha, i_max, end_temp,check_start_solution=check_beginning_solution)
                    if check_end_solution:
                        end_results         =   run_model_mip_fixed(input,end_results,time_limit_last_fix,print_optimizer = False,create_model_and_warmstart_file=False)
                        string_to_write     =   ['End_sol_preformance:  obj: ' + str(end_results['obj']) + 'best bound: '+str(end_results['best_bound']) + 'MIPgap: '+str(end_results['MIPGap'])+'runtime : ' + str(end_results['runtime'])]
                        print(string_to_write)
                    if check_best_solution:
                        global_best_results =   run_model_mip_fixed(input,global_best_results,time_limit_last_fix,print_optimizer = False,create_model_and_warmstart_file=False)
                        string_to_write     =   ['Best_sol_preformance:  obj: ' + str(global_best_results['obj']) + 'best bound: '+str(global_best_results['best_bound']) + 'MIPgap: '+str(global_best_results['MIPGap'])+'runtime : ' + str(global_best_results['runtime'])]
                        print(string_to_write)
                else:                                                                
                    end_results, global_best_results, input =   run_second_stage_pattern(beta,output_file_name,flex, num_groups, num_scenarios, seed, time_limit_EVS, initial_temp, alpha, i_max, end_temp,check_start_solution=check_beginning_solution)
                    if check_end_solution:
                        end_results         =   run_model_mip_fixed(input,end_results,time_limit_last_fix,print_optimizer = False,create_model_and_warmstart_file=False)
                        string_to_write     =   ['End_sol_preformance:  obj: ' + str(end_results['obj']) + 'best bound: '+str(end_results['best_bound']) + 'MIPgap: '+str(end_results['MIPGap'])+'runtime : ' + str(end_results['runtime'])]
                        print(string_to_write)
                        write_string_to_excel(output_file_name,input,string_to_write,sheet_number=1)
                    if check_best_solution:
                        global_best_results =   run_model_mip_fixed(input,global_best_results,time_limit_last_fix,print_optimizer = False,create_model_and_warmstart_file=False)
                        string_to_write     =   ['Best_sol_preformance:  obj: ' + str(global_best_results['obj']) + 'best bound: '+str(global_best_results['best_bound']) + 'MIPgap: '+str(global_best_results['MIPGap'])+'runtime : ' + str(global_best_results['runtime'])]
                        print(string_to_write)
                        write_string_to_excel(output_file_name,input,string_to_write,sheet_number=1)
                
                if save_best_solution_as_pickle:
                    solution_string = 'input_output/best_runs_heuristic/best_solution_' + str(num_groups) + '_' + str(num_scenarios) +  '_' + str(seed) + '_' + str(int(flex*10)) + '_' + str(num_groups) + '_run' + str(run)+ '.pkl'
                    saved_values            =   {}
                    saved_values["input"]   =   input
                    saved_values["results"] =   global_best_results
                    with open(solution_string,"wb") as f:
                        pickle.dump(saved_values,f)
            else:
                end_results, global_best_results, input  =   run_second_stage_mip(beta,output_file_name,flex, num_groups, num_scenarios, seed, time_limit_EVS, time_limit_first_fix, time_limit_iteration, initial_temp, alpha, i_max, end_temp, MIPgap_limit=GAP_limit,MIPgap_value=GAP_limit_value)
                    #--- Saving solution in pickle ---
                pickle_string = 'best_solution_run_'
                
            current_time=time.time()-start_time
            print('Total time of this run:')
            print(current_time)
            
            #---WRITING EXTRA INFO TO EXCEL ABOUT FIXING LAST SOLUTIONS  and INPUT----
            write_to_excel_heuristic_run(excel_file_name_summary,num_runs,run, initial_temp, alpha, i_max, end_temp,       end_results["obj"], end_results["runtime"], global_best_results["obj"],global_best_results["runtime"])
        input_string= ['nGroups: ' + str(num_groups) +   '   nScenarios: ' + str(num_scenarios) + '   seed: ' + str(seed)+  '   flex: ' + str(flex) + '   beta: ' + str(beta) + '  time_limit_EVS : ' + str(time_limit_EVS) +   '   time_limit_first_fix: '+ str(time_limit_first_fix) + '   time_limit_iteration: '  +str(time_limit_iteration)+  '   time_limit_last_fix: ' + str(time_limit_last_fix)]
        write_string_to_excel_heuristic_run(excel_file_name_summary, input_string, sheet_number=0)       