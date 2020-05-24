
import numpy as np
from numpy import random 
import copy
import matplotlib.pyplot as plt
import scipy
from scipy.stats import cauchy
import matplotlib.pyplot as plt 


def main():

    k_max = 1000
    m = 100
    cont = scipy.stats.rv_continuous(a=1,b=100)
    cauchy(cont)
    rv = cauchy.interval(.99)#(cauchy.rvs(loc=0,scale=1,size=5))
  
    print (rv)
    '''
    population = init_POP(m)
    population_final = NXT_GEN(k_max,population,m)
    
    
def init_POP(pop_size):
    return np.zeros((1,10))

def selection(POP,m): # Truncation
    temp = np.zeroes((m,1))
    for i in range(m):
        temp[i] = objective(POP[i])
    obj = sorted(temp)
    key = sorted(range(len(temp)), key=lambda k: temp[k])
    parents = []
    for ii in range(m/3):
        parents[len(parents):] = POP[key[ii]]

    return parents

def cross_over(parents,m):
    return child

def mutant(child):
    return child

def NXT_GEN(k_max,POP,pop_size):
    for k in range(k_max):
        parents = selection(POP,pop_size)
        for p in range(len(parents)):
            children = cross_over(POP[p])
        POP = mutant(children)

    return POP

def objective(individual):
    return 0
    '''

if __name__ == '__main__':
    main()