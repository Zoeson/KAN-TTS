# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   Description :    rvc.
   Author :       dengyj5
   date:          2023/3/2
-------------------------------------------------
"""
import requests
from component.utils.myLogger import *
from tornado.web import Application, RequestHandler
from tornado.ioloop import IOLoop
import json
import threading
from queue import Queue
import tcloud_tts
import config
import rvc_infer
import librosa
import os


log = get_log(log_path="/data/prod/dengyj5/deep_model/text2vec_logs", level="INFO")
costDict = {}

djy_tgt_sr, djy_net_g, djy_vc, djy_cpt = rvc_infer.get_vc(config.dongjiayao_model)
dwt_tgt_sr, dwt_net_g, dwt_vc, dwt_cpt = rvc_infer.get_vc(config.douwentao_model)
qq_tgt_sr, qq_net_g, qq_vc, qq_cpt = rvc_infer.get_vc(config.quanquan_model)

queue = Queue(1000)


def get_duration(file_path):
     """
     获取mp3/wav音频文件时长
     :param file_path:
     :return:
     """
     duration = librosa.get_duration(filename=file_path)
     return duration


class UpdateHandler(RequestHandler):
     def post(self):
        result = {}
        body = self.request.body
        try:
            body = json.loads(body)
            result["params"] = body
            if "source" in body and "operation" in body and "ids" in body:
                assert body["source"] in ["ai_brief", "3h_news"]
                if body["operation"] == "delete":
                    for id in body["ids"]:
                        cos_default_path = f"{config.cos_prefix}/{id}_default.wav"
                        cos_dwt_path = f"{config.cos_prefix}/{id}_douwentao.wav"
                        cos_djy_path = f"{config.cos_prefix}/{id}_dongjiayao.wav"
                        cos_qq_path = f"{config.cos_prefix}/{id}_quanquan.wav"
                        config.exec_cmd(f"coscmd delete {cos_default_path} -y")
                        config.exec_cmd(f"coscmd delete {cos_dwt_path} -y")
                        config.exec_cmd(f"coscmd delete {cos_djy_path} -y")
                        config.exec_cmd(f"coscmd delete {cos_qq_path} -y")
                if config.cos_exist(cos_default_path) or config.cos_exist(cos_dwt_path) or config.cos_exist(cos_djy_path):
                    result["msg"] = "failed"
                else:
                    result["msg"] = "success"
            else:
                result["msg"] = f"failed: params not correct."
                log.error("params error! result: {}".format(result))
        except Exception as e:
            result["msg"] = f"failed: {e}"
            log.error("request process failed, result: {}".format(result))
            log.exception(e)
        self.finish(json.dumps(result, ensure_ascii=False))


class RecallHandler(RequestHandler):
     def post(self):
        result = {}
        body = self.request.body
        try:
            body = json.loads(body)
            result["params"] = body
            if "source" in body and "items" in body and isinstance(body["items"], dict):
                assert body["source"] in ["ai_brief", "3h_news"]
                queue.put(body)
                result["msg"] = "success"
            else:
                result["msg"] = f"failed: params not correct."
                log.error("params error! result: {}".format(result))
        except Exception as e:
            result["msg"] = f"failed: {e}"
            log.error("request process failed, result: {}".format(result))
            log.exception(e)
        self.finish(json.dumps(result, ensure_ascii=False))


def consumer_func():
    while True:
        body = queue.get()
        print(f"new request: {body}")
        source = body["source"]
        items = body["items"]
        data = {}
        tasks = {}
        print(f"1. submit tts. {source}")
        for id, text in items.items():
            # 1. get tts
            task_id = tcloud_tts.submit_tts(voice_type=101013, text=text)
            tasks[f"male_{id}"] = task_id
            task_id = tcloud_tts.submit_tts(voice_type=101011, text=text)
            tasks[f"female_{id}"] = task_id
        # time.sleep(120)
        print(f"2. get tts and clone voice. {source}")
        try:
            for id, text in items.items():
                # 1. get tts
                male_path = f"{config.local_prefix}/{source}/{id}_male_tts.wav"
                female_path = f"{config.local_prefix}/{source}/{id}_female_tts.wav"
                if not os.path.exists(f"{config.local_prefix}/{source}"):
                    config.exec_cmd(f"mkdir -p {config.local_prefix}/{source}")
                if os.path.exists(male_path):
                    config.exec_cmd(f"rm -f {male_path}")
                tcloud_tts.get_tts_polling(tasks[f"male_{id}"], output_path=male_path)
                if os.path.exists(female_path):
                    config.exec_cmd(f"rm -f {female_path}")
                tcloud_tts.get_tts_polling(tasks[f"female_{id}"], output_path=female_path)
                # 2. rvc
                if os.path.exists(male_path):
                    log.info(f"start to clone voice {id}, {source}, {male_path} ...")
                    dwt_output = f"{config.local_prefix}/{source}/{id}_douwentao.wav"
                    rvc_infer.infer(0, male_path, config.douwentao_index, "harvest", dwt_output, 0.75, dwt_tgt_sr, dwt_net_g, dwt_vc, dwt_cpt)
                    djy_output = f"{config.local_prefix}/{source}/{id}_dongjiayao.wav"
                    rvc_infer.infer(0, male_path, config.dongjiayao_index, "harvest", djy_output, 0.75, djy_tgt_sr, djy_net_g, djy_vc, djy_cpt)
                if os.path.exists(female_path):
                    cos_default_path = f"{config.cos_prefix}/{id}_default.wav"
                    log.info(f"upload default to cos {cos_default_path}...")
                    config.exec_cmd(f"coscmd delete {cos_default_path} -y")
                    config.exec_cmd(f"coscmd upload {female_path} {cos_default_path}")

                    log.info(f"start to clone voice {id}, {source}, {male_path} ...")
                    qq_output = f"{config.local_prefix}/{source}/{id}_quanquan.wav"
                    rvc_infer.infer(0, female_path, config.quanquan_index, "harvest", qq_output, 0.75, qq_tgt_sr, qq_net_g, qq_vc, qq_cpt)
                if os.path.exists(dwt_output):
                    cos_dwt_path = f"{config.cos_prefix}/{id}_douwentao.wav"
                    log.info(f"douwentao output exist. upload to cos {cos_dwt_path}...")
                    config.exec_cmd(f"coscmd delete {cos_dwt_path} -y")
                    config.exec_cmd(f"coscmd upload {dwt_output} {cos_dwt_path}")
                if os.path.exists(djy_output):
                    cos_djy_path = f"{config.cos_prefix}/{id}_dongjiayao.wav"
                    log.info(f"dongjiayao output exist. upload to cos {cos_djy_path} ...")
                    config.exec_cmd(f"coscmd delete {cos_djy_path} -y")
                    config.exec_cmd(f"coscmd upload {djy_output} {cos_djy_path}")
                if os.path.exists(qq_output):
                    cos_qq_path = f"{config.cos_prefix}/{id}_quanquan.wav"
                    log.info(f"quanquan output exist. upload to cos {cos_qq_path} ...")
                    config.exec_cmd(f"coscmd delete {cos_qq_path} -y")
                    config.exec_cmd(f"coscmd upload {qq_output} {cos_qq_path}")
                data[id] = {}
                if config.cos_exist(cos_default_path):
                    data[id]["default"] = {"cos_url": f"https://video19.ifeng.com/video09/1997/01/01/{id}_default.wav",
                                            "duration": get_duration(female_path)}
                if config.cos_exist(cos_dwt_path):
                    data[id]["douwentao"] = {"cos_url": f"https://video19.ifeng.com/video09/1997/01/01/{id}_douwentao.wav",
                                            "duration": get_duration(dwt_output)}
                if config.cos_exist(cos_djy_path):
                    data[id]["dongjiayao"] = {"cos_url": f"https://video19.ifeng.com/video09/1997/01/01/{id}_dongjiayao.wav",
                                            "duration": get_duration(djy_output)}
                if config.cos_exist(cos_qq_path):
                    data[id]["quanquan"] = {"cos_url": f"https://video19.ifeng.com/video09/1997/01/01/{id}_quanquan.wav",
                                            "duration": get_duration(qq_output)}
        except Exception as e:
            print(f"catch exception: {e}")
        
        params = {"items": data}
        if "attach" in body:
            params["attach"] = body["attach"]
        log.info(params)
        res = send_callback(params, source)
        if res != -1:
            log.info(f"send callback success. source: {source}, id: {id}")
        else:
            log.info(f"send callback failed! source: {source}, id: {id}")


def send_callback(result: dict, source):
    url = None
    if source == "ai_brief":
        url = "http://10.66.228.123:7900/aiSummary/audioCallback"
    elif source == "3h_news":
        url = "http://recom-ali.ifeng.com/three-hours-engine/receiveAudioCallback"
    try:
        res = requests.post(url, json=result).json()
        if res["status"] == "success":
            return 0
    except Exception as e:
        log.error(e)
    return -1


p = threading.Thread(target=consumer_func)
p.start()


if __name__ == '__main__':
    try:
        app = Application([(r"/tts/speed_transfer", RecallHandler), (r"/tts/speed_operation", UpdateHandler)], debug=False)
        app.listen(8080)
        IOLoop.current().start()
    except Exception as e:
        print(e)