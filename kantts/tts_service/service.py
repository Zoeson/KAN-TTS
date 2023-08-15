import datetime
import time
import config
import ujson
import os
import numpy

from flask import Flask, jsonify, request
from faiss_model import FaissModel
from threading import Thread
import logger
import requests
import random
import traceback
import sys

# 初始化代码
_tag = "FlaskApp"
app = Flask(__name__)
logger = logger.Logger(config.serviceLog)

models = {}  # 初始化models
#         models[modelVersion] = FaissModel(latestData, logger)

logger.printLog(_tag, 1, "已加载的模型: " + str(list(models.keys())))
logger.printLog(_tag, 1, "Service ready ...")

# 测试接口，用于监控服务器状态
@app.route("/recall/faiss/test", methods=["GET"])
def test():
    return "ok"


# 根据文章的一级分类，选取最终的返回结果，防止某一类文章过多
def select(filterResult, size):
    result = []
    categoryNumD = getCategoryNum(filterResult, size)
    selectedNumD = {}
    for candidate in filterResult:
        category = candidate["category"]
        maxNum = categoryNumD[category]
        if category not in selectedNumD:
            result.append(candidate)
            selectedNumD[category] = 1
        else:
            currentNum = selectedNumD[category]
            if currentNum < maxNum:
                result.append(candidate)
                selectedNumD[category] = selectedNumD[category] + 1
            else:
                continue
        if len(result) >= size:
            break
    return result


# 过滤曝光超过阈值（db2）
def select_cold(uid, filterResult, size, expose_list):
    result = []
    categoryNumD = getCategoryNum(filterResult, size)
    selectedNumD = {}
    for candidate in filterResult:
        category = candidate["category"]
        docId = candidate["docId"].encode()
        if docId in expose_list:
            maxNum = categoryNumD[category]
            if category not in selectedNumD:
                result.append(candidate)
                selectedNumD[category] = 1
            else:
                currentNum = selectedNumD[category]
                if currentNum < maxNum:
                    result.append(candidate)
                    selectedNumD[category] = selectedNumD[category] + 1
                else:
                    continue
            if len(result) >= size:
                break
        else:
            # logger.printLog("曝光超过500次, 不允许继续曝光:", 1, uid + ":" + docId.decode())
            continue
    return result


def getCategoryNum(filterResult, size):
    # 计算每个一级分类下合适的文章数量
    stat = {}
    for candidate in filterResult:
        category = candidate["category"]
        if category not in stat:
            stat[category] = 1
        else:
            stat[category] = stat[category] + 1

    candidateSize = len(filterResult)
    result = {}
    for category, count in stat.items():
        maxNum = count / candidateSize * size
        # 每一类至少有5篇文章的机会
        if maxNum < 5.0:
            result[category] = 5
        else:
            result[category] = int(maxNum)

    return result


def addStart(costDict, tag):
    start = time.time()
    costDict[tag] = [start]


def addEnd(costDict, tag):
    if tag in costDict:
        end = time.time()
        costDict[tag].append(end)


def costLine(costDict):
    if len(costDict) > 0:
        lst = list(costDict.items())
        # 按照添加的顺序排序
        lst.sort(key=lambda t: t[1][0])
        costList = [{t[0]: int(1000 * (t[1][1] - t[1][0]))} for t in lst if len(t[1]) > 1]
        return ujson.dumps(costList)
    else:
        return "-"


# 输入uid，召回用户近期感兴趣文章
@app.route("/recall/faiss/topn", methods=["POST"])
def recall():
    try:
        costDict = {}
        addStart(costDict, 'total')

        # get posted data
        data = request.form
        size = int(data.get('size', default=100))
        uid = data['uid']
        modelVersion = data['modelVersion']
        embeddingStr = data['embedding']

        if embeddingStr is None or modelVersion not in models:
            return ujson.dumps([])
        else:
            inputList = [0.0]
            userEmbedding = ujson.loads(embeddingStr)
            inputList.extend(userEmbedding)
            vector = numpy.array([inputList]).astype('float32')

            simIdDict = models[modelVersion].topN(vector, config.candidateSize)

            candidateResult = [{"simId": simId, "docId": docId, "distance": dis, "title": title, "category": c,
                                "classV1": c, "classV2": sc, "mediaId": mediaId, "source": source, "sourceName": sourceName,
                                "expireTime": expireTime, "docType": docType, 'flatResults': flatResults, "id": docId}
                               for simId, (docId, dis, title, c, sc, mediaId, source, sourceName, expireTime, docType, flatResults)
                               in simIdDict.items()]
            candidateResult.sort(key=lambda d: d["distance"])

            result = select(candidateResult, size)

            addEnd(costDict, 'total')
            logger.printLog(_tag, 1, "u:{}, m:{}, si:{}, cand:{}, so:{}, cost: {}" \
                            .format(uid, modelVersion, size, len(candidateResult), len(result),
                                    costLine(costDict)))
            return ujson.dumps(result)
    except Exception as _:
        msg = traceback.format_exc()
        logger.printLog(_tag, 3, msg)
        return ujson.dumps([])

