#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""   
--------------------------------------------
    Author :      heling
    Date   :      2023/8/10 21:41
    File   :      test_model.py
    Description:
--------------------------------------------
"""
import time
from modelscope.outputs import OutputKeys
from modelscope.pipelines import pipeline
from modelscope.utils.constant import Tasks
import logger
serviceLog = "./test_model.log"
logger = logger.Logger(serviceLog)


text = ''
with open('./input/input.txt', 'r', encoding='utf-8') as f:
    data = f.readlines()
    for line in data:
        text += line

model_id = 'damo/speech_sambert-hifigan_tts_zh-cn_16k'
sambert_hifigan_tts = pipeline(task=Tasks.text_to_speech, model=model_id)
logger.printLog("start", 1, "开始生成voice ")

for voice in ['zhitian_emo', 'zhiyan_emo','zhizhe_emo','zhibei_emo']:
    _tag = voice
    start = time.time()
    output = sambert_hifigan_tts(input=text, voice=voice)
    end1 = time.time()
    wav = output[OutputKeys.OUTPUT_WAV]
    with open("output/"+voice+'.wav', 'wb') as f:
        f.write(wav)
    end2 = time.time()
    logger.printLog("finished", 1, voice)

# import os
# import shutil
# import tempfile
#
# from modelscope.metainfo import Trainers
# from modelscope.msdatasets import MsDataset
# from modelscope.trainers import build_trainer
# from modelscope.utils.audio.audio_utils import TtsTrainType
#
# model_id = 'speech_tts/speech_sambert-hifigan_tts_zh-cn_multisp_pretrain_24k'
# dataset_id = 'speech_kantts_opendata'
# dataset_namespace = 'speech_tts'
# # 训练信息，用于指定需要训练哪个或哪些模型，这里展示AM和Vocoder模型皆进行训练
# # 目前支持训练：TtsTrainType.TRAIN_TYPE_SAMBERT, TtsTrainType.TRAIN_TYPE_VOC
# # 训练SAMBERT会以模型最新step作为基础进行finetune
# # 训练Vocoder（HifiGAN）会从0开始进行训练，指定多少个step，训练多少个step
# train_info = {
#     TtsTrainType.TRAIN_TYPE_SAMBERT: {  # 配置训练AM（sambert）模型
#         'train_steps': 2,               # 训练多少个step
#         'save_interval_steps': 1,       # 每训练多少个step保存一次checkpoint
#         'eval_interval_steps': 1,       # 每训练多少个step评估一次
#         'log_interval': 1               # 每训练多少个step打印一次训练日志
#     },
#     TtsTrainType.TRAIN_TYPE_VOC: {      # 配置训练Vocoder（HifiGAN）模型
#         'train_steps': 2,
#         'save_interval_steps': 1,
#         'eval_interval_steps': 1,
#         'log_interval': 1
#     }
# }
# # 这里展示使用临时目录作为训练的workdir
# tmp_dir = tempfile.TemporaryDirectory().name
# print("tmp_dir:" + tmp_dir)
# if not os.path.exists(tmp_dir):
#     os.makedirs(tmp_dir)
#
# # 配置训练参数，指定数据集，临时工作目录和train_info
# kwargs = dict(
#     model=model_id,                             # 指定要finetune的模型
#     work_dir=tmp_dir,                           # 指定临时工作目录
#     train_dataset=dataset_id,                   # 指定数据集id
#     train_dataset_namespace=dataset_namespace,  # 指定数据集所属namespace
#     train_type=train_info                       # 指定要训练类型及参数
# )
# trainer = build_trainer(
#     Trainers.speech_kantts_trainer, default_args=kwargs)
# trainer.train()
# # 训练好的checkpoint位于{tmp_dir}/tmp_am/ckpt及{tmp_dir}/tmp_voc/ckpt中
# tmp_am = os.path.join(tmp_dir, 'tmp_am', 'ckpt')
# tmp_voc = os.path.join(tmp_dir, 'tmp_voc', 'ckpt')
# print("tmp_am:" + tmp_am)
# print("tmp_voc:" + tmp_voc)
# assert os.path.exists(tmp_am)
# assert os.path.exists(tmp_voc)