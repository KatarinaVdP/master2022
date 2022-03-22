
MSnxi       = [1, 3, 5, 8]
MSnxi_dur   = [40, 13, 79, 2]

MSnxi       = [x for _,x in sorted(zip(MSnxi_dur,MSnxi))]
MSnxi_dur.sort(reverse=True)
MSnxi.reverse()


print(MSnxi)
print(MSnxi_dur)

MSi =[[],[11,12]]

if MSi[0]:
    print(' 0not empty')
elif not MSi[0]:
    print('0 empty')
    
if MSi[1]:
    print('1 not empty')
elif not MSi[1]:
    print('1 empty')