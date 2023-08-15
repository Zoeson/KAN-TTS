#!/bin/bash

aishell_rootdir=$1
resample_dir=$2
resampling_rate=$3

for sp in `ls $aishell_rootdir`;do
    echo "$sp is resampling..."
    mkdir -p $resample_dir/$sp/wav
    cp -r $aishell_rootdir/$sp/prosody $resample_dir/$sp/
    cp -r $aishell_rootdir/$sp/interval $resample_dir/$sp/
    for wav in `ls $aishell_rootdir/$sp/wav/*.wav`;do
        wav_bn=`basename $wav`
        sox $wav -r $resampling_rate -b 16 -c 1 $resample_dir/$sp/wav/$wav_bn
    done
done

