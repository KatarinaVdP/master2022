from math import ceil
import pyomo.environ as pyo
import pandas as pd
from sympy import S
import xlwt
from xlwt import Workbook
from itertools import cycle
import statistics
import read_model_input



model = pyo.AbstractModel()

#--------- Declaration of sets -----------
model.W     =   pyo.Set()                           #   W       =   Wards, index w
model.S     =   pyo.Set()                           #   S       =   Specialties, index s
model.G     =   pyo.Set()                           #   G       =   Surgery groups, index g
model.GW    =   pyo.Set(model.W, domain=model.G)    #   G^W_w   =   Surgery groups that can receive postoperative care at ward w, indexed g
model.GS    =   pyo.Set(model.S, domain=model.G)    #   G^S_s   =   Surgery groups that can receive treatment from specialty s, indexed g     
model.R     =   pyo.Set()                           #   R       =   ORs, index r
model.RS    =   pyo.Set(model.S, domain=model.R)    #   R^S_s   =   ORs suitable for specialty s, indexed r
model.RG    =   pyo.Set(model.G, domain=model.R)    #   R^G_g   =   ORs suitable for group g, indexed r
model.D     =   pyo.Set()                           #   D       =   Days in planning period, indexed d
model.C     =   pyo.Set()                           #   C       =   Scenarios, index c

#--------- Declaration of parameters -----------
model.Pi    =   pyo.Param(model.C)                  #   Pi_c    =   Probability of scenario c occurring
model.Co    =   pyo.Param(model.G)                  #   C_g     =   Unit cost of not meeting the demand of surgery group g
model.TC    =   pyo.Param()                         #   T^C     =   Cleaning time post surgery
model.L     =   pyo.Param(model.G)                  #   L_g     =   Surgery duration of a patient in surgery group g
model.F     =   pyo.Param()                         #   F       =   Maximum percentage of flexible number of slots
model.N     =   pyo.Param(model.D)                  #   N_d     =   Total number of available ORs on day d
model.U     =   pyo.Param(model.S)                  #   U^X_d   =   Maximum number of times a specialty s may extend its opening hours during a cycle
model.I     =   pyo.Param()                         #   I       =   Number of cycles in the planning horizon
model.K     =   pyo.Param(model.S, model.D)         #   K_sd    =   Number of surgical teams from specialty s available on day d
model.H     =   pyo.Param(model.D)                  #   H_d     =   Default amount of time available in a slot if it is assigned on a day d
model.E     =   pyo.Param()                         #   E       =   Additional time available if a slot’s opening hours are extended
model.Q     =   pyo.Param(model.G,model.C)          #   Q_gc    =   Number of patients from surgery group g in line for surgery in scenario c
model.P     =   pyo.Param(model.G,model.W,model.D)  #   P_gwd   =   Probability that a patient from surgery group g occupies a bed in ward w, on the night d days after surgery
model.J     =   pyo.Param(model.W)                  #   J_w     =   Maximum number of nights a patient may stay in ward w
model.B     =   pyo.Param(model.W,model.D)          #   B_wd    =   Number of available beds at ward w on the night following day d

"--------- Decision variables -----------"
model.gamma     =   pyo.Var(model.S, model.R, model.D, domain=pyo.Binary)                           # 1 if specialty s is assigned a fixed slot in room r on day d
model.lamda     =   pyo.Var(model.S, model.R, model.D, domain=pyo.Binary)                           # 1 if specialty s extends opening hours in room r on day d
model.delta     =   pyo.Var(model.S, model.R, model.D, model.C, domain=pyo.Binary)                  # 1 if specialty s is assigned a flexible slot in room r on day d in scenario c
model.x         =   pyo.Var(model.S, model.R, model.D, model.C, domain=pyo.NonNegativeIntegers)     # Patients from surgery group g operated in room r on day d in scenario c
model.a         =   pyo.Var(model.G, model.C, domain=pyo.Binary)                                    # Patients from surgery group g waiting in line, but not scheduled for surgery in scenario c
model.v         =   pyo.Var(model.W, model.D, domain=pyo.NonNegativeReals)                          # Expected number of occupied beds in ward w on the night following day d in the next ...
                                                                                                    # ...planning period, by patients operated in the current planning period

input_file = "Old Model/Input/input_model.dat"
instance = model.create_instance(input_file)
print("Instance created in MIP model")

"--------- Objective function ----------"
def objective_rule(m):                                                                              # Is the objective function, and minimizes the total expected cost of unmet demand.
    return sum(m.Pi[c] *(sum(m.Co[g]*m.a[g,c] for g in m.G)) for c in m.C)
model.OBJ = pyo.Objective(rule=objective_rule, sense=pyo.minimize)

"--------- Constraints ----------"
def PercentFixedRooms_rule(m):                                  # A.2                                       # Ensures that the percentage of flexible slots is not exceeded.                                                                        # Ensures a minimum percentage of fixed slots.
    return  sum(sum(sum(m.gamma[s,r,d] for d in m.D) for r in m.R) for s in m.S) - ceil((1-m.F)*sum(m.N[d] for d in m.D)) >= 0
model.PercentFixedRooms_Constraint    =  pyo.Constraint(rule=PercentFixedRooms_rule)

def LongDaysLegal_rule(m,s,r,d):                                # A.3                                       # Ensures that a speciality can only extend a slot if it is assigned to that slot in the fixed schedule.
    return  m.lamda[s,r,d]   <=  m.gamma[s,r,d]

for s in range(model.S):   
    model.LongDaysLegal_Constraint  =   pyo.Constraint(model.S,model.RS[s],model.D,rule=LongDaysLegal_rule)

def LongDaysMax_rule(m,s):                                      # A.4                                       # Ensures that the number of extended slots on a given day is not greater than this day's maximum.
    return  sum(sum(m.lamda[s,r,d] for d in m.D) for r in m.RS[s])  <=  m.U
model.LongDaysMax_Constraint    =   pyo.Constraint(model.S,rule=LongDaysMax_rule)

def NoRoomDoubleBooking_rule(m,r,d,c):                          # A.5                                       # Ensures that no ORs are double booked.
    return  sum(m.gamma[s,r,d]  +   m.delta[s,r,d,c]    for s in m.S)   <=  1
for s in model.RS:
    model.NoRoomDoubleBooking_Constraint    =   pyo.Constraint(model.RS[s],model.D,model.C,rule=NoRoomDoubleBooking_rule)

def NoTeamDoubleBooking_rule(m,r,d,c):                          # A.6                                       # Ensures that no speciality is assigned more ORs than they have teams available on that day.
    return  sum(m.gamma[s,r,d]  +   m.delta[s,r,d,c]    for s in m.S)
for s in model.RS:
    model.NoTeamDoubleBooking_Constraint    =   pyo.Constraint(model.RS[s],model.D,model.C,rule=NoTeamDoubleBooking_rule)

def TotalRoomsInUse_rule(m,d,c):                                # A.7                                       # Ensures that we can not assign more ORs than there are ORs available each day.
    return  sum((m.gamma[s,r,d] +   m.delta[s,r,d,c]    for r in m.R)for s in m.S)  <=  m.N[d]
model.TotalRoomsInUse_Constraint    =   pyo.Constraint(model.D,model.C,rule=TotalRoomsInUse_rule)

def AvalibleTimeInRoom_rule(m,s,r,d,c):                         # A.8                                       # Ensures that the total planned operating time in a slot does not exceed the slot's available time (no planned overtime). The constraint also ensures that patients can only be planned for surgery in slots assigned to the speciality that their surgery group belongs to.
    return  sum((m.L[g]+m.TC)*m.x[g,r,d,c]  -   m.H[d]*(m.gamma[s,r,d]+m.delta[s,r,d,c]) -   m.E*m.lamda[s,r,d]  for g in m.GS) <=  0
for s in model.RS:
    model.AvalibleTimeInRoom_Constraint =   pyo.Constraint(model.S,model.RS[s],model.D,model.C,rule=AvalibleTimeInRoom_rule)

def Demand_rule(m,g,c):                                         # A.9                                       # Keeps track of the unmet demand of surgery group g in scenario c through the variable a_gc
    return  sum(sum(m.x[g,r,d,c]    for d in m.D)   for r in m.R)    +   m.a[g,c]   ==   m.Q[g,c]
model.Demand_Constraint =   pyo.Constraint(model.G,model.C,rule=Demand_rule)

def OnlyFlexibleIfOperationScheduled_rule(m,r,d,c):              # A.10                                      # Ensure that a flexible slot is only assigned to a specialty if there is at least one planned operation in that slot.
    return  sum(m.delta[s,r,d,c]    for s in m.S)   <=  sum(m.x[g,r,d,c]    for g in m.G)
model.OnlyFlexibleIfOperationScheduled_Constraint   =   pyo.Constraint(model.R,model.D,model.C,rule=OnlyFlexibleIfOperationScheduled_rule)

def BedOccupationCapacity_rule(m,w,d,c):                        # A.11                                      # Ensures the expected bed utilization on each ward and night does not exceed the number of bed available. This constraint takes into account the expected number of beds occupied by patients operated in the previous period.
    return  sum(sum(sum(m.P[w,g,d-dd+1]*m.x[g,r,dd,c]   for dd in range(max(1,d+len(m.D)+1-m.J[w]))) for r in m.R)  for g in m.GW[w])  <=  m.B[w,d]    -   m.v[w,d]
model.BedOccupationCapacity_Constraint  =   pyo.Constraint(model.W,model.D,model.C,rule=BedOccupationCapacity_rule)

def BedOccupationBoundaries_rule(m,w,d):                        # A.12                                      # Keep track of the expected number of beds occupied by patients operated in this period in a ward on the night following day d, in the next period.
    return  sum(m.Pi[c]* sum(sum(sum(m.P[w,g,d + len(m.D)+1-dd] * m.x[g,r,dd,c]    for dd in range(1,d+len(m.D)+1-m.J[w])   )  for r in m.R)   for g in m.GW[w]) for c in m.C) == m.v[w,d]
for w in model.J:
    model.BedOccupationBoundaries_Constraint    =   pyo.Constraint(model.W,model.J[w],rule=BedOccupationBoundaries_rule)

def cyclic_count(d, nDays, cycles):
    return nDays/cycles +   d

def RollingFixedSlotCycles_rule(m,s,r,d):                       # A.13                                      # Ensures that fixed slots repeat themselves in two-week cycles throughout the planning period.
    return  m.gamma[s,r,d]  ==  m.gamma[s,r,cyclic_count(d,len(m.D),m.I)]
model.RollingFixedSlotCycles_Constraint  ==  pyo.Constraint(model.S,model.RS,range(1,len(model.D)-len(model.D)/model.I+1),rule=RollingFixedSlotCycles_rule)

def RollingLongDaysCycles_rule(m,s,r,d):                        # A.14                                      # Ensures that long days repeat themselves in two-week cycles throughout the planning period.
    return m.lamda[s,r,d]   ==  m.lamda[s,r,cyclic_count(d,len(m.D),m.I)]
model.RollingLongDaysCycles_Constraint  ==  pyo.Constraint(model.S,model.RS,range(1,len(model.D)-len(model.D)/model.I+1),rule=RollingLongDaysCycles_rule)

"--------- Create instance and run ----------"



opt = pyo.SolverFactory('gurobi', solver_io="python", PoolSolutions=5, PoolSearchMode=2)

#input_file = "input_file_prosjektoppgave.dat"
#instance = model.create_instance(input_file)

#print("Instance created")

obj_values = []
running_time = []
run_time = 0
print("Solving now.........")
for i in range(360):
    run_time += 10
    opt.options["TimeLimit"] = 10
    if i==0:
        results = opt.solve(instance, warmstart = False)
    else:
        results = opt.solve(instance, warmstart=True)
    running_time.append(run_time)
    print("h")
    print(pyo.value(instance.OBJ))
    obj_values.append(pyo.value(instance.OBJ))
    print(str(pyo.value(instance.OBJ)))
    print("Time: %d, Value: %s" % (run_time, str(pyo.value(instance.OBJ))))