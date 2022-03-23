
def sort_list_by_another(list_to_sort,list_to_sort_by, decending=True):
    list_to_sort  =   [x for _,x in sorted(zip(list_to_sort_by,list_to_sort))]
    list_to_sort_by.sort(reverse=decending)
    list_to_sort.reverse()
    return list_to_sort, list_to_sort_by

def sort_MS_after_duration(input_dict,MSi,MSi_dur,decending=True):
    for s in input_dict["Si"]:
        MSi_sorted_s, MSi_dur_sorted_s  =   sort_list_by_another(MSi[s],MSi_dur[s],decending=True)
        MSi[s]=MSi_sorted_s
        MSi_dur[s]=MSi_dur_sorted_s
    return MSi, MSi_dur

"""MSi_test       = [[1, 3, 7], [5, 8, 9]]
MSi_dur_test   = [[40, 13, 53], [79, 2, 51]]
dict_test={}
dict_test["Si"]=[0,1]
MSi_test, MSi_dur_test =sort_MS_after_duration(dict_test, MSi_test,MSi_dur_test)
print(MSi_test)
print(MSi_dur_test)"""


list_1=[[1,2,3,4],[]]
list_2=[]
list_3=[0]
list_4=[-1]

if list_1[1]:
    print('1 1')
else:
    print('1 0')

if list_2:
    print('2 1')
else:
    print('2 0')

if list_3:
    print('3 1')
else:
    print('3 0')

if list_4:
    print('4 1')
else:
    print('4 0')


if 16 in [16, 14]:
    print('yes')