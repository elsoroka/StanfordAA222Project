# File created: 05/20/2020
# Tested on   : Python 3.7.4
# Author      : Emiko Soroka
# Unittests   : None
# Description :
# Particle swarm algorithm implementation, based on "Algorithms for Optimization" chapter 9.
# How to use  : Run file for demo

import copy
import numpy as np

class Particle:
	def __init__(self, x, v, x_best):
		self.x = x
		self.v = v
		self.x_best = x_best


class ParticleSwarm:
	def __init__(self, f:callable, population:np.array, w=1, c1=1, c2=1):
		self.f     = f     # objective function which takes x, f : R^n -> R
		self.pop   = population # Initial population
		self.w     = w     # inertia coefficient
		self.c1    = c1    # momentum coefficients
		self.c2    = c2

	def run(self, k_max:int)->np.array:
		# Algorithm from page 159
		# Initialization
		n = len(self.pop[0].x)
		x_best, y_best = copy.deepcopy(self.pop[0].x_best), np.Inf

		# Find the best value in the initial population
		for p in self.pop:
			y = self.f(p.x)
			if y < y_best:
				x_best[:], y_best = p.x, y

		# Iterate
		for k in range(0, k_max):
			for p in self.pop:
				r1, r2 = np.random.rand(n), np.random.rand(n)
				p.x = np.add(p.x, p.v) # velocity
				p.v = self.w*p.v + self.c1*r1*(p.x_best - p.x) + \
				                   self.c2*r2*(x_best - p.x)
				y = self.f(p.x)
				if y < y_best:
					x_best[:], y_best = p.x, y
				if y < self.f(p.x_best):
					p.x_best[:] = p.x

		return self.pop


if __name__ == "__main__":
	print("Self-test on Wheeler's Ridge: f* = 0, x* = [1.0, 1.5]")
	# test on a small objective function
	# the global optimum is 0 at [1, 3/2]
	def wheelers_ridge(x, a = 1.5):
		x1 = x[0]; x2 = x[1]
		return -np.exp(-(x1*x2 - a)**2 - (x2 - a)**2) + 1

	n = 2
	init_x = [np.random.rand(2) for i in range(20)]
	init_population = [Particle(x=x, v=np.ones(n), x_best=x) for x in init_x]

	ps = ParticleSwarm(wheelers_ridge, init_population)
	final_population = ps.run(20); # Number of iterations
	best_f = np.Inf
	best_x = np.ones(n)*np.Inf
	for p in final_population:
		#print("x: ", p.x)
		#print("v: ", p.v)
		#print("x_best: ", p.x_best)
		fp = wheelers_ridge(p.x_best)
		if fp < best_f:
			best_f = fp; best_x = p.x_best

	print("\nBest x overall:", best_x, "\nwith f:", best_f)