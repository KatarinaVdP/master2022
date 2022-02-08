# -*- coding: utf-8 -*-
"""
Created on Wed Apr  7 10:38:55 2021

@author: piai
"""

import simpy
import pandas as pd
import numpy as np
import utils
from xlwt import Workbook
import math



#####################################SETUP#####################################

file = 'input25M.xlsx'
results_file = 'ReplicationEstimate1.xls'

number_of_weeks = 11
runs = 60
warm_up_weeks = [1,2,3,4]

cancel_surgeries = False # If True, then elective surgeries are cancelled if they were to start after closing time of OR
late_elec_start = False # If True, then elective surgeries can start even if the expected surgery duration indicates that the surgery will last longer than the OR is open
late_emerg_start = False # If True, then emergency surgeries can start even if the expected surgery duration indicates that the surgery will last longer than the OR is open

print('Input file: %s, results file: %s, cancellations?: %s' %(file, results_file, str(cancel_surgeries)))
print()

#####################################SETUP#####################################

if not cancel_surgeries:
    late_elec_start = True # If surgeries cannot be cancelled, it is not logical not to allow surgeries to start late
else:
    pass

# Class for a surgery clinic
class Clinic:
    def __init__(self, env, KGASA_cap, KGAS1_cap, KGAS2_cap, KURS_cap, KENS_cap, KKAS_cap, ICU_cap, TOV_cap, GA1_cap, GA2_cap, GA3_cap, GA4_cap, GA5_cap, GA6_cap, GA7_cap, emerg_OR_cap, red_emerg_OR_cap):
        self.KGASA = simpy.PriorityResource(env, capacity=float(KGASA_cap))
        self.KGAS1 = simpy.PriorityResource(env, capacity=float(KGAS1_cap))
        self.KGAS2 = simpy.PriorityResource(env, capacity=float(KGAS2_cap))
        self.KURS = simpy.PriorityResource(env, capacity=float(KURS_cap))
        self.KENS = simpy.PriorityResource(env, capacity=float(KENS_cap))
        self.KKAS = simpy.PriorityResource(env, capacity=float(KKAS_cap))
        self.ICU = simpy.PriorityResource(env, capacity=float(ICU_cap))
        self.TOV = simpy.PriorityResource(env, capacity=float(TOV_cap))
        self.GA1 = simpy.PriorityResource(env, capacity = GA1_cap)
        self.GA2 = simpy.PriorityResource(env, capacity = GA2_cap)
        self.GA3 = simpy.PriorityResource(env, capacity = GA3_cap)
        self.GA4 = simpy.PriorityResource(env, capacity = GA4_cap)
        self.GA5 = simpy.PriorityResource(env, capacity = GA5_cap)
        self.GA6 = simpy.PriorityResource(env, capacity = GA6_cap)
        self.GA7 = simpy.PriorityResource(env, capacity = GA7_cap)
        self.emerg_OR = simpy.PriorityResource(env, capacity = emerg_OR_cap)
        self.red_emerg_OR = simpy.PriorityResource(env, capacity = red_emerg_OR_cap)
        self.unavailable_OR = simpy.PriorityResource(env, capacity = 1)
        
        
# Class for elective patients
class ElecPatients:
    def __init__(self, weeknr, arrival_time, patient_group, speciality, surgery_day, surgery_room, surgery_duration, start_LOS_ward, LOS_ward, LOS_TOV, LOS_ICU, med_sur_dur, dummy_group):
        self.weeknr = weeknr
        self.arrival_time = arrival_time    #A list where [0]=day, [1]=hour, [2]=minute
        self.patient_group = patient_group
        self.speciality = speciality
        self.surgery_day = surgery_day
        self.surgery_duration = surgery_duration    #In minutes
        self.start_LOS_ward = start_LOS_ward
        self.LOS_ward = LOS_ward
        self.LOS_TOV = LOS_TOV
        self.LOS_ICU = LOS_ICU
        self.surgery_room = surgery_room
        self.med_sur_dur = med_sur_dur
        self.type = 'elec'
        self.dummy_group = dummy_group
        
        self.surgery_time = None
        self.surgery_done = None
        self.discharge_time = None
        self.priority = None
        self.id = None

        
        self.cancellation = 0
        self.overtime = 0
        self.cleaning_time = 0
        

        
    def set_priority(self, priority):
        self.priority = priority
    def set_surgery_time(self, surgery_time):
        self.surgery_time = surgery_time
    def set_discharge_time(self, discharge_time):
        self.discharge_time = discharge_time
    def set_cancellation(self):
        self.cancellation = 1
        self.start_LOS_ward = 0
        self.LOS_ward = 0
        self.LOS_ICU = 0
        self.LOS_TOV = 0
    def set_overtime(self, time):
        self.overtime = time 
    def set_id(self, id):
        self.id = id
    def set_cleaning_time(self, time):
        self.cleaning_time = time
    def set_surgery_done(self, minutes):
        self.surgery_done = utils.min_to_time(minutes)
    def add_LOS(self):
        self.LOS_ward += 1       
    
        
# Class for emergency patients
class EmergPatient:
    def __init__(self, id, weeknr, arrival_time, speciality, surgery, surgery_pri, surgery_duration, start_LOS_ward, LOS_ward, LOS_TOV, LOS_ICU, med_sur_dur):
        self.id = id 
        self.weeknr = weeknr
        self.arrival_time = arrival_time    #A list where [0]=day, [1]=hour, [2]=minute
        self.speciality = speciality   #KGAS1, KGAS2, KGASA or URO
        self.surgery = surgery
        self.surgery_pri = surgery_pri   # Surgery priority
        self.surgery_duration = surgery_duration    #In minutes
        self.start_LOS_ward = start_LOS_ward
        self.LOS_ward = LOS_ward
        self.LOS_TOV = LOS_TOV
        self.LOS_ICU = LOS_ICU
        self.med_sur_dur = med_sur_dur
        
        self.admission_time = None
        self.surgery_reg_time = None
        self.surgery_time = None
        self.surgery_done = None
        self.surgery_room = None
        self.discharge_time = None
        self.arrivalWeekend = None
        self.surgeryWeek = None
        self.surgeryWeekend = None
        self.cancellation = False
        self.old_surgery_pri = 0
        self.KGAS1_or_KGAS2 = None
        self.request = None
        self.ward_priority = 1
        self.reached_threshold = 0
        self.cleaning_time = 0
        self.overtime = 0
        self.waiting_time = 0
        
        self.type = 'emerg'

    def set_admission_time(self, admission_time):
        self.admission_time = admission_time
    def set_surgery_reg_time(self, surgery_reg_time):
        self.surgery_reg_time = surgery_reg_time
    def set_surgery_time(self, surgery_time):
        self.surgery_time = surgery_time
    def set_surgery_room(self, surgery_room):
        self.surgery_room = surgery_room
    def set_discharge_time(self, discharge_time):
        self.discharge_time = discharge_time
    def set_arrivalWeekend(self, x):
        self.arrivalWeekend = x
    def set_surgeryWeek(self, x):
        self.surgeryWeek = int(x)
    def set_surgeryWeekend(self, x):
        self.surgeryWeekend = x
    def set_new_surgery_pri(self, surg_pri):
        self.old_surgery_pri = surg_pri
        self.surgery_pri = 1
    def set_KGAS1_or_KGAS2(self, ward):
        self.KGAS1_or_KGAS2 = ward
    def set_reached_threshold(self):
        self.reached_threshold += 1
    def set_cleaning_time(self, time):
        self.cleaning_time = time
    def set_surgery_done(self, minutes):
        self.surgery_done = utils.min_to_time(minutes)
    def set_overtime(self, minutes):
        self.overtime = minutes
    def add_LOS(self):
        self.LOS_ward += 1
    def set_waiting_time(self, surgery_time, surgery_reg_time):
        self.waiting_time = (utils.time_to_min(surgery_time) - utils.time_to_min(surgery_reg_time))
        
        
        
# Creating the surgery clinic object
def clinic_generator(env, resources):
    capacity = resources['Max avail'].values
    KGASA_cap = capacity[0]
    KGAS1_cap = capacity[1]
    KGAS2_cap = capacity[2]
    KURS_cap = capacity[3]
    KENS_cap = capacity[4]
    KKAS_cap = capacity[5]
    ICU_cap = capacity[6]
    TOV_cap = capacity[7]
    GA1_cap = capacity[8]
    GA2_cap = capacity[9]
    GA3_cap = capacity[10]
    GA4_cap = capacity[11]
    GA5_cap = capacity[12]
    GA6_cap = capacity[13]
    GA7_cap = capacity[14]
    emerg_OR_cap = capacity[15]
    red_emerg_OR_cap = capacity[16]

    clinic = Clinic(env, KGASA_cap, KGAS1_cap, KGAS2_cap, KURS_cap, KENS_cap, KKAS_cap, ICU_cap, TOV_cap, GA1_cap, GA2_cap, GA3_cap, GA4_cap, GA5_cap, GA6_cap, GA7_cap, emerg_OR_cap, red_emerg_OR_cap)
    return clinic 


# Generate elective patients according to MSS
def elec_patient_generator(mss, elec_info, ward_sheet, number_of_weeks, number_of_cycles):
    
    #Retrieving info from MSS:
    patient_group_list = mss['Patient group'].values
    OR_list = mss['OR'].values
    surgery_day_list = mss['Surgery day'].values
    number_of_patients_list = mss['Number of patients'].values
    
    #Retrieving info on patient
    patient_group_info_list =  elec_info['Patient group'].values
    speciality_list = elec_info['Speciality'].values
    med_sur_dur_list = elec_info['Median surgery duration [min]'].values
    
    elec_patient_list = [] #Fill in with all patients
    
    for i in range(number_of_cycles):
        for j in range(len(surgery_day_list)):
            
            weeknr = math.ceil( (i*14 + surgery_day_list[j]) /7)
            patient_group = str(patient_group_list[j])
            surgery_room = str(OR_list[j])
            surgery_day = i*14  + surgery_day_list[j] #Continue counting after day 14
            arrival_time = [surgery_day, 7, 0] #Temporarily set all elective patients to arrive at this point in time on the day of their surgery
            
            for k in range(len(speciality_list)): 
                if patient_group_info_list[k] == patient_group:
                    speciality = speciality_list[k]
                    med_sur_dur = med_sur_dur_list[k]
            
            number_of_patients = number_of_patients_list[j]
            for l in range(int(number_of_patients)):
                
                patient_group, dummy_group = utils.set_dummy_group(patient_group, elec_info, patient_group_info_list)
                
                surgery_duration = utils.set_elec_surgery_duration(patient_group, elec_info, patient_group_info_list) #Log-normal distribution
                
                [start_LOS_ward, LOS_ward, LOS_TOV, LOS_ICU] = utils.set_elec_LOS(patient_group, ward_sheet, elec_info)
            
                elec_patient = ElecPatients(weeknr, arrival_time, patient_group, speciality, surgery_day, surgery_room, surgery_duration, start_LOS_ward, LOS_ward, LOS_TOV, LOS_ICU, med_sur_dur, dummy_group)

                elec_patient_list.append(elec_patient)
                
    return elec_patient_list
            

def sequence_elec_surgery(elec_patient_list, number_of_weeks):
    
    elec_ORs = ['GA1', 'GA2', 'GA3', 'GA4', 'GA5', 'GA6', 'GA7']
    
    id = 1
    
    for day in range(7*number_of_weeks): # Sequencing for each day
        if not (day+1) in utils.days_in_weekend(number_of_weeks):
            for OR in range(7): # Sequencing for each OR, 7 elective ORs
                #print('Day %d in OR %d' %(day+1,OR+1))
                slot_list = []
                priority = 1
                for elec_patient in elec_patient_list:
                    if elec_patient.surgery_day == (day+1) and elec_patient.surgery_room == elec_ORs[OR]:
                        slot_list.append(elec_patient)
                
                #print('list before sorting:')
                #for elec_patient in slot_list:
                    #print(elec_patient.surgery_day, str(elec_patient.surgery_room), str(elec_patient.patient_group), elec_patient.surgery_duration)
                    
                slot_list.sort(key = utils.durSort, reverse = True)
                
                #print('list after sorting:')
                #for elec_patient in slot_list:
                    #print(elec_patient.surgery_day, str(elec_patient.surgery_room), str(elec_patient.patient_group), elec_patient.surgery_duration)
                
                for elec_patient in slot_list:
                    elec_patient.set_priority(priority)
                    elec_patient.set_id(id)
                    id += 1
                    priority += 1
                    
                #print('list after priority:')
                #for elec_patient in slot_list:
                    #print(elec_patient.surgery_day, str(elec_patient.surgery_room), str(elec_patient.patient_group), elec_patient.surgery_duration, elec_patient.priority)
    
    elec_patient_list.sort(key = utils.idSort)
    return elec_patient_list

# Creating multiple emergency patient objects. Returning a list of patients to send through hospital_stay.
# The input paramenter Random_week is six random week numbers we want to look at
def emerg_patient_generator(emerg_arrivals, emerg_info, random_weeks, ward_sheet):
    weeknr_list = emerg_arrivals['Weeknr'].values
    daynr_list = emerg_arrivals['Daynr'].values
    hour_list = emerg_arrivals['Hour'].values
    minute_list = emerg_arrivals['Minute'].values

    emerg_patient_list = []
    id = 0

    # Creating patients arriving from the ED
    # Going through the total list of arriving emergency patients
    for i in range(len(weeknr_list)):
        if weeknr_list[i] in random_weeks:
            id += 1
            weeknr = random_weeks.index(weeknr_list[i]) + 1
            arrival_time = [daynr_list[i] + (7*(weeknr-1)), hour_list[i], minute_list[i]]

            speciality = utils.set_speciality(emerg_info)
            surgery = utils.set_surgery(emerg_info, speciality)

            patient_group = "EM-"+ speciality
            
            if surgery == 1:
                surgery_pri = utils.set_surgery_pri(emerg_info, speciality)
                [surgery_duration, med_sur_dur] = utils.set_emerg_surgery_duration(emerg_info, speciality)
                patient_group+="-S"
            else:
                surgery_pri = 0
                surgery_duration = 0
                med_sur_dur = None


            [start_LOS_ward, LOS_ward, LOS_TOV, LOS_ICU] = utils.set_emerg_LOS(patient_group, ward_sheet, emerg_info, speciality)

            emerg_patient = EmergPatient(id, weeknr, arrival_time, speciality, surgery, surgery_pri, surgery_duration, start_LOS_ward, LOS_ward, LOS_TOV, LOS_ICU, med_sur_dur)
            
            if speciality == 'KGASA':
                utils.KGAS1_KGAS2(emerg_info, emerg_patient) # Deciding which speciality should operate on the patient on elective side
            else:
                pass
            
            # Adding the created emergency patient object to the list
            emerg_patient_list.append(emerg_patient)

    emerg_patient_list.sort(key = utils.arrSort)
    return emerg_patient_list

# Creating other entities that occupy the ORs at night to simulate closing times of ORs or to simulate unavailability
# Returns time in minutes
def closed_OR_times_generator(number_of_cycles, resources):
    
    closed_periods = []  

    stop_sim = number_of_weeks * 7 * 24 * 60 + 1
    closed_periods.append(['unavailable_OR', 0, stop_sim])
    
    #closed_periods.append(['red_emerg_OR', 0, stop_sim]) 
    use = 1
    if use == 1:
        #print("")
        #print('Closing red_emerg_OR')
        for day in range(number_of_weeks*7):
            #if (day+1) in utils.days_in_weekend(number_of_weeks):
                #start = (day+1)*24*60
                #stop = (day+1)*24*60 + 24*60
            #else:
            start = (day+1)*24*60 + (8*60)
            stop = (day+1)*24*60 + (16*60)
            #print("")
            #print('Closing red_emerg_OR at', utils.min_to_time(start))
            #print('Open red_emerg_OR at', utils.min_to_time(stop))
            closed_periods.append(['red_emerg_OR', start, stop])
    
    '''
    red_OR = 'red_emerg_OR'
    afternoon = 16*60 # Other patients arrive from 16
    open_OR = 4*60 # Open for 4 hours
    morning = 7*60 # OR to themselves
    latest_open = morning-open_OR
    
    #first night red_emerg, no surgeries
    stop = 24*60 + morning
    closed_periods.append([red_OR, 0, stop])
    
    
    midnight = 24*60
    next_midnight = midnight + 24*60
    for i in range(number_of_weeks*7):
        start = midnight + afternoon
        print()
        print('Closing OR at', utils.min_to_time(start))
        stop = np.random.randint(start, high = next_midnight + latest_open) # Start min of open OR
        print('Open OR at', utils.min_to_time(stop))
        closed_periods.append([red_OR, start, stop])
        start = stop + open_OR
        print('Closing OR at', utils.min_to_time(start))
        closed_periods.append([red_OR, start, next_midnight + morning])
        print('Open OR at', utils.min_to_time(next_midnight+ morning))
        midnight += 24*60
        next_midnight = midnight + 24*60
    ''' 
    ORs_str = ['emerg_OR', 'GA1', 'GA2', 'GA3', 'GA4', 'GA5', 'GA6', 'GA7']
    
    ORs_opening_times = []        
    for i in range(len(ORs_str)):
        ORs_opening_times.append(resources[ORs_str[i]].values) # Retrieving all opening times
          
    # The first day
    for OR in range(len(ORs_str)):
        start = 0
        stop = 24*60 + (ORs_opening_times[OR][0])*60
        
        #print('OR %s is closed between %s and %s' % (ORs_str[OR],utils.min_to_time(start),utils.min_to_time(stop)))
        closed_periods.append([ORs_str[OR], start, stop])
    
    #All other days
    for cycle in range(number_of_cycles):
        for day in range(14):
            for OR in range(len(ORs_str)):
                
                start = cycle*14*24*60 + (day+1)*24*60 + (ORs_opening_times[OR][2*(day) + 1])*60
                
                if day == 13:
                    stop = cycle*14*24*60 + (day+2)*24*60 + (ORs_opening_times[OR][0])*60
                else:
                    stop = cycle*14*24*60 + (day+2)*24*60 + (ORs_opening_times[OR][2*(day) + 2])*60
                
                #if ORs_str[OR] == 'emerg_OR':
                    #print('OR %s is closed between %s and %s' % (ORs_str[OR], utils.min_to_time(start),utils.min_to_time(stop)))
                closed_periods.append([ORs_str[OR], start, stop])
    
    return closed_periods

    
def elec_hospital_stay(env, elec_patient, clinic, discharge_info, number_of_weeks, elec_patient_list, resources):
    
    yield env.timeout(utils.time_to_min(elec_patient.arrival_time)) #Fast forward to the arrival of the patient
    
    # print('Elective patient %s has arrived at %s in week %s' % (elec_patient.id, str(utils.min_to_time(env.now)), elec_patient.weeknr))
    
    ward = utils.get_resource(elec_patient.speciality, clinic)
    
    req = ward.request(priority = elec_patient.priority)
    yield req #Receiving a bed in the speciality
    
    yield env.process(elec_surgery(env, elec_patient, clinic, resources, number_of_weeks))
    
    time_to_discharge = utils.set_time_to_discharge(elec_patient, env.now, discharge_info)
    discharge_time = env.now + time_to_discharge
    
    if not elec_patient.start_LOS_ward == 0:
        IC_clinic = [clinic.TOV, clinic.ICU]
        
        if elec_patient.LOS_TOV > 0:
            LOS_IC = elec_patient.LOS_TOV
            IC_ward = IC_clinic[0]
        elif elec_patient.LOS_ICU > 0:
            LOS_IC = elec_patient.LOS_ICU
            IC_ward = IC_clinic[1]
        else:
            print('Elec_patient %s has not recieved an IC even though he/she has a start_LOS_ward greater than 0' %elec_patient.id )
        
        IC_req = IC_ward.request(priority = elec_patient.priority) 
        yield IC_req
        
        move_day = utils.min_to_time(env.now)[0] + LOS_IC
        move_hour = 12
        move_minute = 0
        
        move = [move_day, move_hour, move_minute]
        yield env.timeout(utils.time_to_min(move) - env.now)

        IC_ward.release(IC_req)
    else:
        pass
   
    yield env.timeout(discharge_time - env.now)
    ward.release(req)


# Simulation of the hospital stay for each emergency patient
def emerg_hospital_stay(env, emerg_patient, clinic, number_of_weeks, discharge_info, emerg_info, resources, ward_pre_reg_sheet):
    
    # Skip to the point in time where the patient arrives
    yield env.timeout(utils.time_to_min(emerg_patient.arrival_time) - env.now)
    # print('Emergency patient %s has arrived at %s in week %s' % (emerg_patient.id, str(utils.min_to_time(env.now)), emerg_patient.weeknr))
    
    ward = utils.get_resource(emerg_patient.speciality, clinic)
    
    # Request a bed within the speciality
    req = ward.request(priority = emerg_patient.ward_priority)
    yield req

    # Updating patient object, giving the patient their admission time
    emerg_patient.set_admission_time(utils.min_to_time(env.now))
   
    weekend = utils.days_in_weekend(number_of_weeks)
   
    if emerg_patient.admission_time[0] in weekend:
        emerg_patient.set_arrivalWeekend(1)
    else:
        emerg_patient.set_arrivalWeekend(0)

    # If patient needs surgery, surgery and postoperative care and is performed
    if emerg_patient.surgery == 1:
        time_to_reg = utils.set_time_to_reg(emerg_patient, env.now, emerg_info, ward_pre_reg_sheet)
        yield env.timeout(time_to_reg)
        yield env.process(emerg_surgery(env, emerg_patient, clinic, number_of_weeks, emerg_info, resources, mss))
        emerg_patient.set_waiting_time(emerg_patient.surgery_time, emerg_patient.surgery_reg_time)
    else:
        pass # No surgery performed

    time_to_discharge = utils.set_time_to_discharge(emerg_patient, env.now, discharge_info)
    discharge_time = env.now + time_to_discharge
    #print('Discharge time for emerg_patient %s is at %s' %(emerg_patient.id, utils.min_to_time(discharge_time)))
    
    if not emerg_patient.start_LOS_ward == 0:
        IC_clinic = [clinic.TOV, clinic.ICU]
        
        if emerg_patient.LOS_TOV > 0:
            LOS_IC = emerg_patient.LOS_TOV
            IC_ward = IC_clinic[0]
        elif emerg_patient.LOS_ICU > 0:
            LOS_IC = emerg_patient.LOS_ICU
            IC_ward = IC_clinic[1]
        else:
            print('emerg_patient %s has not recieved an IC even though he/she has a start_LOS_ward greater than 0' %emerg_patient.id )
        
        IC_req = IC_ward.request(priority = emerg_patient.ward_priority) 
        yield IC_req
        
        move_day = utils.min_to_time(env.now)[0] + LOS_IC
        move_hour = 12
        move_minute = 0
        
        move = [move_day, move_hour, move_minute]
        yield env.timeout(utils.time_to_min(move) - env.now)

        IC_ward.release(IC_req)
    else:
        pass
   
    yield env.timeout(discharge_time - env.now)
    ward.release(req)

    #print('Emerg_patient %s is discharged from bed at %s' % (emerg_patient.id, str(utils.min_to_time(env.now))))


def elec_surgery(env, elec_patient, clinic, resources, number_of_weeks):
    
    duration = elec_patient.surgery_duration
    elec_OR = utils.get_resource(elec_patient.surgery_room, clinic)
    day = elec_patient.surgery_day
    
    day_in_cycle = day % 14

    if day_in_cycle == 0:
        day_in_cycle = 14 + int(day_in_cycle/14)
    
    [na, OR_closing_time] = utils.OR_opening_times(elec_patient, elec_patient.surgery_room, day_in_cycle, day, resources)
    
    yield env.timeout(utils.time_to_min([day, 7, 0]) - env.now) #Fast forward to an hour prior to surgery of patient
    
    # print('Count dag %d in elec_OR %s is %s' %(day, elec_patient.surgery_room, elec_OR.count))
    
    #print('Closing time of OR is %s, time now is %s'%(utils.min_to_time(OR_closing_time), utils.min_to_time(env.now)))
    #print('elec_patient.med_sur_dur ', utils.min_to_time(elec_patient.med_sur_dur), elec_patient.med_sur_dur)
    #print('Cutoff point is ', (utils.min_to_time(OR_closing_time-elec_patient.med_sur_dur)))
    
    if cancel_surgeries and late_elec_start: # Surgeries can start up until closing of OR
        cutoff_point = env.timeout(OR_closing_time - env.now)
    elif cancel_surgeries: # Surgeries can only start if the expected surgery duration indicates that the surgery will be done prior to closing time of OR
        cutoff_point = env.timeout(OR_closing_time - elec_patient.med_sur_dur - env.now)
    else: # No limits as to when the elective surgery can start
        cutoff_point = env.timeout(number_of_weeks*7*24*60)
    
    with elec_OR.request(priority = elec_patient.priority) as surg_req:
        
        yield surg_req | cutoff_point
        
        if surg_req.triggered:
            #print('Elec patient %d enters room %s at %s' %(elec_patient.id ,elec_patient.surgery_room, utils.min_to_time(env.now)))
            elec_patient.set_surgery_time(utils.min_to_time(env.now))
            
            yield env.timeout(duration)
            elec_patient.set_surgery_done(env.now)

            
            cleaning_t = utils.set_elec_cleaning_time()
            elec_patient.set_cleaning_time(cleaning_t)
            yield env.timeout(cleaning_t) #Cleaning of OR
            if env.now > OR_closing_time:
                if (env.now - duration - cleaning_t) > OR_closing_time:
                    elec_patient.set_overtime(duration + cleaning_t)
                else:
                    elec_patient.set_overtime(env.now - OR_closing_time)
                    #print('Surgery is done at %s for patient %s. Overtime is set to %d' %(utils.min_to_time(env.now), elec_patient.id, elec_patient.overtime))
            else:
                pass
            elec_OR.release(surg_req)
            # print('Elec patient leaves room %s at %s' %(elec_patient.surgery_room, utils.min_to_time(env.now)))
        
        else:
            elec_patient.set_cancellation()
            elec_patient.set_discharge_time(utils.min_to_time(env.now))
            
            # print('Surgery of elec_patient %s is cancelled at %s' % (elec_patient.id, str(utils.min_to_time(env.now))))
            
            
    return elec_patient.surgery_time


# Requesting surgery for emergency patient -> Waiting until available operation room -> Performing surgery on patient -> Releasing OR
def emerg_surgery(env, emerg_patient, clinic, number_of_weeks, emerg_info, resources, mss):
    
    duration = emerg_patient.surgery_duration
    threshold_list = emerg_info['Threshold'].values
    
    surg_pri = emerg_patient.surgery_pri
    threshold = threshold_list[int(surg_pri)]

    if surg_pri == 1:
        maybe = 'unavailable_OR'
    else:
        maybe = 'unavailable_OR'
        
    ORs_str = ['emerg_OR', maybe, 'GA1', 'GA2', 'GA3', 'GA4', 'GA5', 'GA6', 'GA7']

    reqs = []
    for i in range(len(ORs_str)):
        resource = utils.get_resource(ORs_str[i], clinic)
        req = resource.request(priority = surg_pri*100)
        reqs.append(req)

    time_threshold = env.now + threshold*60

    while not emerg_patient.surgery_room:

        until_threshold = env.timeout(time_threshold - env.now)
        timeouts = []
        
        yield reqs[0] | reqs[1] | reqs[2] | reqs[3] | reqs[4] | reqs[5] | reqs[6] | reqs[7] | reqs[8] | until_threshold

        for i in range(len(reqs)):
            req, room = reqs[i], ORs_str[i]
            
            day = utils.min_to_time(env.now)[0]
            day_in_cycle = day % 14

            if day_in_cycle == 0:
                day_in_cycle = 14 + int(day_in_cycle/14)

            # If the req is a timeout, pass
            if utils.timeout(req):
                timeouts.append(i)

            # If req is triggered
            elif req.triggered:

                # Already have a room, release
                if emerg_patient.surgery_room:
                    utils.get_resource(room, clinic).release(req)

                # Emergency room:
                elif i<2:
                    
                    OR_closing_time = utils.OR_opening_times(emerg_patient, room, day_in_cycle, day, resources)[1]
                    
                    if room == 'red_emerg_OR' or late_emerg_start or emerg_patient.med_sur_dur < (OR_closing_time - env.now):
                        emerg_patient.set_surgery_room(room)
                        emerg_patient.request = req
                        emerg_patient.set_surgery_time(utils.min_to_time(env.now))
                        if emerg_patient.surgery_time[0] in utils.days_in_weekend(number_of_weeks):
                            emerg_patient.set_surgeryWeekend(1)
                        else:
                            emerg_patient.set_surgeryWeekend(0)
                        surgeryWeek = np.ceil(emerg_patient.surgery_time[0] / 7)
                        emerg_patient.set_surgeryWeek(surgeryWeek)
                    
                    else:
                        utils.get_resource(room, clinic).release(req)
                        reqs[i] = env.timeout(utils.time_to_min([day+1, 0, 0]) - env.now)

                # Elective room
                else:
                    
                    OR_closing_time = utils.OR_opening_times(emerg_patient, room, day_in_cycle, day, resources)[1]
                    if utils.check_speciality(env.now, emerg_patient, room, mss, emerg_info) and (
                            late_emerg_start or emerg_patient.med_sur_dur < (OR_closing_time - env.now)):
                        #print("Received elective room!")
                        emerg_patient.set_surgery_room(room)
                        emerg_patient.request = req
                        emerg_patient.set_surgery_time(utils.min_to_time(env.now))
                        emerg_patient.set_surgery_done(env.now)
                        emerg_patient.set_surgeryWeekend(0)
                        surgeryWeek = np.ceil(emerg_patient.surgery_time[0] / 7)
                        emerg_patient.set_surgeryWeek(surgeryWeek)
                    else:
                        utils.get_resource(room, clinic).release(req)
                        reqs[i] = env.timeout(utils.time_to_min([day+1, 0, 0]) - env.now)
            else:
                pass


        #deadlines = [6, 24, 72]
        if not emerg_patient.surgery_room:
            # Loop is gonna run again, so timeouts needs to be taken care of
            threshold_reached = False
            if time_threshold - env.now == 0:
                threshold_reached = True
                emerg_patient.set_reached_threshold()

                time_threshold = number_of_weeks*7*24*60 + 1
                
            if threshold_reached:
                if emerg_patient.surgery_pri == 1 and emerg_patient.old_surgery_pri == 0:
                    emerg_patient.set_new_surgery_pri(surg_pri)
                    ORs_str[1] = 'red_emerg_OR'
                    reqs[1] = utils.get_resource(ORs_str[1], clinic).request(priority=surg_pri * 100)
                
                elif emerg_patient.surgery_pri != 1:
                    emerg_patient.set_new_surgery_pri(surg_pri)
                    surg_pri = emerg_patient.surgery_pri
                    #ORs_str[1] = 'red_emerg_OR'
                    for i in range(len(reqs)):
                        if not i in timeouts:
                            try: reqs[i].cancel()
                            except: pass
                        resource = ORs_str[i]
                        reqs[i] = utils.get_resource(resource, clinic).request(priority=99)
                        

            elif utils.midnight(env.now):
                for i in timeouts:
                    reqs[i] = utils.get_resource(ORs_str[i], clinic).request(priority=surg_pri * 100)
            else:
                pass
            
    for req in reqs:
        if not req==emerg_patient.request:
            try: req.cancel()
            except: pass
        
    #if emerg_patient.surgery_room == 'emerg_OR':
        #print('Starting surgery at ', utils.min_to_time(env.now))
        #print('Duration: ', emerg_patient.surgery_duration)
    yield env.timeout(duration)
    emerg_patient.set_surgery_done(env.now)
    
    emerg_ORs = ['GA1', 'GA2', 'GA3', 'GA4', 'GA5', 'GA6', 'GA7']
    
    if emerg_patient.surgery_room in emerg_ORs:
        cleaning_time = utils.set_elec_cleaning_time()
    else:
        cleaning_time = utils.set_emerg_cleaning_time()
    
    if (env.now + cleaning_time) > 60*24*7*number_of_weeks:
        emerg_patient.set_cleaning_time(60*24*7*number_of_weeks-env.now)
    else:
        emerg_patient.set_cleaning_time(cleaning_time)
        
    yield env.timeout(cleaning_time) #Vasking
    
    if emerg_patient.surgery_room != 'red_emerg_OR':
        # Setting overtime
        day = emerg_patient.surgery_time[0]
        day_in_cycle = day % 14
    
        if day_in_cycle == 0:
            day_in_cycle = 14 + int(day_in_cycle/14)
        
        [na, OR_closing_time] = utils.OR_opening_times(emerg_patient, emerg_patient.surgery_room, day_in_cycle, day, resources)
        if utils.time_to_min(emerg_patient.surgery_done) > OR_closing_time:
            if (env.now - duration - cleaning_time) > OR_closing_time:
                emerg_patient.set_overtime(duration + cleaning_time)
            else:
                emerg_patient.set_overtime(int(env.now - OR_closing_time))
            

    
    utils.get_resource(emerg_patient.surgery_room, clinic).release(emerg_patient.request)

            
    
# Closing OR in unavailable periods
def closing_OR(env, clinic, period):
    # Period is an array [str(OR), start, stop]
    OR = utils.get_resource(period[0], clinic)
    start = period[1]
    stop = period[2]
    
    yield env.timeout(start - env.now)
    
    with OR.request( priority = 50 ) as req:
        yield req
        #if period[0] == 'red_emerg_OR' and 30 > utils.min_to_time(env.now)[0] > 15:
            #print()
            #print('Closing %s at %s' % (period[0], utils.min_to_time(env.now)))
            #print('Should open at time ',utils.min_to_time(stop))
        try: yield env.timeout(stop - env.now)
        except: 
            pass
        #print('Passed: ', utils.min_to_time(env.now))
        #if period[0] == 'red_emerg_OR':
            #print('Opening %s at %s ' % (period[0], utils.min_to_time(env.now)))
        OR.release(req)
        
        
# A list that updates every day, counting the number of patients occupying the different wards
def status(env, clinic, status_list, number_of_weeks):
    night = 0

    # Yield to start day1
    yield env.timeout(2*60*24)

    while True:
        # Midnight:
        night += 1
        KGAS1 = clinic.KGAS1.count
        KGAS2 = clinic.KGAS2.count
        KGASA = clinic.KGASA.count
        KURS = clinic.KURS.count
        KENS = clinic.KENS.count
        KKAS = clinic.KKAS.count
        ICU = clinic.ICU.count
        TOV = clinic.TOV.count

        entry = [night, KGAS1, KGAS2, KGASA, KURS, KENS, KKAS, ICU, TOV]

        status_list.append(entry)
        # yield next night :
        yield env.timeout(60 * 24)

    
# Main functions, utilizing all previously defined functions
def main(seed, run, resources, mss, discharge_info, elec_info, emerg_arrivals, emerg_info , all_elec_LOS, arrival_weeks, number_of_weeks, number_of_cycles, ward_pre_reg_sheet):

    np.random.seed(seed)
    env = simpy.Environment()

    # Choosing 5 random weeks where the number of arriving patients is >44
    random_weeks = []
    for i in range(number_of_weeks):
        new_week = np.random.choice(arrival_weeks)
        while new_week in random_weeks:
            new_week = np.random.choice(arrival_weeks)
        random_weeks.append(new_week)
        

    
    # Generating a list of elective patients and a list of OR_day_slots which contains which patients to be operated on each day in every OR
    elec_patient_list = elec_patient_generator(mss, elec_info, ward_sheet, number_of_weeks, number_of_cycles)
    

    
    #Sequencing patients within the OR slots
    elec_patient_list = sequence_elec_surgery(elec_patient_list, number_of_weeks)

    # Generating a list of emergency patient entities
    emerg_patient_list = emerg_patient_generator(emerg_arrivals, emerg_info, random_weeks, ward_sheet)



    # Initiating the surgical clinic object
    clinic = clinic_generator(env, resources)

    # Generating a list of the closed periods of the ORs
    closed_OR_times_list = closed_OR_times_generator(number_of_cycles, resources)
    
    #print('length of closed OR times: ', len(closed_OR_times_list))

    # Starting the simulation processes
    for period in closed_OR_times_list:
        env.process(closing_OR(env, clinic, period))
    
    for elec_patient in elec_patient_list:
        env.process(elec_hospital_stay(env, elec_patient, clinic, discharge_info, number_of_weeks, elec_patient_list, resources))
    
    for emerg_patient in emerg_patient_list:
        env.process(emerg_hospital_stay(env, emerg_patient, clinic, number_of_weeks, discharge_info, emerg_info, resources, ward_pre_reg_sheet))

    # Starting the status process
    status_list = []
    env.process(status(env, clinic, status_list, number_of_weeks))

    #Running simulation for chosen number_of_weeks
    env.run(until = number_of_weeks*7*24*60 + 1) # Adding 1 to run status on last night
    
    return elec_patient_list, emerg_patient_list, status_list
    # 
    
    
#--------------------------------------------------


#Reading sheets in file
resources = pd.read_excel(file, sheet_name='resources')
mss = pd.read_excel(file, sheet_name='mss')
discharge_info = pd.read_excel(file, sheet_name = 'discharge_info')
elec_info = pd.read_excel(file, sheet_name ='elec_info')
emerg_arrivals = pd.read_excel(file, sheet_name='emerg_arrivals')
emerg_info = pd.read_excel(file, sheet_name = 'emerg_info')

#Retrieving LOS in each ward for elec patient
ward_sheet = pd.read_excel(file, sheet_name = 'Ward')
ward_pre_reg_sheet = pd.read_excel(file, sheet_name = 'WardPreReg')

arrival_weeks = emerg_arrivals['Weeks in simulation'].tolist() # Arrival weeks for emergency patients. Only busy weeks

for week in arrival_weeks[:]:
    if str(week) == "nan":
        arrival_weeks.remove(week)

for i in range(len(arrival_weeks)):
    arrival_weeks[i] = int(arrival_weeks[i])

number_of_cycles = int(number_of_weeks/2) # Since MSS is a cyclic schedule, number of weeks is divided by 2

seeds_list = []

possible_seeds = []

for i in range(100):
    possible_seeds.append(i+1)


for i in range(runs):
    seeds_list.append(np.random.choice(possible_seeds))
    print(seeds_list[i])
    possible_seeds.remove(seeds_list[i])

print('Seeds: ', seeds_list)
    
total_elec_patient_list = []
total_emerg_patient_list = []
total_status_list = []

for r in range(runs):
    # Running main function

    elec_patient_list, emerg_patient_list, status_list = main(seeds_list[r], r, resources, mss, discharge_info, elec_info, emerg_arrivals, emerg_info , ward_sheet, arrival_weeks, number_of_weeks, number_of_cycles, ward_pre_reg_sheet) 
    
    total_elec_patient_list.append(elec_patient_list)
    total_emerg_patient_list.append(emerg_patient_list)
    total_status_list.append(status_list)
    
    print("Simulation run " + str(r+1) + " is done")
    

#Writing to file
hb = Workbook()
    
# Finding and printing performance measures

wards = ['KGAS1', 'KGAS2', 'KGASA', 'KURS', 'KENS', 'KKAS', 'ICU', 'TOV']

# Elec patients

elec_overtime = [None]*(runs+1)
elec_cancellations = [None]*(runs+1)
elec_count = [None]*(runs+1)

run = 1
for i in range(runs):
    elec_overtime[run] = [None]*(len(wards)-2) # Array with element for each speciality
    elec_cancellations[run] = [None]*(len(wards)-2)
    elec_count[run] = [None]*len(wards) # Array with element for each ward

    for speciality in range((len(wards)-2)):
        elec_overtime[run][speciality] = [0]*(number_of_weeks + 1)
        elec_cancellations[run][speciality] = [0]*(number_of_weeks + 1)
    
    for ward in range(len(wards)):
        elec_count[run][ward] = [0]*7*(number_of_weeks + 1)
    
    run += 1


# Emerg patients
GA_rooms = ['GA1', 'GA2', 'GA3', 'GA4', 'GA5', 'GA6', 'GA7']

emerg_overtime = [None]*(runs+1)
surgeries_GA = [None]*(runs+1)
ex_deadlines = [None]*(runs+1)
emerg_count = [None]*(runs+1)

run = 1
for i in range(runs):
    emerg_overtime[run] = [None]*(len(wards)-2)
    surgeries_GA[run] = [0]*(number_of_weeks + 1)
    ex_deadlines[run] = [0,0,0,0]
    emerg_count[run] = [None]*len(wards) # Array with element for each ward
    
    for pri in range(4):
        ex_deadlines[run][pri] = [0]*(number_of_weeks + 1)
    
    for speciality in range((len(wards)-2)):
        emerg_overtime[run][speciality] = [0]*(number_of_weeks + 1)
    
    for ward in range(len(wards)):
        emerg_count[run][ward] = [0]*7*(number_of_weeks + 2)
    
    run += 1
    
    
run = 0
# Creating arrays
for elec_patient_list in total_elec_patient_list:
    run += 1
    for patient in elec_patient_list:
        for i in range(len(wards)):
            if patient.speciality == wards[i]: 
                elec_cancellations[run][i][patient.weeknr] += patient.cancellation
        
        for i in range(len(wards)-2):
            if patient.speciality == wards[i]: 
                elec_overtime[run][i][patient.weeknr] += patient.overtime
                #if patient.arrival_time[0] == 1:
                    #print('Patient %d speciality is %s (%s), arrival day is %s and LOS in ward is %d' %(patient.id ,str(patient.speciality), wards[i], str(patient.arrival_time[0]), patient.LOS_ward))
                if patient.discharge_time != None:
                    for j in range(patient.discharge_time[0] - patient.arrival_time[0]):
                        if (patient.arrival_time[0] + j) < number_of_weeks*7:
                            elec_count[run][i][patient.arrival_time[0] + j] += 1
                        #if patient.arrival_time[0] == 1:
                            #print('Adding day ', patient.arrival_time[0] + j)
                            #print('count day %d is %d'%((patient.arrival_time[0] + j), elec_count[i][patient.arrival_time[0] + j]))
                    
        for i in range(patient.LOS_ICU):
            elec_count[run][6][patient.arrival_time[0] + i] += 1
        
        for i in range(patient.LOS_TOV):
            elec_count[run][7][patient.arrival_time[0] + i] += 1


run = 0
for emerg_patient_list in total_emerg_patient_list:
    run += 1
    for patient in emerg_patient_list:
        
        if patient.surgery_room in GA_rooms:
            surgeries_GA[run][patient.weeknr] += 1
            
        if patient.reached_threshold > 0:
            ex_deadlines[run][patient.old_surgery_pri][patient.weeknr] += 1
    
        for i in range(len(wards)-2):
            if patient.speciality == wards[i]: 
                emerg_overtime[run][i][patient.weeknr] += patient.overtime
                if patient.discharge_time != None:
                    for j in range(patient.discharge_time[0] - patient.arrival_time[0]):
                        #print('Patient %d arrived day %d and stays for %d days' % (patient.id, patient.arrival_time[0], patient.LOS_ward))
                        #print('Simulation done at ', number_of_weeks*7)
                        #print(patient.arrival_time[0] + j)
                        if (patient.arrival_time[0] + j) < number_of_weeks*7:
                            emerg_count[run][i][patient.arrival_time[0] + j] += 1
                else:
                    for j in range(number_of_weeks*7 - patient.arrival_time[0]):
                        emerg_count[run][i][patient.arrival_time[0] + j] += 1
                    
        for i in range(patient.LOS_ICU):
            emerg_count[run][6][patient.arrival_time[0] + i] += 1
        
        for i in range(patient.LOS_TOV):
            emerg_count[run][7][patient.arrival_time[0] + i] += 1


# Writing to file
KPI_elec = hb.add_sheet('Elec KPI')

# 1st row elec_KPI
KPI_elec.write(0, 0, 'Run')
KPI_elec.write(0, 1, 'Week')

KPI_elec.write(0, 2, 'Overtime:')
c = 3
for i in range(len(wards)-2):
    KPI_elec.write(0, c, wards[i])
    c += 1

KPI_elec.write(0, 9, 'Cancellations:')
c = 10
for i in range(len(wards)-2):
    KPI_elec.write(0, c, wards[i])
    c += 1
    
KPI_elec.write(0, 17, 'Run count')
KPI_elec.write(0, 18, 'Count night')
c = 19
for i in range(len(wards)):
    KPI_elec.write(0, c, wards[i]+' bed')
    c += 1

    
# Other rows
row = 1
run = 1
for k in range(runs):
    value = 1
    for j in range(number_of_weeks):
        KPI_elec.write(row, 0, run)
        KPI_elec.write(row, 1, value)
        c = 3
        for i in range(len(wards)-2):
            # Overtime per speciality per week
            #print('Run %d, speciality %s, row %d, value %d' %(run, wards[i],row, value))
            KPI_elec.write(row, c, elec_overtime[run][i][value])
            # Cancellations per speciality per week
            KPI_elec.write(row, c + 7, elec_cancellations[run][i][value])
            c += 1
        row += 1
        value += 1
    run += 1

row = 1
run = 1
for k in range(runs):
    value = 1
    for j in range(7*number_of_weeks):
        KPI_elec.write(row, 17, run)
        KPI_elec.write(row, 18, value)
        c = 19
        for i in range(len(wards)):
            # Count per speciality per night
            KPI_elec.write(row, c, elec_count[run][i][value])
            c += 1
        row += 1
        value += 1
    run += 1




KPI_emerg = hb.add_sheet('Emerg KPI')
    
# 1st row emerg_KPI
KPI_emerg.write(0, 0, 'Run')
KPI_emerg.write(0, 1, 'Week')

KPI_emerg.write(0, 2, 'Overtime:')
c = 3
for i in range(len(wards)-2):
    KPI_emerg.write(0, c, wards[i])
    c += 1

KPI_emerg.write(0, 9, 'Surgeries in elective rooms per week')
KPI_emerg.write(0, 10, 'Exceeded deadlines:')
KPI_emerg.write(0, 11, 'Pri 1')
KPI_emerg.write(0, 12, 'Pri 2')
KPI_emerg.write(0, 13, 'Pri 3')
    
KPI_emerg.write(0, 15, 'Run count')
KPI_emerg.write(0, 16, 'Count night')
c = 17
for i in range(len(wards)):
    KPI_emerg.write(0, c, wards[i])
    c += 1

    
# Other rows
r = 1
run = 1
for k in range(runs):
    value = 1
    for i in range(number_of_weeks):
        KPI_emerg.write(r, 0, run)
        KPI_emerg.write(r, 1, value)
        KPI_emerg.write(r, 9, surgeries_GA[run][value])
        KPI_emerg.write(r, 11, ex_deadlines[run][1][value])
        KPI_emerg.write(r, 12, ex_deadlines[run][2][value])
        KPI_emerg.write(r, 13, ex_deadlines[run][3][value])
        
        c = 3
        for j in range(len(wards)-2):
            # Overtime per speciality per week
            KPI_emerg.write(r, c, emerg_overtime[run][j][value])
            c += 1
        r += 1
        value += 1
    run += 1

r = 1
run = 1
for k in range(runs):
    value = 1
    for i in range(7*number_of_weeks):
        KPI_emerg.write(r, 15, run)
        KPI_emerg.write(r, 16, value)
        c = 17
        for j in range(len(wards)):
            # Count per speciality per night
            KPI_emerg.write(r, c, emerg_count[run][j][value])
            c += 1
        r += 1
        value += 1
    run += 1
 


            
#Adding sheet for elective patients
elec_patients = hb.add_sheet('elec_patients')

elec_patients.write(0, 0, 'Run number')

elec_patients.write(0, 1, 'Elec patient ID')
elec_patients.write(0, 2, 'Arrival week')
elec_patients.write(0, 3, 'Arrival day')
elec_patients.write(0, 4, 'Arrival time')

elec_patients.write(0, 5, 'Patient group')
elec_patients.write(0, 6, 'Speciality')

elec_patients.write(0, 7, 'Surgery priority')
elec_patients.write(0, 8, 'Surgery day')
elec_patients.write(0, 9, 'Surgery time')
elec_patients.write(0, 10, 'Surgery room')
elec_patients.write(0, 11, 'Surgery duration')
elec_patients.write(0, 12, 'Median surgery duration')
elec_patients.write(0, 13, 'Surgery done at')
elec_patients.write(0, 14, 'Cleaning time')
elec_patients.write(0, 15, 'Surgery overtime')
elec_patients.write(0, 16, 'Surgery cancellation')

elec_patients.write(0, 17, 'Start night LOS in ward')
elec_patients.write(0, 18, 'LOS in ward')
elec_patients.write(0, 19, 'LOS in ICU')
elec_patients.write(0, 20, 'LOS in TOV')
elec_patients.write(0, 21, 'Discharge day')
elec_patients.write(0, 22, 'Discharge time')


count = 0
run = 0

# Writing elective patients to file
for elec_patient_list in total_elec_patient_list:
    
    run += 1
        
    for elec_patient in elec_patient_list:
        count += 1
        
        elec_patients.write(count, 0, run)
        elec_patients.write(count, 1, elec_patient.id)
        elec_patients.write(count, 2, elec_patient.weeknr)
        elec_patients.write(count, 3, int(elec_patient.arrival_time[0]))
        
        if len(str(elec_patient.arrival_time[1])) == 1 and len(str(elec_patient.arrival_time[2])) == 1:
            elec_patients.write(count, 4, '0' + str(elec_patient.arrival_time[1]) + ':0' + str(elec_patient.arrival_time[2]))
        elif len(str(elec_patient.arrival_time[1])) == 1:
            elec_patients.write(count, 4, '0' + str(elec_patient.arrival_time[1]) + ':' + str(elec_patient.arrival_time[2]))
        elif len(str(elec_patient.arrival_time[2])) == 1:
            elec_patients.write(count, 4, str(elec_patient.arrival_time[1]) + ':0' + str(elec_patient.arrival_time[2]))
        else:
            elec_patients.write(count, 4, str(elec_patient.arrival_time[1]) + ':' + str(elec_patient.arrival_time[2]))
        
        elec_patients.write(count, 5, str(elec_patient.patient_group))
        elec_patients.write(count, 6, str(elec_patient.speciality))
        
        elec_patients.write(count, 7, elec_patient.priority)
        
        if elec_patient.surgery_time != None:
            elec_patients.write(count, 8, int(elec_patient.surgery_time[0]))
        
            if len(str(elec_patient.surgery_time[1])) == 1 and len(str(elec_patient.surgery_time[2])) == 1:
                elec_patients.write(count, 9, '0' + str(elec_patient.surgery_time[1]) + ':0' + str(elec_patient.surgery_time[2]))
            elif len(str(elec_patient.surgery_time[1])) == 1:
                elec_patients.write(count, 9, '0' + str(elec_patient.surgery_time[1]) + ':' + str(elec_patient.surgery_time[2]))
            elif len(str(elec_patient.surgery_time[2])) == 1:
                elec_patients.write(count, 9, str(elec_patient.surgery_time[1]) + ':0' + str(elec_patient.surgery_time[2]))
            else:
                elec_patients.write(count, 9, str(elec_patient.surgery_time[1]) + ':' + str(elec_patient.surgery_time[2]))
        else:
            elec_patients.write(count, 16, elec_patient.cancellation)
    
        elec_patients.write(count, 10, str(elec_patient.surgery_room))
        elec_patients.write(count, 11, elec_patient.surgery_duration)
        elec_patients.write(count, 12, float(elec_patient.med_sur_dur))
        if elec_patient.surgery_done != None:
            
            if len(str(elec_patient.surgery_done[1])) == 1 and len(str(elec_patient.surgery_done[2])) == 1:
                elec_patients.write(count, 13, '0' + str(elec_patient.surgery_done[1]) + ':0' + str(elec_patient.surgery_done[2]))
            elif len(str(elec_patient.surgery_done[1])) == 1:
                elec_patients.write(count, 13, '0' + str(elec_patient.surgery_done[1]) + ':' + str(elec_patient.surgery_done[2]))
            elif len(str(elec_patient.surgery_done[2])) == 1:
                elec_patients.write(count, 13, str(elec_patient.surgery_done[1]) + ':0' + str(elec_patient.surgery_done[2]))
            else:
                elec_patients.write(count, 13, str(elec_patient.surgery_done[1]) + ':' + str(elec_patient.surgery_done[2]))
            
        elec_patients.write(count, 14, elec_patient.cleaning_time)
        elec_patients.write(count, 15, int(elec_patient.overtime))
        
        elec_patients.write(count, 17, int(elec_patient.start_LOS_ward))
        elec_patients.write(count, 18, int(elec_patient.LOS_ward))
        elec_patients.write(count, 19, int(elec_patient.LOS_ICU))
        elec_patients.write(count, 20, int(elec_patient.LOS_TOV))
    
        if elec_patient.discharge_time != None:  
            elec_patients.write(count, 21, elec_patient.discharge_time[0])
            if len(str(elec_patient.discharge_time[1])) == 1 and len(str(elec_patient.discharge_time[2])) == 1:
                elec_patients.write(count, 22, '0' + str(elec_patient.discharge_time[1]) + ':0' + str(elec_patient.discharge_time[2]))
            elif len(str(elec_patient.discharge_time[1])) == 1:
                elec_patients.write(count, 22, '0' + str(elec_patient.discharge_time[1]) + ':' + str(elec_patient.discharge_time[2]))
            elif len(str(elec_patient.discharge_time[2])) == 1:
                elec_patients.write(count, 22, str(elec_patient.discharge_time[1]) + ':0' + str(elec_patient.discharge_time[2]))
            else:
                elec_patients.write(count, 22, str(elec_patient.discharge_time[1]) + ':' + str(elec_patient.discharge_time[2]))


#Adding sheet for emergency patients
emerg_patients = hb.add_sheet('emerg_patients')

emerg_patients.write(0, 0, 'Run number')

emerg_patients.write(0, 1, 'Emerg patient ID')
emerg_patients.write(0, 2, 'Arrival week')
emerg_patients.write(0, 3, 'Arrival weekend? 1=y')
emerg_patients.write(0, 4, 'Arrival day')
emerg_patients.write(0, 5, 'Arrival time')
emerg_patients.write(0, 6, 'Admission day')
emerg_patients.write(0, 7, 'Admission time')

emerg_patients.write(0, 8, 'Speciality')

emerg_patients.write(0, 9, 'Surgery? 1=y')
emerg_patients.write(0, 10, 'Surgery priority')
emerg_patients.write(0, 11, 'Old surgery priority')
emerg_patients.write(0, 12, 'Surgery registration day')
emerg_patients.write(0, 13, 'Number of times threshold has been reached')
emerg_patients.write(0, 14, 'Surgery registration time')
emerg_patients.write(0, 15, 'Surgery week')
emerg_patients.write(0, 16, 'Surgery weekend?`1=y')
emerg_patients.write(0, 17, 'Surgery day')
emerg_patients.write(0, 18, 'Surgery time')
emerg_patients.write(0, 19, 'Surgery room')
emerg_patients.write(0, 20, 'Surgery duration')
emerg_patients.write(0, 21, 'Median surgery duration')
emerg_patients.write(0, 22, 'Surgery done at')
emerg_patients.write(0, 23, 'Surgery waiting time')
emerg_patients.write(0, 24, 'Overtime')
emerg_patients.write(0, 25, 'Cleaning time')

emerg_patients.write(0, 26, 'Start LOS in ward')
emerg_patients.write(0, 27, 'LOS in ward')
emerg_patients.write(0, 28, 'LOS in ICU')
emerg_patients.write(0, 29, 'LOS in TOV')
emerg_patients.write(0, 30, 'Discharge day')
emerg_patients.write(0, 31, 'Discharge time')


count = 0
run = 0

# Writing emergency patients to file
for emerg_patient_list in total_emerg_patient_list:
    
    run += 1
    
    for emerg_patient in emerg_patient_list:
        count += 1
        
        emerg_patients.write(count, 0, run)
        
        emerg_patients.write(count, 1, emerg_patient.id)
        emerg_patients.write(count, 2, emerg_patient.weeknr)
        emerg_patients.write(count, 3, emerg_patient.arrivalWeekend)
        emerg_patients.write(count, 4, int(emerg_patient.arrival_time[0]))
    
        if len(str(emerg_patient.arrival_time[1])) == 1 and len(str(emerg_patient.arrival_time[2])) == 1:
            emerg_patients.write(count, 5, '0' + str(emerg_patient.arrival_time[1]) + ':0' + str(emerg_patient.arrival_time[2]))
        elif len(str(emerg_patient.arrival_time[1])) == 1:
            emerg_patients.write(count, 5, '0' + str(emerg_patient.arrival_time[1]) + ':' + str(emerg_patient.arrival_time[2]))
        elif len(str(emerg_patient.arrival_time[2])) == 1:
            emerg_patients.write(count, 5, str(emerg_patient.arrival_time[1]) + ':0' + str(emerg_patient.arrival_time[2]))
        else:
            emerg_patients.write(count, 5, str(emerg_patient.arrival_time[1]) + ':' + str(emerg_patient.arrival_time[2]))
        
        if emerg_patient.admission_time != None:
            
            emerg_patients.write(count, 6, int(emerg_patient.admission_time[0]))
        
            if len(str(emerg_patient.admission_time[1])) == 1 and len(str(emerg_patient.admission_time[2])) == 1:
                emerg_patients.write(count, 7, '0' + str(emerg_patient.admission_time[1]) + ':0' + str(emerg_patient.admission_time[2]))
            elif len(str(emerg_patient.admission_time[1])) == 1:
                emerg_patients.write(count, 7, '0' + str(emerg_patient.admission_time[1]) + ':' + str(emerg_patient.admission_time[2]))
            elif len(str(emerg_patient.admission_time[2])) == 1:
                emerg_patients.write(count, 7, str(emerg_patient.admission_time[1]) + ':0' + str(emerg_patient.admission_time[2]))
            else:
                emerg_patients.write(count, 7, str(emerg_patient.admission_time[1]) + ':' + str(emerg_patient.admission_time[2]))
        
        else:
            pass
        
        emerg_patients.write(count, 8, str(emerg_patient.speciality))
        
        if emerg_patient.surgery == 1:
            emerg_patients.write(count, 9, emerg_patient.surgery)
            emerg_patients.write(count, 10, emerg_patient.surgery_pri)
            
            if emerg_patient.old_surgery_pri > 0:
                emerg_patients.write(count, 11, emerg_patient.old_surgery_pri)
            else:
                pass
        
            if emerg_patient.surgery_reg_time != None:
                
                emerg_patients.write(count, 12, int(emerg_patient.surgery_reg_time[0]))
                
                if emerg_patient.reached_threshold > 0:
                    emerg_patients.write(count, 13, emerg_patient.reached_threshold)
                else:
                    pass
                
                if len(str(emerg_patient.surgery_reg_time[1])) == 1 and len(str(emerg_patient.surgery_reg_time[2])) == 1:
                    emerg_patients.write(count, 14, '0' + str(emerg_patient.surgery_reg_time[1]) + ':0' + str(emerg_patient.surgery_reg_time[2]))
                elif len(str(emerg_patient.surgery_reg_time[1])) == 1:
                    emerg_patients.write(count, 14, '0' + str(emerg_patient.surgery_reg_time[1]) + ':' + str(emerg_patient.surgery_reg_time[2]))
                elif len(str(emerg_patient.surgery_reg_time[2])) == 1:
                    emerg_patients.write(count, 14, str(emerg_patient.surgery_reg_time[1]) + ':0' + str(emerg_patient.surgery_reg_time[2]))
                else:
                    emerg_patients.write(count, 14, str(emerg_patient.surgery_reg_time[1]) + ':' + str(emerg_patient.surgery_reg_time[2]))
            
            if emerg_patient.surgery_time != None:
                
                emerg_patients.write(count, 15, emerg_patient.surgeryWeek)
                emerg_patients.write(count, 16, emerg_patient.surgeryWeekend)
                
                emerg_patients.write(count, 17, int(emerg_patient.surgery_time[0]))
        
                if len(str(emerg_patient.surgery_time[1])) == 1 and len(str(emerg_patient.surgery_time[2])) == 1:
                    emerg_patients.write(count, 18, '0' + str(emerg_patient.surgery_time[1]) + ':0' + str(emerg_patient.surgery_time[2]))
                elif len(str(emerg_patient.surgery_time[1])) == 1:
                    emerg_patients.write(count, 18, '0' + str(emerg_patient.surgery_time[1]) + ':' + str(emerg_patient.surgery_time[2]))
                elif len(str(emerg_patient.surgery_time[2])) == 1:
                    emerg_patients.write(count, 18, str(emerg_patient.surgery_time[1]) + ':0' + str(emerg_patient.surgery_time[2]))
                else:
                    emerg_patients.write(count, 18, str(emerg_patient.surgery_time[1]) + ':' + str(emerg_patient.surgery_time[2]))
            
                emerg_patients.write(count, 19, str(emerg_patient.surgery_room))
                emerg_patients.write(count, 20, emerg_patient.surgery_duration)
                emerg_patients.write(count, 21, emerg_patient.med_sur_dur)
                if emerg_patient.surgery_done != None:
                    
                    if len(str(emerg_patient.surgery_done[1])) == 1 and len(str(emerg_patient.surgery_done[2])) == 1:
                        emerg_patients.write(count, 22, '0' + str(emerg_patient.surgery_done[1]) + ':0' + str(emerg_patient.surgery_done[2]))
                    elif len(str(emerg_patient.surgery_done[1])) == 1:
                       emerg_patients.write(count, 22, '0' + str(emerg_patient.surgery_done[1]) + ':' + str(emerg_patient.surgery_done[2]))
                    elif len(str(emerg_patient.surgery_done[2])) == 1:
                        emerg_patients.write(count, 22, str(emerg_patient.surgery_done[1]) + ':0' + str(emerg_patient.surgery_done[2]))
                    else:
                        emerg_patients.write(count, 22, str(emerg_patient.surgery_done[1]) + ':' + str(emerg_patient.surgery_done[2]))
                    
                    emerg_patients.write(count, 23, int(emerg_patient.waiting_time)/60)
                    emerg_patients.write(count, 24, emerg_patient.overtime)
                    emerg_patients.write(count, 25, int(emerg_patient.cleaning_time))
            else:
                pass        
    
        emerg_patients.write(count, 26, int(emerg_patient.start_LOS_ward))
        emerg_patients.write(count, 27, int(emerg_patient.LOS_ward))
        emerg_patients.write(count, 28, int(emerg_patient.LOS_ICU))
        emerg_patients.write(count, 29, int(emerg_patient.LOS_TOV))
    
        if emerg_patient.discharge_time != None:
    
            emerg_patients.write(count, 30, int(emerg_patient.discharge_time[0]))
            
            if len(str(emerg_patient.discharge_time[1])) == 1 and len(str(emerg_patient.discharge_time[2])) == 1:
                emerg_patients.write(count, 31, '0' + str(emerg_patient.discharge_time[1]) + ':0' + str(emerg_patient.discharge_time[2]))
            elif len(str(emerg_patient.discharge_time[1])) == 1:
                emerg_patients.write(count, 31, '0' + str(emerg_patient.discharge_time[1]) + ':' + str(emerg_patient.discharge_time[2]))
            elif len(str(emerg_patient.discharge_time[2])) == 1:
                emerg_patients.write(count, 31, str(emerg_patient.discharge_time[1]) + ':0' + str(emerg_patient.discharge_time[2]))
            else:
                emerg_patients.write(count, 31, str(emerg_patient.discharge_time[1]) + ':' + str(emerg_patient.discharge_time[2]))
    
        else:
            pass


system_status = hb.add_sheet('Status')

system_status.write(0, 0, 'Night')
system_status.write(0, 1, 'Weeknr')
system_status.write(0, 2, 'Run')
system_status.write(0, 3, 'KGAS1 count')
system_status.write(0, 4, 'KGAS2 count')
system_status.write(0, 5, 'KGASA count')
system_status.write(0, 6, 'KURS count')
system_status.write(0, 7, 'KENS count')
system_status.write(0, 8, 'KKAS count')
system_status.write(0, 9, 'ICU count')
system_status.write(0, 10, 'TOV count')

r = 0
c = 0

for status_list in total_status_list:
    r+=1
    for i in range(len(status_list)):
        c+=1
        system_status.write(c, 0, status_list[i][0])
        system_status.write(c, 1, np.ceil(int(status_list[i][0]) / 7))
        system_status.write(c, 2, r)
        system_status.write(c, 3, status_list[i][1])
        system_status.write(c, 4, status_list[i][2])
        system_status.write(c, 5, status_list[i][3])
        system_status.write(c, 6, status_list[i][4])
        system_status.write(c, 7, status_list[i][5])
        system_status.write(c, 8, status_list[i][6])
        system_status.write(c, 9, status_list[i][7])
        system_status.write(c, 10, status_list[i][8])



waiting_times_week = [None]*3
average_wait_week = [None]*3

waiting_times_weekend = [None]*3
average_wait_weekend = [None]*3
average_wait = [None]*3

for i in range(3):
    waiting_times_week[i] = []
    waiting_times_weekend[i] = []

for emerg_patient_list in total_emerg_patient_list:
    for emerg_patient in emerg_patient_list:
        if emerg_patient.surgery_time != None and emerg_patient.weeknr not in warm_up_weeks:
            if emerg_patient.surgeryWeekend == 0:
                wait = waiting_times_week
            else:
                wait = waiting_times_weekend
            
            if emerg_patient.old_surgery_pri != 0:
                wait[emerg_patient.old_surgery_pri-1].append(emerg_patient.waiting_time)
            else:
                wait[emerg_patient.surgery_pri-1].append(emerg_patient.waiting_time)
        else:
            pass
#for i in range(len(waiting_times_week[0])):
    #print(waiting_times_week[0][i]/60)

print()
print('Waiting times simulated')
print('       Week       Weekend     All days      Number of surgeries average')


#for h in range(len(waiting_times_week)):
    #print('Pri %d list: %s ' %(h+1, str(waiting_times_week[h])))


          
for i in range(3):       
    average_wait_week[i] = (sum(waiting_times_week[i])/len(waiting_times_week[i]))/60
    average_wait_weekend[i] = (sum(waiting_times_weekend[i])/len(waiting_times_weekend[i]))/60
    average_wait[i] = ((sum(waiting_times_week[i])+sum(waiting_times_weekend[i]))/(len(waiting_times_week[i])+len(waiting_times_weekend[i])))/60
    average_surgeries = (len(waiting_times_week[i]) + len(waiting_times_weekend[i])) / ((number_of_weeks-len(warm_up_weeks))*runs)
    print('Pri %d  %f   %f     %f     %f' %(i+1, average_wait_week[i], average_wait_weekend[i], average_wait[i], average_surgeries))


real_pri1_week = 346.274752475248/60
real_pri1_weekend = 452.45/60
real_pri1 = 373.5992647/60

real_pri2_week = 1329.06849315068/60
real_pri2_weekend = 1652.96202531646/60
real_pri2 = 1414.932886/60


real_pri3_week = 4171.95294117647/60
real_pri3_weekend = 3637.94736842105/60
real_pri3 = 4074.394231/60


print()
print('Waiting times real')
print('       Week       Weekend     All days      Number of surgeries average')
print('Pri 1  %f   %f     %f     %f' %(real_pri1_week,real_pri1_weekend, real_pri1, 544/34))
print('Pri 2  %f   %f     %f     %f' %(real_pri2_week, real_pri2_weekend, real_pri2, 298/34))
print('Pri 3  %f   %f     %f     %f' %(real_pri3_week,real_pri3_weekend, real_pri3, 104/34))

print()
print('Difference waiting times')
print('Pri 1  %f   %f' %((average_wait_week[0] - real_pri1_week),(average_wait_weekend[0] - real_pri1_weekend)))
print('Pri 2  %f   %f' %((average_wait_week[1] - real_pri2_week),( average_wait_weekend[1] - real_pri2_weekend)))
print('Pri 3  %f   %f' %((average_wait_week[2] - real_pri3_week),(average_wait_weekend[2] - real_pri3_weekend)))




    
hb.save(str(results_file))


list = []
for emerg_patient_list in total_emerg_patient_list:
    for patient in emerg_patient_list:
        if patient.surgery_done != None:
            list.append(int(patient.waiting_time)/60)

print(np.amax(list))



