import os
import sys
import time
from utils import *
from model import *

if __name__ == '__main__':
	data_path = sys.argv[1]
	current_fold = sys.argv[2]
	organ_number = int(sys.argv[3])
	low_range = int(sys.argv[4])
	high_range = int(sys.argv[5])
	slice_threshold = float(sys.argv[6])
	slice_thickness = int(sys.argv[7])
	organ_ID = int(sys.argv[8])
	plane = sys.argv[9]
	GPU_ID = int(sys.argv[10])
	learning_rate1 = float(sys.argv[11])
	learning_rate_m1 = int(sys.argv[12])
	learning_rate2 = float(sys.argv[13])
	learning_rate_m2 = int(sys.argv[14])
	crop_margin = int(sys.argv[15])
	crop_prob = float(sys.argv[16])
	crop_sample_batch = int(sys.argv[17])
	snapshot_path = os.path.join(snapshot_path, 'SIJ_training_' + \
		sys.argv[11] + 'x' + str(learning_rate_m1) + ',' + str(crop_margin))
	epoch = {}
	epoch['S'] = int(sys.argv[18])
	epoch['I'] = int(sys.argv[19]) 
	epoch['J'] = int(sys.argv[20])
	epoch['lr_decay'] = int(sys.argv[21])
	timestamp = sys.argv[22]

	if not os.path.exists(snapshot_path):
		os.makedirs(snapshot_path)
	
	FCN_weights = os.path.join(pretrained_model_path, 'fcn8s-heavy-pascal.pth') #'fcn8s_from_caffe.pth')
	print('FCN_weights: ', FCN_weights)
	if not os.path.isfile(FCN_weights):
		raise RuntimeError('Please Download <http://drive.google.com/uc?id=0B9P1L--7Wd2vT0FtdThWREhjNkU> from the Internet ...')

	from Data import DataLayer
	training_set = DataLayer(data_path=data_path, current_fold=int(current_fold), organ_number=organ_number, \
		low_range=low_range, high_range=high_range, slice_threshold=slice_threshold, slice_thickness=slice_thickness, \
		organ_ID=organ_ID, plane=plane)

	batch_size = 1
	os.environ["CUDA_VISIBLE_DEVICES"]= str(GPU_ID)
	trainloader = torch.utils.data.DataLoader(training_set, batch_size=batch_size, shuffle=True, num_workers=16, drop_last=True)
	print(current_fold + plane, len(trainloader))
	print(epoch)

	RSTN_model = RSTN(crop_margin=crop_margin, \
		crop_prob=crop_prob, crop_sample_batch=crop_sample_batch)
	RSTN_snapshot = {}

	model_parameters = filter(lambda p: p.requires_grad, RSTN_model.parameters())
	params = sum([np.prod(p.size()) for p in model_parameters])
	print('model parameters:', params)

	optimizer = torch.optim.SGD(
		[
			{'params': get_parameters(RSTN_model, coarse=True, bias=False, parallel=False)},
			{'params': get_parameters(RSTN_model, coarse=True, bias=True, parallel=False),
			'lr': learning_rate1 * 2, 'weight_decay': 0},
			{'params': get_parameters(RSTN_model, coarse=False, bias=False, parallel=False),
			'lr': learning_rate1 * 10},
			{'params': get_parameters(RSTN_model, coarse=False, bias=True, parallel=False),
			'lr': learning_rate1 * 20, 'weight_decay': 0}	
		],
		lr=learning_rate1,
		momentum=0.99,
		weight_decay=0.0005)

	criterion = DSC_loss()
	COARSE_WEIGHT = 1 / 3

	RSTN_model = RSTN_model.cuda()
	RSTN_model.train()

	for mode in ['S', 'I', 'J']:
		if mode == 'S':
			RSTN_dict = RSTN_model.state_dict()
			pretrained_dict = torch.load(FCN_weights) # FCN8s(n_class=21)
			# 1. filter out unnecessary keys
			pretrained_dict_coarse = {'coarse_model.' + k : v
					for k, v in pretrained_dict.items() 
					if 'coarse_model.' + k in RSTN_dict and 'score' not in k}
			pretrained_dict_fine = {'fine_model.' + k : v
					for k, v in pretrained_dict.items() 
					if 'fine_model.' + k in RSTN_dict and 'score' not in k}
			# 2. overwrite entries in the existing state dict
			RSTN_dict.update(pretrained_dict_coarse) 
			RSTN_dict.update(pretrained_dict_fine)
			# 3. load the new state dict
			RSTN_model.load_state_dict(RSTN_dict)
			print(plane + mode, 'load pre-trained FCN8s model successfully!')
		
		elif mode == 'I':
			print(plane + mode, 'load S model successfully!')
		elif mode == 'J':
			print(plane + mode, 'load I model successfully!')
		else:
			raise ValueError("wrong value of mode, should be in ['S', 'I', 'J']")

		try:
			for e in range(epoch[mode]):
				total_loss = 0.0
				total_coarse_loss = 0.0
				total_fine_loss = 0.0
				start = time.time()
				for index, (image, label) in enumerate(trainloader):
					start_it = time.time()
					optimizer.zero_grad()
					image, label = image.cuda().float(), label.cuda().float()
					coarse_prob, fine_prob = RSTN_model(image, label, mode=mode)
					coarse_loss = criterion(coarse_prob, label)
					fine_loss = criterion(fine_prob, label)
					loss = COARSE_WEIGHT * coarse_loss \
							+ (1 - COARSE_WEIGHT) * fine_loss
					total_loss += loss.item()
					total_coarse_loss += coarse_loss.item()
					total_fine_loss += fine_loss.item()
					loss.backward()
					optimizer.step()
					print(current_fold + plane + mode, "Epoch[%d/%d], Iter[%05d], Coarse/Fine/Avg Loss %.4f/%.4f/%.4f, Time Elapsed %.2fs" \
							%(e+1, epoch[mode], index, coarse_loss.item(), fine_loss.item(), loss.item(), time.time()-start_it))
					del image, label, coarse_prob, fine_prob, loss, coarse_loss, fine_loss
				
				if mode == 'J' and (e+1) % epoch['lr_decay'] == 0:
					print('lr decay')
					for param_group in optimizer.param_groups:
						param_group['lr'] *= 0.5

				print(current_fold + plane + mode, "Epoch[%d], Total Coarse/Fine/Avg Loss %.4f/%.4f/%.4f, Time elapsed %.2fs" \
						%(e+1, total_coarse_loss / len(trainloader), total_fine_loss / len(trainloader), total_loss / len(trainloader), time.time()-start))

		except KeyboardInterrupt:
			print('!' * 10 , 'save before quitting ...')
		finally:
			snapshot_name = 'FD' + current_fold + ':' + \
				plane + mode + str(slice_thickness) + '_' + str(organ_ID) + '_' + timestamp
			RSTN_snapshot[mode] = os.path.join(snapshot_path, snapshot_name) + '.pkl'
			torch.save(RSTN_model.state_dict(), RSTN_snapshot[mode])
			print('#' * 10 , 'end of ' + current_fold + plane + mode + ' training stage!')

