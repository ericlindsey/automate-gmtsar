#!/usr/bin/env python

import multiprocessing
import numpy as np


def my_func(arg):
  return np.zeros((arg,arg))

if __name__ == '__main__':

    numproc=2
    args=[1,2,3,4]
    with multiprocessing.Pool(processes=numproc) as pool:
        output=pool.map(my_func, args)
    print(output)
