from PIL import Image
import numpy as np
from matplotlib import pyplot as plt

dir = '/home/iclab/work/'
p1 = 'up/images/0001.npy'
p2x = 'up/results/coarse_testing_1e-5x10,20/FD0:XJ3_1_20180822_204202.pkl/volumes/e2682_1/volume.npy'
p2y = 'up/results/coarse_testing_1e-5x10,20/FD0:XJ3_1_20180822_204202.pkl/volumes/e2682_2/volume.npy'
p2z = 'up/results/coarse_testing_1e-5x10,20/FD0:ZJ3_1_20180822_204202.pkl/volumes/e2682_1/volume.npy'

p3 = 'mu/images/0001.npy'
p4x = 'mu/results/coarse_testing_1e-5x10,20/FD0:XJ3_1_20180822_204202.pkl/volumes/e2682_1/volume.npy'
p4y = 'mu/results/coarse_testing_1e-5x10,20/FD0:YJ3_1_20180822_204202.pkl/volumes/e2682_1/volume.npy'
p4z = 'mu/results/coarse_testing_1e-5x10,20/FD0:ZJ3_1_20180822_204202.pkl/volumes/e2682_1/volume.npy'

# data = np.load(dir+p4)
# print(data.shape) #512,512,240 [rows, cols, slice]? WxHxL?

# for i in range(data.shape[2]):
#   plt.imshow(data[:, :, i].astype(np.float32), cmap='gray')
#   plt.title('slice # ' + str(i))
#   plt.show(block=False)
#   plt.pause(0.1)
case =2
if case ==1:
  data_input = np.load(dir+p3)
  data_output = np.load(dir+p4z)
else:
  data_input = np.load(dir+p1)
  data_output = np.load(dir+p2x)

fig = plt.figure(figsize=(10, 7)) 
# fig.add_subplot(rows=1, columns=2, index=1) 
for i in range(14,data_input.shape[2]): #14-37
  # plt.imshow(data[:, :, i].astype(np.float32), cmap='gray')
  # plt.title('slice # ' + str(i))
  # plt.show(block=False)
  # plt.pause(0.1)
  # # Adds a subplot at the 1st position 
  # plt.title('slice # ' + str(i)) 
  fig.suptitle('slice # ' + str(i)) 
  fig.add_subplot(1,2,1)
    
  # showing image 
  plt.imshow(data_input[:, :, i].astype(np.float32), cmap='gray')
  # plt.axis('off') 
  # plt.title('slice # ' + str(i))
    
  # Adds a subplot at the 2nd position 
  fig.add_subplot(1,2,2)
    
  # showing image 
  plt.imshow(data_output[:, :, i].astype(np.float32), cmap='gray')
  # plt.axis('off') 
  # plt.title('slice # ' + str(i))
  plt.show(block=False)
  plt.pause(0.1)
