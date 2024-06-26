import numpy as np
import os
import pydicom

N = 1       #病人個數
W = 512     #影像寬
H = 512     #影像長
path1 = 'CT'
path2 = 'images'
if not os.path.exists(path2):
    os.makedirs(path2)

for n in range(N):
    volumeID = '{:0>4}'.format(n + 1)
    print('Processing File ' + volumeID)
    filename1 = 'Patient_' + volumeID
    directory1 = os.path.join(path1, filename1)
    filename2 = volumeID + '.npy'

    for path_, _, file_ in os.walk(directory1):
        L = len(file_)
        if L > 0:
            print('  ' + str(L) + ' slices along the axial view.')
            data = np.zeros((W, H, L), dtype = np.int16)
            for f in sorted(file_):
                file1 = os.path.abspath(os.path.join(path_, f))
                image = pydicom.read_file(file1)
                sliceID = image.data_element("InstanceNumber").value - 1
                if image.pixel_array.shape[0] != 512 or image.pixel_array.shape[1] != 512:
                    exit('  Error: DICOM image does not fit ' + str(W) + 'x' + str(H) + ' size!')
                data[:, :, sliceID] = image.pixel_array
            file2 = os.path.join(path2, filename2)
            np.save(file2, data)
    print('File ' + volumeID + ' is saved in ' + file2 + ' .')

