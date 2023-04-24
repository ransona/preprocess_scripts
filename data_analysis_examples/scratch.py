import numpy as np

x = np.empty((10,10,0),float)

x = np.append(x,np.random.rand(((10,10))),axis=2)