import psutil
import utils
import time
import os

# 检查update_service_model.py进程是否存在
def checkUpdateProcess():
    updateRunning = False
    for p in psutil.process_iter():
        cmd = " ".join(p.cmdline())
        if "python" in cmd and "update_service_model.py" in cmd:
            updateRunning = True
            break
    return updateRunning


def addToDict(element, countDict):
    if element not in countDict:
        countDict[element] = 1
    else:
        count = countDict[element]
        countDict[element] = count + 1

# get gunicorn father process
def getGunicornPid():
    procNum = 0
    procCount = {}
    for p in psutil.process_iter():
        cmd = " ".join(p.cmdline())
        if "ffm_gunicorn.conf service:app" in cmd:
            procNum += 1
            addToDict(p.pid, procCount)
            addToDict(p.parent().pid, procCount)
    for pid, count in procCount.items():
        if count == procNum:
            return pid
    return -1

def checkKillSuccess():
    for p in psutil.process_iter():
        cmd = " ".join(p.cmdline())
        if "ffm_gunicorn.conf service:app" in cmd:
            return False
    return True


if __name__ == "__main__":
    # deal with update_service_model.py process
    updateRunning = checkUpdateProcess()
    if not updateRunning:
        print("starting update_service_model.py ...")
        utils.execCmd("nohup python -u ./update_service_model.py >> update_service_model.log 2>&1 &")
    else:
        print("update_service_model.py already running ...")

    # try to kill previous service
    gunicornPid = getGunicornPid()
    if gunicornPid > 0:
        print("killing gunicorn father process:", gunicornPid, "...")
        process = psutil.Process(gunicornPid)
        process.kill()

    # start service while no previous service is running
    while True:
        time.sleep(1)
        if checkKillSuccess():
            print("starting service ...")
            #python 3.7以上对标准输出和错误输出都采用unbuffered，不需要设置此变量
            #os.environ['PYTHONUNBUFFERED'] = 'TRUE'
            os.environ['OMP_NUM_THREADS'] = '1'
            utils.execCmd("nohup gunicorn -c gunicorn.conf service:app >> nohup.out 2>&1 &")
            break
    print("done.")

