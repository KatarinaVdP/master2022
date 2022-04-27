import random
import numpy as np

levels = list(range(1, 4)) #levels blir følgende: levels = [1,2,3]
level_iters = [25,25,25]
swap_types = ['fix', 'ext', 'flex']
level_probs = [[0.5, 0.25, 0.25],[0.25, 0.5, 0.25],[0.25, 0.25, 0.5]]


print("{0:<15}".format("Temp level"), end="")
print("{0:<15}".format("Temp iter"),end="")
print("{0:<15}".format("Swap type"))
for level in levels:
        iter = 1
        while iter <= level_iters[level-1]:
            swap_type = np.random.choice(swap_types, p = level_probs[level-1])
            level_str = str(level)+"/"+str(len(levels))
            iter_str = str(iter)+"/"+str(level_iters[level-1])
            print("{0:<15}".format(level_str), end="") 
            print("{0:<15}".format(iter_str),end="")
            print("{0:<15}".format(swap_type))
            iter+=1