#!/bin/bash

aishell_rootdir=$1
resample_rootdir=$2
sp=$3
sp_out=$4
resampling_rate=$5

echo "$sp is resampling..."
mkdir -p $resample_rootdir/$sp_out/wav
echo "mkdir -p $resample_rootdir/$sp_out/wav"
cp -r $aishell_rootdir/$sp/prosody $resample_rootdir/$sp_out/
cp -r $aishell_rootdir/$sp/interval $resample_rootdir/$sp_out/
for wav in `ls $aishell_rootdir/$sp/wav/*.wav`;do
    wav_bn=`basename $wav`
    sox $wav -r $resampling_rate -b 16 -c 1 $resample_rootdir/$sp_out/wav/$wav_bn
done
