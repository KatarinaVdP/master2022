
import pandas as pd
import math
import itertools

# Denne funksjonen burde importeres fra old_model_gurobi.py, men får det ikke til. Har brukt en del tid på det, så kanskje best å la det ligge
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

duration  =   read_list(parameters, "Surgery Duration")                     # Operasjonslengde per gruppe
groups = read_list(parameters, "Surgery Groups")                            # Navn på alle operasjonsgrupper
cleaning_time = read_list(parameters, "Cleaning Time")[0]                   # Vasketid
slot_time = read_list(parameters, "Opening Hours")[0]                       # Antall minutter i vanlig slot
slot_time_extended = slot_time + read_list(parameters, "Extended Time")[0]  # Antall minutter i extended slot

# Lager en dictionary med spesialiteter som key og en liste med tilhørende surgery durations (ink cleaning time) som value
durations_per_specialty = {}
durations_per_specialty[groups[0][0:2]] = [duration[0] + cleaning_time]
for i in range(1, len(groups)):                      
    if groups[i][0:2] != groups[i-1][0:2]:
        durations_per_specialty[groups[i][0:2]] = [duration[i] + cleaning_time]
    else:
        durations_per_specialty[groups[i][0:2]].append(duration[i] + cleaning_time)

# Regner ut maks antall operasjoner som kan gjennomføres i en slot ila en dag, både for vanlig og extended slot
max_operations_per_specialty = []
max_operations_per_specialty_extended = []
for group in durations_per_specialty:
    max_operations_per_specialty.append(math.floor(slot_time/min(durations_per_specialty[group])))
    max_operations_per_specialty_extended.append(math.floor(slot_time_extended/min(durations_per_specialty[group])))
      
# Lager en dict med oversikt over alle mulige operasjonskombinasjoner gitt ved operasjonslengde ila en dag, per spesialitet
combinations_per_group = {}
combinations_per_group_extended = {}
j = 0
for specialty, durations in durations_per_specialty.items():
    combinations_per_group[specialty] = [duration for i in range(1, max_operations_per_specialty[j]+1)
          for duration in itertools.combinations_with_replacement(durations, i)
          if sum(duration) <= slot_time]
    combinations_per_group_extended[specialty] = [duration for i in range(1, max_operations_per_specialty_extended[j]+1)
          for duration in itertools.combinations_with_replacement(durations, i)
          if sum(duration) <= slot_time_extended]
    j += 1

# Lager en dict med oversikt over patterns, per spesialitet
# Vanlig slot
patterns_per_group = {}
for specialty, combinations in combinations_per_group.items():
    patterns_per_group[specialty] = []
    for i, combination in enumerate(combinations):
        patterns_per_group[specialty].append({})
        for duration in durations_per_specialty[specialty]:
            patterns_per_group[specialty][i][duration - cleaning_time] = 0
            
for specialty, patterns in patterns_per_group.items():
    for i in range(len(patterns)):
        for duration, numbers in patterns[i].items():
            for specialty2 in combinations_per_group.values():
                for j in range(len(specialty2)):
                    for duration2 in specialty2[j]:
                        if i == j and duration == duration2 - cleaning_time:
                            patterns[i][duration] += 1  
# Extended                           
patterns_per_group_extended = {}        
for specialty, combinations in combinations_per_group_extended.items():
    patterns_per_group_extended[specialty] = []
    for i, combination in enumerate(combinations):
        patterns_per_group_extended[specialty].append({})
        for duration in durations_per_specialty[specialty]:
            patterns_per_group_extended[specialty][i][duration - cleaning_time] = 0
                            
for specialty, patterns in patterns_per_group_extended.items():
    for i in range(len(patterns)):
        for duration, numbers in patterns[i].items():
            for specialty2 in combinations_per_group_extended.values():
                for j in range(len(specialty2)):
                    for duration2 in specialty2[j]:
                        if i == j and duration == duration2 - cleaning_time:
                            patterns[i][duration] += 1       

print("\nPatterns per group:\n")
print(patterns_per_group)
print("\nPatterns per group, extended:\n")
print(patterns_per_group_extended)