
import pandas as pd
import math
import itertools
import numpy as np
from input_functions import read_list

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
parameters  =   pd.read_excel("Cutting Stock Model/Input/model_input_9groups_2or3spec.xlsx", sheet_name='Parameters')

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
          if sum(duration) > slot_time and sum(duration) <= slot_time_extended]
    j += 1

# Lager en dict med oversikt over patterns, per spesialitet
# Vanlig slot

patterns_per_specialty = {}
for specialty, combinations in combinations_per_group.items():
    patterns_per_specialty[specialty] = []
    for i, combination in enumerate(combinations):
        patterns_per_specialty[specialty].append({})
        for duration in durations_per_specialty[specialty]:
            patterns_per_specialty[specialty][i][duration - cleaning_time] = 0
            
for specialty, patterns in patterns_per_specialty.items():
    for i in range(len(patterns)):
        for duration, numbers in patterns[i].items():
            for specialty2 in combinations_per_group.values():
                for j in range(len(specialty2)):
                    for duration2 in specialty2[j]:
                        if i == j and duration == duration2 - cleaning_time:
                            patterns[i][duration] += 1  
                                
def patterns_non_extended():
    list_patterns = []
    for combinations in combinations_per_group.values():
        for i, combination in enumerate(combinations):
            list_patterns.append([0 for _ in range(len(groups))])
            
    list_pattern = 0
    start_group = 0
    for patterns in patterns_per_specialty.values():
        if len(patterns) > 0:
            for pattern in patterns:
                group = start_group
                for number in pattern.values():
                    list_patterns[list_pattern][group] = number
                    group += 1
                list_pattern += 1
        start_group += len(patterns[0])
        
    return list_patterns

# Extended   
                        
patterns_per_specialty_extended = {}        
for specialty, combinations in combinations_per_group_extended.items():
    patterns_per_specialty_extended[specialty] = []
    for i, combination in enumerate(combinations):
        patterns_per_specialty_extended[specialty].append({})
        for duration in durations_per_specialty[specialty]:
            patterns_per_specialty_extended[specialty][i][duration - cleaning_time] = 0
                            
for specialty, patterns in patterns_per_specialty_extended.items():
    for i in range(len(patterns)):
        for duration, numbers in patterns[i].items():
            for specialty2 in combinations_per_group_extended.values():
                for j in range(len(specialty2)):
                    for duration2 in specialty2[j]:
                        if i == j and duration == duration2 - cleaning_time:
                            patterns[i][duration] += 1      
                             
def patterns_extended():                               
    list_patterns_extended = []
    for combinations in combinations_per_group_extended.values():
        for i, combination in enumerate(combinations):
            list_patterns_extended.append([0 for _ in range(len(groups))])
            
    list_pattern_extended = 0
    start_group_extended = 0
    for patterns in patterns_per_specialty_extended.values():
        if len(patterns) > 0:
            for pattern in patterns:
                group = start_group_extended
                for number in pattern.values():
                    list_patterns_extended[list_pattern_extended][group] = number
                    group += 1
                list_pattern_extended += 1
            start_group_extended += len(patterns[0])
        
    return list_patterns_extended

# Parameter A_mg
def all_patterns():
    return patterns_non_extended() + patterns_extended()

# Set M^NE
def patterns_non_extended_indices():
    return [i for i in range(len(patterns_non_extended()))]

# Set M^E
def patterns_extended_indices():
    start = len(patterns_non_extended())
    return [i for i in range(start, start+len(patterns_extended()))]

# Set M
def all_patterns_indices():
    return patterns_non_extended_indices() + patterns_extended_indices()

# Set M^S_s
def patterns_specialty():
    matrix = [[] for _ in range(5)] # OBS! Dette er veldig hardkodet. Hente inn fra excel-fil. Er det riktig at vi her alltid har fem spesialiteter, selv om vi ikke nødvendigvis ser på alle? Tror det.
    specialty = 0
    start_index = 0
    for patterns in patterns_per_specialty.values():
        matrix[specialty] = [j for j in range(start_index, start_index+len(patterns))]
        specialty += 1
        start_index += len(patterns)
     
    specialty = 0
    for patterns in patterns_per_specialty_extended.values():
        matrix[specialty].extend([j for j in range(start_index, start_index+len(patterns))])
        specialty += 1
        start_index += len(patterns)   
    
    return(matrix)

# Set P_mwd
def accumulated_probabilities():
    #instantiate Pmwd
    cum_P = [[[0 for _ in range(28)] for _ in range(2)] for _ in range(len(all_patterns_indices()))]
    for m in Mi:
        for w in Wi:
            for g in Gi:
                if A[m][g] > 0:
                    cum_P[m][w] = np.add(cum_P[m][w], A[m][g]*P[w][g])
    
    matrix = [[[0 for i in range(28)]]]
    return cum_P        
    

print("\nPatterns per group:\n")
print(patterns_non_extended())
print("\nPatterns per group, extended:\n")
print(patterns_extended())
print(patterns_non_extended_indices())
print(patterns_extended_indices())
print(all_patterns_indices())
print(patterns_per_specialty)
print(patterns_per_specialty_extended)
print(patterns_specialty())