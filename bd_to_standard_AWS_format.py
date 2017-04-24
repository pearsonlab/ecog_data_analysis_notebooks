### Code to convert behavioral data from task output to standard AWS format
### Can run on multiple files at the same time- will ask for independent user
### input for each file based on information about each task/file.

import numpy as np
import pandas as pd
import os

import json
import argparse
import sys

from datetime import datetime
from datetime import timedelta


# To read in the new blocks
def open_to_blocks(filename):
    with open(filename, 'r') as f:
        blocks = []
        while True:
            this_block = f.readline()
            if len(this_block) > 0:
                blocks.append(json.loads(this_block))
            else:
                break
    return blocks

# To find start and stop time and clean data chunk before putting into final format
def chop_blocks(begin, end, blocks, keep):
    start_timing = blocks[int(begin)]

    if "wall_time" in start_timing:
        start_time = start_timing['wall_time']
    elif "wall_start_time" in start_timing:
        start_time = start_timing['wall_start_time']
    else:
        print "Start time not found in file"
        sys.exit()
    
    if not keep:
        for i in np.arange(int(begin)+1):
            blocks.pop(0)
    
    if end:
        end_timing = blocks[-int(end)]
        if "wall_time" in end_timing:
            stop_time = end_timing['wall_time']
        elif "wall_stop_time" in end_timing:
            stop_time = end_timing['wall_stop_time']
        else:
            print "End time not found in file"
            sys.exit()

        if not keep:
            for i in np.arange(int(end)):
                blocks.pop()
    else:
        end_timing = blocks[-1]
        if "time_of_resp" in end_timing:
            len_of_trial = end_timing['time_of_resp']
        elif "time_of_response" in end_timing:
            len_of_trial = end_timing['time_of_response']
        else:
            print "Length of trial not found in file"
            sys.exit()

        # This takes start time + time up to last valid response + 5 minutes
        # and makes it stop_time when there is no stopt_ime saved (which shouldn't happen anymore).
        t = datetime.strptime(start_time, "%H:%M:%S:%f")+timedelta(seconds=len_of_trial+300)
        stop_time = '%d:%d:%d:%d' % (t.hour, t.minute, t.second, t.microsecond)
    
    return blocks, start_time, stop_time

# To save file
def save_file(expname, sid, start_time, stop_time, day, blocks):
    if not os.path.exists('behavioral_data/'):
            os.makedirs('behavioral_data')

    with open('behavioral_data/' + expname + '_' + str(sid)+ '.json', 'a') as f:
                f.write(json.dumps(
                        {
                            "meta": {
                                "subject": sid,
                                "start_time": start_time,
                                "stop_time": stop_time,
                                "experiment": expname,
                                "day": day
                            },
                            "data": blocks
                        }
                        )
                    )
if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description = "Take .json files and covert them for AWS")
    parser.add_argument(nargs='+', dest='files', help="Files to process")


    args = parser.parse_args()
    
    sid = raw_input("Subject ID: ")

    for file in args.files:
        print file
        
        expname = raw_input("\tExperiment Name: ")
        day = raw_input("\tDay of experiment (post-surgery; Surgery day = 0): ")
        begin = raw_input("\tLine number at beginning where start time is found (zero-indexed): ")
        end = raw_input("\tNumber of lines from end, where end time is found (one-indexed; use positive number)\n\t\t(Leave blank if no end time stored): ")
        keep = raw_input("\tDelete lines with start and stop times? (Blank if yes, 'no' if no): ")


        blocks = open_to_blocks(file)
        blocks_cut, start_time, stop_time = chop_blocks(int(begin), int(end), blocks, keep)
        save_file(expname, sid, start_time, stop_time, day, blocks_cut)
        print '\n'



