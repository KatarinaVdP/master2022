
# Helping functions
# Obtaining appropriate ward resource object
import math
import numpy as np

np.random.seed(0)

def get_resource(resource, clinic):
    if resource == 'KGAS1':
        return clinic.KGAS1
    if resource == 'KGAS2':
        return clinic.KGAS2
    if resource == 'KGASA':
        return clinic.KGASA
    if resource == 'KURS':
        return clinic.KURS
    if resource == 'KENS':
        return clinic.KENS
    if resource == 'KKAS':
        return clinic.KKAS
    if resource == 'ICU':
        return clinic.ICU
    if resource == 'TOV':
        return clinic.TOV
    if resource == 'GA1':
        return clinic.GA1
    if resource == 'GA2':
        return clinic.GA2
    if resource == 'GA3':
        return clinic.GA3
    if resource == 'GA4':
        return clinic.GA4
    if resource == 'GA5':
        return clinic.GA5
    if resource == 'GA6':
        return clinic.GA6
    if resource == 'GA7':
        return clinic.GA7
    if resource == 'emerg_OR':
        return clinic.emerg_OR
    if resource == 'red_emerg_OR':
        return clinic.red_emerg_OR
    if resource == 'unavailable_OR':
        return clinic.unavailable_OR


#Converts minutes to [day, hour, min]
def min_to_time(minutes):
    day = math.floor(minutes/(60 * 24))
    rest = minutes - (day*60*24)
    hour = math.floor(rest/60)
    rest = rest - (hour*60)
    minutes = math.floor(rest)
    return [day, hour, minutes]


def time_to_min(time):
    minutes = time[0]*60*24
    minutes += time[1]*60
    minutes += time[2]
    return minutes

def set_dummy_group(patient_group, elec_info, patient_group_info_list):
    
    dum_groups = []
    dummy_group = None
    
    dummy_weights_list = elec_info['Dummy weight'].values
    dummy_weights = []
    
    if patient_group[3:] == 'dum':
        dummy_group = patient_group
        #print()
        #print('Patient is dummy, patient group is ', str(dummy_group))
        for i in range(len(patient_group_info_list)):
            if patient_group_info_list[i][:2] == patient_group[:2] and patient_group_info_list[i][3:] != 'dum':
                dum_groups.append(patient_group_info_list[i])
                dummy_weights.append(dummy_weights_list[i])
                #print('Real patient_group appended in dum_groups: %s, weight: %s ' %(patient_group_info_list[i], dummy_weights_list[i]))
        
        
        probs = [None]*len(dum_groups)
        
        probs[0] = dummy_weights[0]
        #print('Probability first group', probs[0])
        
        if len(dum_groups) > 1:
            for i in range(len(dum_groups)-1):
                probs[i+1] = probs[i] + dummy_weights[i+1]
                #print('Probability next is group:', probs[i+1])
        
        x = np.random.uniform(0,1)
        #print('X is', x)
        received_group = False
        
        i = 0
        while not received_group:
            if x <= probs[i]:
                patient_group = dum_groups[i]
                received_group = True
                #print('Patient received group ', patient_group)
            i += 1
            
        
    return patient_group, dummy_group

def set_elec_surgery_duration(patient_group, elec_info, patient_group_info_list):
    
    exp_surgery_dur_list = elec_info['Exp surgery duration'].values
    std_surgery_dur_list = elec_info['Std surgery duration'].values
    max_surgery_dur_list = elec_info['Max surgery duration'].values
    

    
    for i in range(len(patient_group_info_list)):
        if patient_group_info_list[i] == patient_group:
            exp = exp_surgery_dur_list[i]
            std = std_surgery_dur_list[i]
            max = max_surgery_dur_list[i]
            
            surgery_duration = round(np.random.lognormal(exp, std))
            
            while surgery_duration > max:
                surgery_duration = round(np.random.lognormal(exp, std))
            
    return surgery_duration


def durSort(patient):
    return patient.med_sur_dur

def idSort(patient):
    return patient.id

def arrSort(patient):
    return time_to_min(patient.arrival_time)


def set_elec_LOS(patient_group, ward_sheet, elec_info):

    prob_LOS_day_ward = [] #List of probabilities for each day in designated ward (speciality)
    
    global prob_ward, prob_ICU, prob_TOV
    
    # Creating a list of the probabilities for each day for each patient group for each placement. 
    # Also finding the list for the probabilities for the first placement
    
    patient_group_info_list = elec_info['Patient group']
    
    for i in range(len(patient_group_info_list)):
        if patient_group_info_list[i] == patient_group:
            prob_ICU = elec_info['Prob complex'].values[i]
    
    patient_group_ward_list = ward_sheet['Patient group'].values   #Gives number of patient groups
        
    for k in range(len(patient_group_ward_list)): #Searching through list of patient groups to find the right one
    
        #Gathering probabilities for ward and kompleks
        if patient_group_ward_list[k] == patient_group:
            prob_ward = ward_sheet['J1'].values[k]
            # The rest are sent home
                    
            for j in range(20): #Setter 20 dager siden Jmax er 20 dager
                name_col = str('J' + str(j+1))
                day = ward_sheet[name_col].values[k]
                        
                prob_LOS_day_ward.append(day)
    
                
    # Finding the path of the patient
    x = np.random.uniform(0,1) #Draw a random number between 0 and 1
    
    LOS_ward = 0
    start_LOS_ward = 0 #The day the patient is admitted into the ward (starts at 0)
    LOS_ICU = 0
    LOS_TOV = 0
    
    night = 0
    
    if x <= prob_ward:
        while night < 20 and x <= prob_LOS_day_ward[night]:
            LOS_ward += 1
            night += 1
    
    else:
        pass # Patient is sent home with initialized variables
    
    if LOS_ward > 3:
        x = np.random.uniform(0,1)
        
        if x <= prob_ICU:
            LOS_ICU = np.random.choice([1,2])
            start_LOS_ward = LOS_ICU + 1
        
        else:
            LOS_TOV = np.random.choice([1,2])
            start_LOS_ward = LOS_TOV + 1
    
    else:
        pass # Patient is not admittet to IC-ward
        
    
    all_LOS = [start_LOS_ward, LOS_ward, LOS_TOV, LOS_ICU]

    
    return all_LOS



def set_emerg_LOS(patient_group, ward_sheet, emerg_info, speciality):

    prob_LOS_day_ward = [] #List of probabilities for each day in designated ward (speciality)
    
    global prob_ward, prob_ICU, prob_TOV
    
    # Creating a list of the probabilities for each day for each patient group for each placement. 
    # Also finding the list for the probabilities for the first placement
    
    prob_ICU = emerg_info[speciality].values[13]
    
    patient_group_list = ward_sheet['Patient group'].values   #Gives number of patient groups
        
    for k in range(len(patient_group_list)): #Searching through list of patient groups to find the right one
    
        #Gathering probabilities for ward and kompleks
        if patient_group_list[k] == patient_group:
            prob_ward = ward_sheet['J1'].values[k]
            # The rest are sent home
            
            for j in range(20): #Setter 20 dager siden Jmax er 20 dager
                name_col = str('J' + str(j+1))
                day = ward_sheet[name_col].values[k]
                        
                prob_LOS_day_ward.append(day)
                    
    # Finding the path of the patient
    x = np.random.uniform(0,1) #Draw a random number between 0 and 1
    
    LOS_ward = 0
    start_LOS_ward = 0 #The day the patient is admitted into the ward (starts at 0)
    LOS_ICU = 0
    LOS_TOV = 0
    
    night = 0
    
    if x <= prob_ward:
        
        while x <= prob_LOS_day_ward[night]:
            LOS_ward += 1
            night += 1
    
    else:
        pass # Patient is sent home with initialized variables
    
    if LOS_ward > 3:
        x = np.random.uniform(0,1)
        
        if x <= prob_ICU:
            LOS_ICU = np.random.choice([1,2])
            start_LOS_ward = LOS_ICU + 1
        
        else:
            LOS_TOV = np.random.choice([1,2])
            start_LOS_ward = LOS_TOV + 1
    
    else:
        pass # Patient is not admittet to IC-ward
        
    
    all_LOS = [start_LOS_ward, LOS_ward, LOS_TOV, LOS_ICU]

    
    return all_LOS



def set_time_to_reg(patient, now, emerg_info, ward_pre_reg_sheet):
    time_now = min_to_time(now)
    current_day = time_now[0]
    current_hour = time_now[1]

    params = emerg_info[patient.speciality].values

    groups = ward_pre_reg_sheet["Patient group"].values
    patient_group = "EM-"+str(patient.speciality)+"-S"
    index = None

    for i in range(len(groups)):
        if patient_group == groups[i]:
            index=i
    probs=[]
    for i in range(15):
        list =  ward_pre_reg_sheet["J"+str(i+1)].values
        probs.append(list[index])

    if index==None:
        print("MIIISTAKKKKEEEE, COULDNT FIND patient group in WardPreReg!!!!!")


    random = np.random.uniform(0, 1)
    days_to_reg = 0
    for prob in probs:
        if random < prob:
            days_to_reg += 1

    day = current_day + days_to_reg
    
    if current_hour == 23:
        day += 1
    else:pass

    hour_min = params[11]
    hour_max = params[12]
    
    if day == current_day:
        time_float = np.random.uniform(current_hour+1, hour_max)
    else:
        time_float = np.random.uniform(hour_min, hour_max)

    hour = math.floor(time_float)
    rest = time_float - hour
    minute = math.floor(rest * 60)

    reg_time = [day, hour, minute]
    patient.set_surgery_reg_time(reg_time)

    time_to_reg = time_to_min(reg_time) - now

    #print("Time to reg: ", time_to_reg)
    return time_to_reg




def set_speciality(emerg_info):
    
    limit_KGAS1 = emerg_info['KGAS1'].values[0]
    limit_KGAS2 = limit_KGAS1 + emerg_info['KGAS2'].values[0]
    limit_KGASA = limit_KGAS2 + emerg_info['KGASA'].values[0]
    limit_KURS = limit_KGASA + emerg_info['KURS'].values[0]
    limit_KENS = limit_KURS + emerg_info['KENS'].values[0]

    random = np.random.uniform(0,1)

    if random < limit_KGAS1:
        return 'KGAS1'
    elif random < limit_KGAS2:
        return 'KGAS2'
    elif random < limit_KGASA:
        return 'KGASA'
    elif random < limit_KURS:
        return 'KURS'
    elif random < limit_KENS:
        return 'KENS'
    else:
        return 'KKAS'


def KGAS1_KGAS2(emerg_info, emerg_patient):
        prob_KGAS1 = emerg_info['KGASA'].values[9]
        # Rest is KGAS2
        
        x = np.random.uniform(0,1)
        
        if x < prob_KGAS1:
            emerg_patient.set_KGAS1_or_KGAS2('KGAS1') 
        else:
            emerg_patient.set_KGAS1_or_KGAS2('KGAS2') 
    

def set_surgery(emerg_info, speciality):
    
    random = np.random.uniform(0, 1)
    prob = emerg_info[speciality].values[1]

    if random < prob:
        return 1
    else:
        return 0


def set_surgery_pri(emerg_info, speciality):
    limit_pri1 = emerg_info[speciality].values[2]
    limit_pri2 = limit_pri1 + emerg_info[speciality].values[3]  

    random = np.random.uniform(0, 1)

    if random<limit_pri1:
        return 1
    if random<limit_pri2:
        return 2
    else:
        return 3


def set_emerg_surgery_duration(emerg_info, speciality):
    
    avg = emerg_info[speciality].values[5]
    exp = emerg_info[speciality].values[6]
    std = emerg_info[speciality].values[7]
    max = emerg_info[speciality].values[8]
    
    surgery_duration = round(np.random.lognormal(exp, std))
    
    while surgery_duration > max:
        surgery_duration = round(np.random.lognormal(exp, std))
    
    return [surgery_duration, avg]


def set_time_to_discharge(patient, now, discharge_info):
    
    if patient.cancellation == True:
        time_to_discharge = 0
    else:
        time_now = min_to_time(now)
        current_day = time_now[0]
        current_hour = time_now[1]
    
        discharge_day = current_day + patient.LOS_ward

        discharge_list = discharge_info[patient.speciality].values
        
        earliest = discharge_list[0]*60 # Converting hour input to minutes
        peak = discharge_list[1]*60
        latest = discharge_list[2]*60

        if discharge_day == current_day and (current_hour*60) >= (latest-60):
            discharge_day += 1
            patient.add_LOS()
            #print('Next day')
        else: pass      
    
        if discharge_day == current_day:
            discharge_minute = round(np.random.triangular(earliest, peak, latest))
            while min_to_time(discharge_minute)[1] < current_hour + 1:
                discharge_minute = round(np.random.triangular(earliest, peak, latest))
        else:
            discharge_minute = round(np.random.triangular(earliest, peak, latest))

        discharge_time_in_minutes = discharge_minute + (discharge_day * 24 * 60)
        
        time_to_discharge = discharge_time_in_minutes - now
        discharge_time = min_to_time(now + time_to_discharge)
        #print('discharge time: ', discharge_time)
        patient.set_discharge_time(discharge_time)

    return time_to_discharge

def available(ward):
    if ward.count < ward.capacity:
        return True
    else:
        return False

def time_to_hours(time1, time2):
    minutes = time_to_min(time2) - time_to_min(time1)
    return minutes_to_hours(minutes)

def minutes_to_hours(minutes):
    time = min_to_time(minutes)
    return str((time[0]*60) + time[1]) + ":" + str(time[2])

def days_in_weekend(number_of_weeks):
    
    weekend = []
        
    for i in range(number_of_weeks):
        sat = (6 +7*i)
        sun = (7 + 7*i)
        weekend.append(sat)
        weekend.append(sun)
        
        
    return weekend

# Returns opening times in minutes
def OR_opening_times(patient, OR, day_in_cycle, day, resources):
    
    #print('day in cycle ', day_in_cycle)
    #print('day ', day)
    
    opening_hours = resources[OR].values
    
    OR_opening_time = 60*opening_hours[2*(day_in_cycle-1)]
    OR_closing_time = 60*opening_hours[2*(day_in_cycle-1) + 1]
    
    OR_opening_time += day * 24 * 60
    OR_closing_time += day * 24 * 60
    
    opening_times = [OR_opening_time, OR_closing_time]
    
    return opening_times

def check_speciality(now, emerg_patient, OR, mss, emerg_info):
    
    correct_speciality = False
    
    day = min_to_time(now)[0]
    
    day = day%14
    if day == 0:
        day = 14
    
    speciality = emerg_patient.speciality
    
    if speciality == 'KGASA':
        speciality = emerg_patient.KGAS1_or_KGAS2
    else:
        pass

    day_slot_list = mss['Day slot'].values
    assigned_ORs_list = mss['Assigned OR'].values
    speciality_list = mss['Speciality'].values
    
    for i in range(len(day_slot_list)):
        if str(day_slot_list[i]) == "nan":
            pass
        else:
            if int(day_slot_list[i]) == int(day) and assigned_ORs_list[i] == OR and speciality_list[i] == speciality:
                correct_speciality = True
                #print("CORRECT SPECIALITY")

    return correct_speciality

def set_elec_cleaning_time():
    
    cleaning_time = round(float(np.random.triangular(10, 30, 62)))
    
    return cleaning_time

def set_emerg_cleaning_time():
    
    exp = 4.565586
    std = 0.74560
    max = 429.8499999
    
    cleaning_time = round(np.random.lognormal(exp, std))
    while cleaning_time > max:
        cleaning_time = round(np.random.lognormal(exp, std))
    
    return cleaning_time
    

def timeout(object):
    if type(object).__name__ == "Timeout":
        return True
    else:
        return False


def midnight(time):
    hour = min_to_time(time)[1]
    minute = min_to_time(time)[2]
    if hour == 0 and minute == 0:
        return True
    else:
        return False


    
    