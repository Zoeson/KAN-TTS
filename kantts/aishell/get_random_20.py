import os
import sys
import glob
import random
import shutil

MAX_LEN=20

voicedir = sys.argv[1]
outdir = sys.argv[2]
if os.path.exists(outdir):
    shutil.rmtree(outdir)

wavdir = os.path.join(voicedir, 'wav')
prosodydir = os.path.join(voicedir, 'prosody')
intervaldir = os.path.join(voicedir, 'interval')
newwavdir = os.path.join(outdir, 'wav')
newprosodydir = os.path.join(outdir, 'prosody')
newintervaldir = os.path.join(outdir, 'interval')
os.makedirs(newwavdir, exist_ok=True)
os.makedirs(newprosodydir, exist_ok=True)
os.makedirs(newintervaldir, exist_ok=True)


wavfiles = glob.glob(os.path.join(wavdir, '*.wav'))
names = []
for wavfile in wavfiles:
    name = os.path.splitext(os.path.basename(wavfile))[0]
    names.append(name)

if len(names) <= MAX_LEN:
    cmd = "cp -r {} {}".format(wavdir, newwavdir)
    os.system(cmd)
    cmd = "cp -r {} {}".format(prosodydir, newprosodydir)
    os.system(cmd)
    cmd = "cp -r {} {}".format(intervaldir, newintervaldir)
    os.system(cmd)
else:
    random.shuffle(names)
    valid_names = names[:MAX_LEN]
    # get wav
    for name in valid_names:
        cmd = 'cp -f {} {}/'.format(os.path.join(wavdir, name + '.wav'), newwavdir)
        os.system(cmd)
    
    # get interval
    for name in valid_names:
        cmd = 'cp -f {} {}/'.format(os.path.join(intervaldir, name + '.interval'), newintervaldir)
        os.system(cmd)
    
    # get prosody
    fw = open(os.path.join(newprosodydir, 'prosody.txt'), 'w' )
    with open(os.path.join(prosodydir, 'prosody.txt'), 'r') as fr:
        lines = fr.readlines()
        for index, line in enumerate(lines):
            if not(index & 1):
                name = line.strip().split('\t')[0]
                if name in valid_names:
                    fw.write(line)
                    fw.write(lines[index+1])
    fw.close()