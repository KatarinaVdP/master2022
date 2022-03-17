import pandas as pd
import math
import itertools
import numpy as np
from input_functions import *

# Lager en dictionary med spesialiteter som key og en liste med tilhørende surgery durations (ink cleaning time) som value
def durations_per_specialty(input):
    groups = input["G"]
    cleaning_time = input["TC"]
    duration = input["L"]
    durations_per_specialty = {}
    durations_per_specialty[groups[0][0:2]] = [duration[0] + cleaning_time]
    for i in range(1, len(groups)):                      
        if groups[i][0:2] != groups[i-1][0:2]:
            durations_per_specialty[groups[i][0:2]] = [duration[i] + cleaning_time]
        else:
            durations_per_specialty[groups[i][0:2]].append(duration[i] + cleaning_time)
    return durations_per_specialty

# Regner ut maks antall operasjoner som kan gjennomføres i en slot ila en dag, både for vanlig og extended slot

def max_operations_per_specialty(input):
    slot_time = input["H"][0]
    max_operations_per_specialty = []
    for group in durations_per_specialty(input):
        max_operations_per_specialty.append(math.floor(slot_time/min(durations_per_specialty(input)[group])))
    return max_operations_per_specialty
    
def max_operations_per_specialty_extended(input):
    slot_time_extended = input["H"][0] + input["E"]
    max_operations_per_specialty_extended = []
    for group in durations_per_specialty(input):
        max_operations_per_specialty_extended.append(math.floor(slot_time_extended/min(durations_per_specialty(input)[group])))
    return max_operations_per_specialty_extended

# Lager en dict med oversikt over alle mulige operasjonskombinasjoner gitt ved operasjonslengde ila en dag, per spesialitet
    
def combinations_per_group(input):
    slot_time = input["H"][0]
    combinations_per_group = {}
    j = 0
    for specialty, durations in durations_per_specialty(input).items():
        combinations_per_group[specialty] = [duration for i in range(1, max_operations_per_specialty(input)[j]+1)
            for duration in itertools.combinations_with_replacement(durations, i)
            if sum(duration) <= slot_time]
        j += 1    
    return combinations_per_group

def combinations_per_group_extended(input):
    slot_time = input["H"][0]
    slot_time_extended = input["H"][0] + input["E"]
    combinations_per_group_extended = {}
    j = 0
    for specialty, durations in durations_per_specialty(input).items():
        combinations_per_group_extended[specialty] = [duration for i in range(1, max_operations_per_specialty_extended(input)[j]+1)
            for duration in itertools.combinations_with_replacement(durations, i)
            if sum(duration) > slot_time and sum(duration) <= slot_time_extended]
        j += 1    
    return combinations_per_group_extended
    
# Lager en dict med oversikt over patterns, per spesialitet
# Vanlig slot

def patterns_per_specialty(input):
    cleaning_time = input["TC"]
    patterns_per_specialty = {}
    for specialty, combinations in combinations_per_group(input).items():
        patterns_per_specialty[specialty] = []
        for i, combination in enumerate(combinations):
            patterns_per_specialty[specialty].append({})
            for duration in durations_per_specialty(input)[specialty]:
                patterns_per_specialty[specialty][i][duration - cleaning_time] = 0
                
    for specialty, patterns in patterns_per_specialty.items():
        for i in range(len(patterns)):
            for duration, numbers in patterns[i].items():
                for specialty2 in combinations_per_group(input).values():
                    for j in range(len(specialty2)):
                        for duration2 in specialty2[j]:
                            if i == j and duration == duration2 - cleaning_time:
                                patterns[i][duration] += 1  
                                
    return patterns_per_specialty
                                
def patterns_non_extended(input):
    groups = input["G"]
    list_patterns = []
    for combinations in combinations_per_group(input).values():
        for i, combination in enumerate(combinations):
            list_patterns.append([0 for _ in range(len(groups))])
            
    list_pattern = 0
    start_group = 0
    for patterns in patterns_per_specialty(input).values():
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
def patterns_per_specialty_extended(input):
    cleaning_time = input["TC"]
    
    patterns_per_specialty_extended = {}        
    for specialty, combinations in combinations_per_group_extended(input).items():
        patterns_per_specialty_extended[specialty] = []
        for i, combination in enumerate(combinations):
            patterns_per_specialty_extended[specialty].append({})
            for duration in durations_per_specialty(input)[specialty]:
                patterns_per_specialty_extended[specialty][i][duration - cleaning_time] = 0
                                
    for specialty, patterns in patterns_per_specialty_extended.items():
        for i in range(len(patterns)):
            for duration, numbers in patterns[i].items():
                for specialty2 in combinations_per_group_extended(input).values():
                    for j in range(len(specialty2)):
                        for duration2 in specialty2[j]:
                            if i == j and duration == duration2 - cleaning_time:
                                patterns[i][duration] += 1      
    
    return patterns_per_specialty_extended                          

def patterns_extended(input):  
    groups = input["G"]                             
    list_patterns_extended = []
    for combinations in combinations_per_group_extended(input).values():
        for i, combination in enumerate(combinations):
            list_patterns_extended.append([0 for _ in range(len(groups))])
            
    list_pattern_extended = 0
    start_group_extended = 0
    for patterns in patterns_per_specialty_extended(input).values():
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
def all_patterns(input):
    return patterns_non_extended(input) + patterns_extended(input)

# Set M^NE
def patterns_non_extended_indices(input):
    return [i for i in range(len(patterns_non_extended(input)))]

# Set M^E
def patterns_extended_indices(input):
    start = len(patterns_non_extended(input))
    return [i for i in range(start, start+len(patterns_extended(input)))]

# Set M
def all_patterns_indices(input):
    return patterns_non_extended_indices(input) + patterns_extended_indices(input)

# Set M^S_s
def patterns_specialty(input):
    matrix = [[] for _ in range(input["nSpecialties"])] # OBS! Dette er veldig hardkodet. Hente inn fra excel-fil. Er det riktig at vi her alltid har fem spesialiteter, selv om vi ikke nødvendigvis ser på alle? Tror det.
    specialty = 0
    start_index = 0
    for patterns in patterns_per_specialty(input).values():
        matrix[specialty] = [j for j in range(start_index, start_index+len(patterns))]
        specialty += 1
        start_index += len(patterns)
     
    specialty = 0
    for patterns in patterns_per_specialty_extended(input).values():
        matrix[specialty].extend([j for j in range(start_index, start_index+len(patterns))])
        specialty += 1
        start_index += len(patterns)   
    
    return matrix

def patterns_specialty_split(input):
    matrix = [[] for _ in range(input["nSpecialties"])] # OBS! Dette er veldig hardkodet. Hente inn fra excel-fil. Er det riktig at vi her alltid har fem spesialiteter, selv om vi ikke nødvendigvis ser på alle? Tror det.
    specialty = 0
    start_index = 0
    for patterns in patterns_per_specialty(input).values():
        matrix[specialty] = [j for j in range(start_index, start_index+len(patterns))]
        specialty += 1
        start_index += len(patterns)
        
    matrix2 = [[] for _ in range(input["nSpecialties"])]
    specialty = 0
    for patterns in patterns_per_specialty_extended(input).values():
        matrix2[specialty] = [j for j in range(start_index, start_index+len(patterns))]
        specialty += 1
        start_index += len(patterns)   
    
    return matrix, matrix2

# Set P_mwd
def accumulated_probabilities(input):
    P_sum = [[[0 for _ in range(20)] for _ in range(input["nWards"])] for _ in range(len(all_patterns_indices(input)))]
    A = all_patterns(input)
    for m in all_patterns_indices(input):
        for w in input["Wi"]:
            for g in input["Gi"]:
                if A[m][g] > 0:
                    for d in range(20):
                        P_sum[m][w][d] += input["P"][w][g][d] * A[m][g]
    return P_sum        

def pattern_durations(input):
    pattern_dur = [0 for _ in range(len(input["Mi"]))]
    for m in input["Mi"]:
        for g in input["Gi"]:
            pattern_dur[m] += input["A"][m][g]*input["L"][g]
    return pattern_dur

def generate_pattern_data(input):
    input["Psum"] = accumulated_probabilities(input)
    input["Mi"] = all_patterns_indices(input)
    input["Mnxi"] = patterns_non_extended_indices(input)
    input["Mxi"] = patterns_extended_indices(input)
    input["MSi"] = patterns_specialty(input)
    input["A"] = all_patterns(input)
    input["MSnxi"], input["MSxi"] = patterns_specialty_split(input)
    input["pattern_dur"] = pattern_durations(input)
    return input