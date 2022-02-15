import pandas as pd
import math
import itertools

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

# Henter ut data 
parameters  =   pd.read_excel("model_input_global.xlsx", sheet_name='Parameters')
duration  =   read_list(parameters, "Surgery Duration")
groups = read_list(parameters, "Surgery Groups")
cleaning_time = 30 # Hentes fra Excel

# Lager en dictionary med spesialiteter som key og en liste med tilhørende surgery durations som value. Surgery durations inkluderer cleaning time
durations_per_specialty = {}
durations_per_specialty[groups[0][0:2]] = [duration[0] + cleaning_time]
for i in range(1, len(groups)):                             #operere med Gi slik som i old model? altså tilhørende indexset til G som er 0 indexert
    if groups[i][0:2] != groups[i-1][0:2]:
        durations_per_specialty[groups[i][0:2]] = [duration[i] + cleaning_time]
    else:
        durations_per_specialty[groups[i][0:2]].append(duration[i] + cleaning_time)

# Data om lengde på vanlig slot og extended slot. Bør hentes fra Excel-fil
slot_time = 450                 # Importere H[0] fra excel
slot_time_extended = 540        # Importere som H[0] + E fra Excel


# Regner ut maks antall operasjoner som kan gjennomføres i en slot ila en dag, både for vanlig og extended slot
max_operations_per_specialty = []
max_operations_per_specialty_extended = []
for group in durations_per_specialty:
    max_operations_per_specialty.append(math.floor(slot_time/min(durations_per_specialty[group])))
    max_operations_per_specialty_extended.append(math.floor(slot_time_extended/min(durations_per_specialty[group])))
      
all_combinations = {}
for specialty, durations in durations_per_specialty.items():
    all_combinations[specialty] = [duration for i in range(1, max_operations_per_specialty[0]+1)
          for duration in itertools.combinations_with_replacement(durations, i)
          if sum(duration) <= slot_time]

print("All combinations:")
print(all_combinations)

number_per_group = {}
for specialty, combinations in all_combinations.items():
    number_per_group[specialty] = {}
    pattern_id = 1
    for duration in durations_per_specialty[specialty]:
        print("Duration:")
        print(duration)
        number_per_group[specialty][pattern_id] = {}
        number_per_group[specialty][pattern_id][duration] = 0
        #print(number_per_group)
        pattern_id += 1
"""    for pattern in combinations:
        for operation in pattern:
            number_per_group[specialty][pattern_id][operation - cleaning_time] += 1"""
        

print(    )
print("Number per group:")
print(number_per_group)
        

# Koden under gjør det samme som "patterns = ..."
"""patterns2=[]
for i in range(1, max_operations_per_specialty[0]+1):
    for duration in itertools.combinations_with_replacement(durations, i):
        if sum(duration) <= slot_time:
            patterns2.append(duration)"""







