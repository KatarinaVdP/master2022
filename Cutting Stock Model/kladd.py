
MSnxi       = [1, 3, 5, 8]
MSnxi_dur   = [40, 13, 79, 2]

MSnxi       = [x for _,x in sorted(zip(MSnxi_dur,MSnxi))]
MSnxi_dur.sort(reverse=True)
MSnxi.reverse()


print(MSnxi)
print(MSnxi_dur)

MSi =[[5],[11,12]]
MSi[0].remove(4)
print(MSi)
