from functions_input import *
from functions_output import *
from model_cutting_stock import *
from run_second_stage_pattern import *
from run_second_stage_mip import *
from model_mip import *
import random

def test_run(temp0:float,alph:float,i:int,temp1:float):
    obj             =   str(temp0)+ " " + str(alph)+ " " + str(i)+ " " + str(temp1) + " obj" + str(random. randint(0,100))
    time_obj        =   random. randint(0,100)
    obj_best        =   str(temp0)+ " " + str(alph)+ " " + str(i)+ " " + str(temp1) + " obj best" + str(random. randint(0,100))
    time_obj_best   =   random. randint(0,100)
    return obj,time_obj,obj_best,time_obj_best
    
def write_to_excel_parameter_tuning(excel_file_name: str, num_runs: int, initial_temp: int, alpha: float, i_max: int, min_temp: float, objectives: list, time_objectives: list, best_objectives: list, time_best_objectives: list):
    try:
        wb = load_workbook(excel_file_name)
        ws = wb.worksheets[0]
    except FileNotFoundError:
        wb  = Workbook()
        ws = wb.create_sheet("parameter_tuning",0)
        wb.save(excel_file_name)
        ws = wb.worksheets[0]
        header_row=[]
        header_row.append("#runs")
        header_row.append("T")
        header_row.append("alpha")
        header_row.append("i_max")
        header_row.append("T_min")
        header_row.append("")
        for i in range(num_runs):
            i+=1
            header_row.append("obj_" + str(i))
        header_row.append("")
        for i in range(num_runs):
            i+=1
            header_row.append("obj_time_" + str(i))
        header_row.append("")
        for i in range(num_runs):
            i+=1
            header_row.append("best_obj_" + str(i))
        header_row.append("")
        for i in range(num_runs):
            i+=1
            header_row.append("best_obj_time_" + str(i))
        header_row.append("")
        ws.append(header_row)
        wb.save(excel_file_name) 
    
    wb.save(excel_file_name)
    ws      = wb.worksheets[0]
    new_row =[]
    new_row.append(num_runs)
    new_row.append(initial_temp)
    new_row.append(alpha)
    new_row.append(i_max)
    new_row.append(min_temp)
    new_row.append("")
    for i in range(num_runs):
        new_row.append(objectives[i])
    new_row.append("")
    for i in range(num_runs):
        new_row.append(time_objectives[i])
    new_row.append("")
    for i in range(num_runs):
        new_row.append(best_objectives[i])
    new_row.append("")
    for i in range(num_runs):
        new_row.append(time_best_objectives[i])
    new_row.append("")
    ws.append(new_row)
    wb.save(excel_file_name) 
    

num_groups                  =   9
num_scenarios               =   2
flex                        =   0.1
seed                        =   1
time_limit_EVS_and_fixed    =   10

excel_file_name             =   'input_output/parameter_tuning_heuristic_pattern.xlsx'

num_runs                    =   30
initial_temp                =   [5,10,100]
alpha                       =   [0.5, 0.75]
i_max                       =   [25,50]
end_temp                    =   [0.1,0.01,0.001]

for temp0 in initial_temp:
    for alph in alpha:
        for i in i_max:
            for temp1 in end_temp:
                objectives              =   []
                time_objectives         =   []
                best_objectives         =   []
                time_best_objectives    =   []
                for run in range(num_runs):
                    #obj, time_obj, best_obj, time_best_obj = test_run(temp0,alph,i,temp1)
                    end_results, global_best_results = run_second_stage_pattern(flex, num_groups, num_scenarios, seed,time_limit_EVS_and_fixed, temp0, alph, i, temp1)
                    #end_results, global_best_results = run_second_stage_mip(flex, num_groups, num_scenarios, seed, time_limit_EVS_and_fixed, temp0, alph, i, temp1)
                    objectives.append(end_results["obj"])
                    time_objectives.append(end_results["runtime"])
                    best_objectives.append(global_best_results["obj"])
                    time_best_objectives.append(global_best_results["runtime"])
                write_to_excel_parameter_tuning(excel_file_name,        num_runs, temp0, alph, i, temp1,       objectives, time_objectives, best_objectives, time_best_objectives)
                    