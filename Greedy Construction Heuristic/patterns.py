import pandas as pd
import math

# Denne funksjonen burde importeres fra old_model_gurobi.py, men får det ikke til
def read_list(sheet, name,integerVal=False):
    set =  sheet[name].values
    list = []
    for value in set:
        if not str(value) == "nan":
            if integerVal:
                list.append(int(value))
            else:
                list.append(value)
    return list

parameters  =   pd.read_excel("model_input_global.xlsx", sheet_name='Parameters')
duration  =   read_list(parameters, "Surgery Duration")
groups = read_list(parameters, "Surgery Groups")

durations_per_specialty = {}
durations_per_specialty[groups[0][0:2]] = [duration[0]]
for i in range(1, len(groups)):                             #operere med Gi slik som i old model? altså tilhørende indexset til G som er 0 indexert
    if groups[i][0:2] != groups[i-1][0:2]:
        durations_per_specialty[groups[i][0:2]] = [duration[i]]
    else:
        durations_per_specialty[groups[i][0:2]].append(duration[i])

slot_time = 450 #dobbeltsjekk               #burde importere H[0] fra excel
slot_time_extended = 540 #dobbeltsjekk      # burde importeres som H[0] + E fra excel

max_operations_per_specialty = []
max_operations_per_specialty_extended = []
for group in durations_per_specialty:
    max_operations_per_specialty.append(math.floor(slot_time/min(durations_per_specialty[group])))
    max_operations_per_specialty_extended.append(math.floor(slot_time_extended/min(durations_per_specialty[group])))
    
patterns = []
patterns_extended = []







