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

print("Durations per specialty:")
print(durations_per_specialty)
print()

# Data om lengde på vanlig slot og extended slot. Bør hentes fra Excel-fil
slot_time = 450                 # Importere H[0] fra excel
slot_time_extended = 540        # Importere som H[0] + E fra Excel


# Regner ut maks antall operasjoner som kan gjennomføres i en slot ila en dag, både for vanlig og extended slot
max_operations_per_specialty = []
max_operations_per_specialty_extended = []
for group in durations_per_specialty:
    max_operations_per_specialty.append(math.floor(slot_time/min(durations_per_specialty[group])))
    max_operations_per_specialty_extended.append(math.floor(slot_time_extended/min(durations_per_specialty[group])))
      
combinations_per_group = {}
for specialty, durations in durations_per_specialty.items():
    combinations_per_group[specialty] = [duration for i in range(1, max_operations_per_specialty[0]+1)
          for duration in itertools.combinations_with_replacement(durations, i)
          if sum(duration) <= slot_time]

print("Combinations per group:")
print(combinations_per_group)

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

print(    )
print("Patterns per group:")
print(patterns_per_group)
        

# Koden under gjør det samme som "patterns = ..."
"""patterns2=[]
for i in range(1, max_operations_per_specialty[0]+1):
    for duration in itertools.combinations_with_replacement(durations, i):
        if sum(duration) <= slot_time:
            patterns2.append(duration)"""







