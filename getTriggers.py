from __future__ import print_function
import numpy as np
from collections import Counter
import datetime
import pandas as pd
import mne
import os
import glob
import argparse
from natsort import natsorted, ns

# defining constants
fs = 2000 # sampling freq for edf files
numframes = 1 #frames per bit on display
refresh = 1/60 #refresh period of monitor --- frame rate
bitperiod = numframes*refresh*fs

bitsperpacket = 8 #number of bits for each data packet

# defining lists for creating dataframe later to 
trigger = []
trigger_time = []
trigger_index = []

def main(array, patient_id):
	#mne_array(array, 'trigger_ch')
	data = array[0]
	print(data)
	# function to clear noise - the values are file specific
	def clearing_noise():
		#data[0:180] = 0
		data[:] = data * -1
		x = -13750 # threshold per data source; open data and see where everything is happening; ant the threshold as high as you can be to not trigger articafact, but low enough to trigger the trigger
		#data[data > x] = x #filtering out the noise #(data < 15000 in other cases)
		data[data < 18000] = x
        
	clearing_noise()

	# getting the most common value, which will be either zero or the maximum value of trigger
	b = Counter(data)
	peak = b.most_common()[1][0]
	print("peak: ", peak)

	print("data: ", data)
	
	# cutoff to take care of noise due to decay in trigger signal
	cutoff = peak + 500
	print("cutoff: ", cutoff)


	# getting everything in terms of ones and zeros - everything above the cutoff = 1, else 0
	# cutoff = 0
	filtereddata=np.zeros((1,len(data)))

	ii = np.where(data < cutoff) # greater than (>) when upright triggers
	filtereddata[0][ii[0]] = 1
	risingedgetimes = np.where(np.diff(filtereddata[0]) > 0)

	risingedges = np.zeros((1,len(data)))
	risingedges[0][risingedgetimes[0]] = 1

	print(risingedges)

	# the start bit time!
	startbittime = risingedgetimes[0][0] #prints the occurance of first one
	print("start: ", startbittime)

	# loop for extracting data
	while (1):
		testval = np.zeros([bitsperpacket])
		testval_time = np.zeros([1])
		testval_time[0]=startbittime

		# extract one byte(arbitrary size, packet) at a time flanked by start/stop bits
		# uses average value of signal during each bit period to allow for error
		for n in range(1,bitsperpacket+1):

			nd1 = int(startbittime+((n)*bitperiod)) #start after the start bit
			nd2 = int(startbittime+((n+1)*bitperiod)) #end 8 bits after start bit
			arr = filtereddata[0][range(nd1, nd2)]
		
			# getting average value (85%) of signal for each bit period
			print(arr)
			mean_val = np.mean(arr)
			if(mean_val > 0.95):
				val = 1
			else:
				val = 0

			testval[n-1] = val

		# print triggers in terminal with trigger index and trigger time
		def show_trigger():
			if(bi2de(testval) > 0): #and (bi2de(testval) != 1 or bi2de(testval) != 4 or bi2de(testval) != 16)):#==170 or bi2de(testval) == 1 or bi2de(testval) == 4 or bi2de(testval) == 16):# or bi2de(testval)!=0):
				trigger.append(bi2de(testval))
				trigger_time.append(testval_time[0]/2000)
				trigger_index.append(testval_time[0])

				print(testval)
				print("trigger: ", bi2de(testval), end="  time: ")
				print(secConversion(testval_time[0]/2000), end= "  seconds: ")
				print(testval_time[0]/2000, end=" index: ")
				print(testval_time[0])
				print()

		show_trigger()

		# Getting the next start bit after the end of the previous stop bit
		newrisingedges = risingedgetimes[0][np.where(risingedgetimes[0]>(startbittime+(bitsperpacket+2)*bitperiod))[0]]

		if (len(newrisingedges) == 0):
			break
		startbittime = newrisingedges[0]

		print("new start bit time: ", startbittime)

	# plotting for visualization
	mne_array(array, 'trigger_ch')
    
	# save to CSV
	saveToCSV(trigger, trigger_time, trigger_index, patient_id)



def secConversion(sec):
	time = datetime.timedelta(seconds=sec)
	return(time)

def bi2de(array):
	num = 0
	for i in range(array.shape[0]):
		num = num + (array[i]*(2**(7-i)))
    # there might be a bunch of things/triggers in your data that are the same, but are actualy slightly different values.
      #ie. you might say, "hey, I programmed a response trigger as code 128, but in the data it actually shows up as anything from 116-134. So change these as you will.
	if(num==247 or num == 231):
		num=4
	if(num==240 or num==253 or num == 191):
		num = 21
	if(num==255):
		num=101
	# for some files:
	#if(num==129 or num==128):
#		num=1
#	if(num==134 or num==132):
#		num = 4
#	if(num==152 or num==144 or num==24 or num==136):
#		num=16
#	if(num==255):
#		num=170
#	if(num==176):
#		num=32
	return(num)


def saveToCSV(trigger, trigger_time, trigger_index, patientID):
	cwd = '/data/Trigger_CSV_Files'
	filename = str(patientID)+"_"+"trigger_ecog.csv"
	download_destination = os.path.join('/Users/Whitehead/Documents/PearsonLab/ecog_data_analysis_notebooks/patient_2010/', filename)
	if not os.path.exists(os.path.dirname(download_destination)):
		os.makedirs(os.path.dirname(download_destination))
		trigger_dict = pd.DataFrame({'trigger' : trigger, 'trigger_time' : trigger_time, 'trigger_index' : trigger_index})
		trigger_dict.to_csv(download_destination, sep=',')
	else:
		trigger_dict = pd.DataFrame({'trigger' : trigger, 'trigger_time' : trigger_time, 'trigger_index' : trigger_index})
		trigger_dict.to_csv(download_destination, sep=',')


def file_process(trig_folder_loc, patient_id):
	# read all the files in the given folder
	files = natsorted(glob.glob(trig_folder_loc+"*.chn"), alg=ns.IGNORECASE)
	data_list = []
	for i in range(len(files)):
		data_list.append(read_file(files[i]))

	main(combining_chunks(data_list), patient_id)

def read_file(filepath):
	with open(filepath, 'rb') as data:
		data.readline()
		num = np.fromfile(data, dtype='<i2').astype('int64')  # read the data into numpy
	data_num = np.reshape(num,(1,len(num)))	
	return(data_num)

def combining_chunks(file_list):
	concate = np.concatenate(file_list, axis=1)
	return(concate)

def mne_array(data, ch_name1):
	ch_types = ['ecog']
	ch_names = [ch_name1]

	info = mne.create_info(ch_names=ch_names, sfreq=10000, ch_types=ch_types)
	raw = mne.io.RawArray(data, info, first_samp=0, verbose=None).load_data()
	
	plot(raw, 'Auto scaled data from original arrays')

def plot(raw, title):
	scalings = {'ecog': 1}
	color = {'ecog': 'g'}
	print("plotting ... ")

	raw.plot(n_channels=1, duration=10.0, color = color, scalings='auto', show=True, block=True)

if __name__ == '__main__':
	# setting up parse options
    parser = argparse.ArgumentParser(description='Get trigger time and trigger values for binary signals ',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('trigFolderLocation', help='Folder location with trigger channel files')
    parser.add_argument('--patientID', help='Patient ID for naming the CSV file; eg: year')
    args = parser.parse_args()

    trig_folder_loc = args.trigFolderLocation
    patient_id = str(args.patientID)

    # checking if all the arguments are given
    if not trig_folder_loc and not patient_id:
    	sys.exit('Must provide folder location with trigger channels (chunk files) and patient ID')
    else:
    	file_process(trig_folder_loc, patient_id)


