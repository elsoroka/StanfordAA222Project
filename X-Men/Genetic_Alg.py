
import numpy as np
from numpy import random 
import copy
import matplotlib.pyplot as plt
import scipy
from scipy.stats import cauchy
from scipy.stats import randint
import matplotlib.pyplot as plt 
import dictionary


def main():

    k_max = 1000
    pop_size = 2
    schedule = GenAlg(K_max=k_max,m=pop_size)  
    schedule.init_POP() 
    '''
    rv = randint.rvs(0,10,size = 10)
    '''

    
class GenAlg:

    def __init__(self,K_max=1000,m=100):
        self.K_max = K_max #max iteration
        self.POP_size = m
        self.courses = load_dataset('spring_2020_AA.csv')
        self.num_courses = len(self.courses[0])
        '''
        define dictionary of options
        option #, time slots, time/week,...
        days([m t w th f] 0 or 1),start time,...
        end time(in military)
        '''
        self.options = dictionary.options_dict()


    def init_POP(self):
        self.POP = []
        for p in range(self.POP_size):
            pop_p = []
            for c in range(len(self.courses[2])):
                if self.courses[2][c] == 50:
                    pop_p[len(pop_p):] = randint.rvs(0,29,size = 1)
                elif self.courses[2][c] == 80:
                    pop_p[len(pop_p):] = randint.rvs(30,43,size = 1)
                elif self.courses[2][c] == 100:
                    pop_p[len(pop_p):] = randint.rvs(44,63,size = 1)
                elif self.courses[2][c] == 110:
                    pop_p[len(pop_p):] = randint.rvs(64,75,size = 1)
                elif self.courses[2][c] == 150:
                    pop_p[len(pop_p):] = randint.rvs(76,85,size = 1)
                elif self.courses[2][c] == 160:
                    pop_p[len(pop_p):] = randint.rvs(86,92,size = 1)
                elif self.courses[2][c] == 220:
                    pop_p[len(pop_p):] = randint.rvs(93,100,size = 1)
                else:
                    print('error,',self.courses[2][c],'min not accounted for')
                    pop_p[len(pop_p):] = randint.rvs(1000,1001,size = 1)
            self.POP[len(self.POP):]=[pop_p]

    def NXT_GEN(self):
        for k in range(self.K_max):
            parents = self.selection()
            children = cross_over(parents)
            self.POP = mutant(children)

    def obj(self,POP_single): #fix later
        score = 0
        overlap = 100
        lunch = 10
        early = 50
        late = 75

        for i in range(self.num_courses):
            if POP_single != 1000 and POP_single != 1001:
                score += randint.rvs(0,100,size = 1)
        return score


    def selection(self): 
        '''Truncation'''
        m = self.POP_size
        temp = np.zeroes((m,1))
        for i in range(m):
            temp[i] = self.obj(POP[i])
            obj = sorted(temp)
            key = sorted(range(len(temp)), key=lambda k: temp[k])
            parents = []
            for ii in range(m/3):
                parents[len(parents):] = self.POP[key[ii]]
        return parents


    '''

def cross_over(parents,m):
    return child

def mutant(child):
    return child

def objective(individual):
    return 0
    '''

def load_dataset(csv_path):
    """Load dataset from a CSV file.

    Args:
         csv_path: Path to CSV file containing dataset.

    Returns:
        Course List
    """

    # Load headers
    with open(csv_path, 'r') as csv_fh:
        headers = csv_fh.readline().strip().split(',')
    # Load features and labels
    dept_cols = [i for i in range(len(headers)) if headers[i].startswith('a')]
    course_cols = [i for i in range(len(headers)) if headers[i].startswith('b')]
    MpW_cols = [i for i in range(len(headers)) if headers[i].startswith('f')]
    #dept = np.loadtxt(csv_path,dtype=str, delimiter=',', skiprows=1, usecols=dept_cols)
    #Course = np.loadtxt(csv_path, dtype=str, delimiter=',', skiprows=1, usecols=course_cols)
    #MinpW = np.loadtxt(csv_path, delimiter=',', skiprows=1, usecols=MpW_cols)
    #fix with working file reader, this is valid for aa spring 2020
    Course_List = [['AA','AA','AA','AA','AA','AA','AA','AA','AA','AA','AA','AA','AA','AA'],
    ['203','204','218','222','252','257','273','279B','279D','294','109Q','119N','146B','173'],
    [160,160,160,160,170,160,160,160,240,80,240,100,160,100]]
    return Course_List

if __name__ == '__main__':
    main()