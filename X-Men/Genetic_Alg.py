
import numpy as np
from numpy import random 
import copy
import matplotlib.pyplot as plt
import scipy
from scipy.stats import cauchy
from scipy.stats import randint
import matplotlib.pyplot as plt 
import dictionary
import csv
import time

def Optimize_Small():
    t = time.process_time()
    k_max = 800
    pop_size = 500 #must be an even number
    muts = 60
    schedule = GenAlg(K_max=k_max,m=pop_size,mutation_rt=muts,data='spring_csv_data_small.csv')  
    schedule.init_POP()
    schedule.NXT_GEN() 
    start,end = schedule.plot_sched()
    print((time.process_time()-t)/60)
def Optimize_Large():
    t = time.process_time()
    k_max = 60
    pop_size = 40 #must be an even number
    muts = 60
    schedule = GenAlg(K_max=k_max,m=pop_size,mutation_rt=muts,data='Engineering_spring_2020_small.csv')  
    schedule.init_POP()
    schedule.NXT_GEN() 
    start,end = schedule.plot_sched()
    print((time.process_time()-t)/60)
def plotss():
    k_max = 100
    pop_size = np.array([2, 10, 100, 250, 500,750, 1000]) #must be an even number
    muts = 30
    pts = 7
    start = np.zeros((pts,1))
    end = np.zeros((pts,1))
    it = range(0,pts,1)
    for i in range(pts):
        schedule = GenAlg(K_max=k_max,m=pop_size[i],mutation_rt=muts,data='spring_csv_data_small.csv')  
        schedule.init_POP()
        schedule.NXT_GEN() 
        start[i],end[i] = schedule.plot_sched()
    
    plt.figure(1)
    plt.plot(pop_size, start, 'ro', linewidth=2)
    plt.plot(pop_size, end, 'ko', linewidth=2)
    plt.xlabel('Population Size')
    plt.ylabel('score')
    plt.show()

    plt.figure(1)
    plt.plot(muts, start, 'ro', linewidth=2)
    plt.plot(muts, end, 'ko', linewidth=2)
    plt.xlabel('mutation rate')
    plt.ylabel('score')
    plt.show()
class GenAlg:
    def __init__(self,K_max=1000,m=1000,mutation_rt=30,data='spring_csv_data_small.csv'):
        self.K_max = K_max #max iteration
        self.POP_size = m
        self.courses = load_dataset(data)
        self.num_courses = len(self.courses[0])
        self.muts = mutation_rt
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
                pop_p[len(pop_p):] = rnd_ass(self.courses[2][c])
                
            self.POP[len(self.POP):]=[pop_p]
    def NXT_GEN(self):
        plt.figure()
        for k in range(self.K_max):
            print(k)
            parents = self.selection()
            '''
            if k%10==0:
                print(self.obj(parents[0]))
            '''
            plt.plot(k,self.obj(parents[0]),'ro')
            if k == 0:
                self.strt_score = self.obj(parents[0])
            if self.obj(parents[0]) == 0:
                break
            children = []
            ch = 0
            for c in range(self.POP_size):
                if c < len(parents):
                    children[len(children):] = [parents[c]]
                else:
                    a = parents[ch]
                    if (ch+1) >=len(parents):
                        b = parents[0]
                    else:
                        b = parents[ch+1]
                    children[len(children):] = [self.cross_over(a,b)]
                    ch +=1
            self.POP = self.mutant(children)
        self.POP = self.selection(last=1)
        self.fin_score = self.obj(self.POP[0])
        plt.plot(self.K_max,self.obj(self.POP[0]),'ro')
        plt.xlabel('iteration')
        plt.ylabel('score')
        plt.show()
    def obj(self,POP_single): #fix later
        score = 0
        overlap = 50
        early = 12
        late = 7.5
        lunch = 7.5
        cant = 50
        shouldnt = 25
        check = []
        for i in range(self.num_courses):
            if self.options[POP_single[i]][3]<930:
                score+=early
            if self.options[POP_single[i]][4]>1630:
                score+=late
            check_set = set(check)
            for slot in range(len(self.options[POP_single[i]][0])):
                if self.options[POP_single[i]][0][slot] in check_set:
                    score+=overlap
                else:
                    check.append(self.options[POP_single[i]][0][slot])
            if 1200 in range(self.options[POP_single[i]][3],self.options[POP_single[i]][4]):
                score+=lunch
            for ii in range(self.num_courses):
                for slot in range(len(self.options[POP_single[i]][0])):
                    check_2_set = set(self.options[POP_single[i]][0])
                    if self.options[POP_single[i]][0][slot] in check_2_set:
                        if ii+1>9:
                            test = str(ii+1)
                        else:
                            test = '0'+str(ii+1)
                        if test in self.courses[3][i]:
                            score += cant
                        if test in self.courses[4][i]:
                            score += shouldnt
        return score
    def selection(self,last=0): 
        '''Truncation'''
        m = self.POP_size
        temp = np.zeros((m,1))
        for i in range(m):
            temp[i] = self.obj(self.POP[i])
        obj = sorted(temp)
        key = sorted(range(len(temp)), key=lambda k: temp[k])
        parents = []
        if last==1:
            for ii in range(m):
                parents[len(parents):] = [self.POP[key[ii]]]

        else:
            for ii in range(int(m/2)):
                parents[len(parents):] = [self.POP[key[ii]]]       
        return parents
    def cross_over(self,a_par, b_par):
        child = []
        for i in range(self.num_courses):
            if np.random.normal(loc=0.0, scale=1.0) <0:
                child.append(a_par[i])
            else:
                child.append(b_par[i]) 
        return child
    def mutant(self,child):
        '''Bit Wise mutation'''
        muts = self.muts #mutation rate
        randint.rvs(76,85,size = 1)
        for pop in range(1,len(child)):
            for clss in range(self.num_courses):
                if randint.rvs(0,100,size = 1)<muts:
                    child[pop][clss] = rnd_ass(self.courses[2][clss])[0]
        return child
    def plot_sched(self):
        print('done')
        print(self.strt_score,self.fin_score)
        print('  ')
        end_POP = copy.deepcopy(self.POP[0])
        for i in range (len(end_POP)):
            print(self.courses[1][i],self.options[end_POP[i]][2],
                self.options[end_POP[i]][3],self.options[end_POP[i]][4])
        return self.strt_score,self.fin_score
def rnd_ass(cls_len):
    if cls_len <= 50:
        return randint.rvs(0,29,size = 1)
    elif cls_len <= 80:
        return randint.rvs(30,43,size = 1)
    elif cls_len <= 100:
        return randint.rvs(44,75,size = 1)
    elif cls_len <= 110:
        return randint.rvs(44,75,size = 1)
    elif cls_len <= 150:
        return randint.rvs(76,92,size = 1)
    elif cls_len <= 160:
        return randint.rvs(76,92,size = 1)
    elif cls_len <= 220:
        return randint.rvs(93,100,size = 1)
    elif cls_len <=240:
        return randint.rvs(93,100,size = 1)
    elif cls_len <=340:
        return randint.rvs(101,104,size = 1)
    else:
        print('error,',cls_len,'min not accounted for')
        return randint.rvs(1000,1001,size = 1)
def load_dataset(csv_path):
    """Load dataset from a CSV file.
    Args: csv_path: Path to CSV file containing dataset.
    Returns: Course List
    """
    file_rows = []
    with open(csv_path, 'r') as csv_fh:
        reader = csv.DictReader(csv_fh)
        for row in reader:
            file_rows.append(row)
    dept = []
    name = []
    length = []
    cant = []
    shouldnt = []
    numb = []
    for i in range(len(file_rows)):
        dept.append(file_rows[i]['dept'])
        name.append(file_rows[i]['courseNumber'])
        length.append(int(file_rows[i]['timeMinPweek']))
        if file_rows[i]['cantOverlap'] == '':
            cant.append('0')
        else:
            cant.append((file_rows[i]['cantOverlap']))
        if file_rows[i]['shouldntOverlap'] == '':
            shouldnt.append('0')
        else:
            shouldnt.append((file_rows[i]['shouldntOverlap']))    
        numb.append(int(file_rows[i]['dataNumber']))
    Course_List = [dept,name,length,cant,shouldnt,numb]
    return Course_List

if __name__ == '__main__':
    #Optimize_Small()
    Optimize_Large()