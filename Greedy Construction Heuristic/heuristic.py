import pandas as pd
import math 

class Slot:
    def __init__(self,room,day):
        self.day    =   day
        self.room   =   room
        self.specialty   = ''
        self.extended    = False
        self.fixed       = True
        self.weekend     = False
        self.totalTime   = 0
        self.plannedTime = 0

class MSS:
    def __init__(self, rooms, days):
        self.days   =   days
        self.rooms  =   rooms
        self.plan   =   [[0]*days]*rooms

def read_list(sheet, name):
    set =  sheet[name].values
    list = []
    for value in set:
        if not str(value) == "nan":
            list.append(value)
    return list

def read_matrix(sheet, prefix, days):
    matrix = []
    for i in range(days):
        column = sheet[prefix + str(i + 1)].values
        sublist = []
        for j in column:
            if not math.isnan(j):
                sublist.append(j)
        matrix.append(sublist)
    return matrix

def retrive_ScenarioData(fileName, nScenarios):
    QTransposeFound             =   False
    file                        =   open(fileName, 'r')
    scenariosMatrix             =   []

    for line in file:
        string_list         =   line.split()
        if string_list:
            if string_list[0] == ']' and QTransposeFound:
                QTransposeFound   =   False  
            if string_list[0] == 'Pi:':
                PI                  = float(string_list[1])
            if QTransposeFound:
                map_object              = map(int, string_list)
                list_of_integers        = list(map_object)
                scenariosMatrix.append(list_of_integers)

            if  string_list[0] == 'QTranspose:':
                QTransposeFound = True  
    return scenariosMatrix, PI

def retrieve_FirstStageSolution(file, days, rooms, specialties, regularTime, extendedTime):
    GammaFixPreFound            =   False
    LambdaFixPreFound           =   False
    mss                         =   MSS(rooms, days)
    file                        =   open(file, 'r')

    for line in file:
        if line == "]\n" and GammaFixPreFound == True :
            GammaFixPreFound    =   False

        if line == "]\n" and LambdaFixPreFound == True :
            LambdaFixPreFound   =   False

        if GammaFixPreFound:
            a_list              = line.split()
            map_object          = map(int, a_list)
            list_of_integers    = list(map_object)
        
            thisSpecialty       = list_of_integers[0]
            thisRoom            = list_of_integers[1]
            thisDay             = list_of_integers[2]
            thisValue           = list_of_integers[3]

            slot                = Slot(thisRoom, thisDay)
            slot.specialty      = specialties[thisSpecialty-1] 
            slot.totalTime      = regularTime
        
            mss.plan[thisRoom-1][thisDay-1] = slot

        if LambdaFixPreFound:
            a_list              = line.split()
            map_object          = map(int, a_list)
            list_of_integers    = list(map_object)
        
            thisSpecialty       = list_of_integers[0]
            thisRoom            = list_of_integers[1]
            thisDay             = list_of_integers[2]
            thisValue           = list_of_integers[3]

            slot                = Slot(thisRoom, thisDay)
            slot.specialty      = specialties[thisSpecialty-1] + "*"
            slot.extended       = True
            slot.totalTime      = regularTime + extendedTime
        
            mss.plan[thisRoom-1][thisDay-1] = slot

        if line == "GammaFixPre:  [\n":
            GammaFixPreFound    =   True

        if line == "LambdaFixPre:  [\n":
            LambdaFixPreFound    =   True

    for room in range(rooms):
        for day in range(days):
            if (day+1)%7 == 0 or (day+1)%7 == 6:
                slot = Slot(room+1, day)
                slot.weekend = True
                slot.specialty = '-'
                mss.plan[room][day-1] = slot
            
            if mss.plan[room][day] == 0:
                slot = Slot(room+1, day+1)
                slot.specialty = '#'
                mss.plan[room][day] = slot
                slot.totalTime = regularTime
    
    return mss

#def create_Patterns(groupsInSpecialty, surgeryDuration):
    #alle kombinasjoner av antall fra hver gruppe
    #max antall gupper mulig i en pattern = max av floorene
    #floor(maxTime/SugeryDuration) gir maks antallet operasjoner av gruppen å inkudere i mønsterene
    #lag en liste som inneholder floor-antall av hver gruppe
    #lag kombinasjoner fra listen fra ett til maxfloor elementer fra denne listen
    #fjern alle mønstre som bryter med saltid
    #fjern alle symmetriske mønstre

#def valid_Patterns():

def main(input_FileName, firstStageSolution_FileName, scenarios_FileName):
    nScenarios  =   10
    seed        =   1
    nGroups     =   25

    overview = pd.read_excel(input_FileName, sheet_name='Overview')  

    nDays       =   int(overview["Planning days"].values[0])  
    # ----- Reading Sets -----
    G           =   read_list(overview, "Surgery groups")               #Surgery Groups
    W           =   read_list(overview, "Wards")                        #Wards
    S           =   read_list(overview, "Specialties")                  #Specialties
    R           =   read_list(overview, "Operating rooms")              #Operating Rooms 
    # ----- Reading Subsets -----
    GS_specialty =  read_list(overview, "Specialty")                     #Surgery groups to each speciality
    RS_spec     =   read_list(overview, "Spec to OR")                     #Room to Specialty to each speciality
    RS_rooms    =   read_list(overview, "OR to spec")                     #Room to Specialty to each speciality 
    # ----- Reading Parameters -----
    FF          =   float(overview["Flexible share"].values[0])           #Flexible Share
    E           =   int(overview["Extended time"].values[0])              #Extended time
    TC          =   int(overview["Cleaning time"].values[0])              #Cleaning Time
    I           =   int(overview["Cycles in PP"].values[0])               #Cycles in Planning Period
    B           =   read_matrix(overview,"B",nDays)                     #Bedward Capacity
    H           =   read_matrix(overview, "H", nDays)                   #Opening hours
    K           =   read_matrix(overview,"K",nDays)                     #Team Capacity per day
    L           =   read_list(overview,"Surgery duration")              #Surgery uration
    M_L         =   read_list(overview,"Max long days")                 #Max long days
    T           =   read_list(overview,"Target Troughput")
    Co          =   [element+TC for element in L]
    Qtranspose, PI = retrive_ScenarioData(scenarios_FileName,nScenarios) #Scenarios and probability of occurance
    #----- Other variables -----
    nRooms      =   len(R)
    nWards      =   len(W)
    nSpecialties =  len(S)
    H_0          =  H[1][1]                                             #Opening hours a regular day
    #----- Initializing the MSS -----
    mss         = retrieve_FirstStageSolution(firstStageSolution_FileName, nDays, nRooms, S, 450, E)
    mss_table   = [['']*nDays]*nRooms
    for room in range(nRooms):
        for day in range(nDays):
            if mss.plan[room][day] != 0:
                mss_table[room][day]=mss.plan[room][day].specialty

    print(mss_table)
    print(Qtranspose)

pathName                        =   "Greedy Construction Heuristic/Input/"
input_FileName                  =   pathName +"model_input.xlsx"
firstStageSolution_FileName     =   pathName + "First Stage Solutions/"+"FirstStageSolution_25_groups_1_scen1_0.1_flex_10_sec.txt"
scenarios_FileName              =   pathName + "Scenarios/"+"Q_groups_25_scenarios_10_Poisson_1.txt"

main(input_FileName, firstStageSolution_FileName, scenarios_FileName)

