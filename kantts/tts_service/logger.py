from datetime import datetime
import os

class Logger:
    """
    适用于多进程的简易logger类，支持按天切分日志
    logPath是日志文件路径前缀，实际的日志文件还需要加上日期后缀
    """
    def __init__(self, logPath):
        self.logPath = logPath
        self.currentDate = datetime.strftime(datetime.now(), "%Y%m%d")
        self.file = open(self.logPath + "." + self.currentDate, 'a')

    """
    tag: 日志标记
    level: 级别 1 INFO 2 WARN 2 ERRO
    info: 输出内容
    """
    def printLog(self, tag, level, info):
        # 首先判断是否需要保存前一天的日志文件
        date = datetime.strftime(datetime.now(), "%Y%m%d")
        if date != self.currentDate:
            self.file.close()
            self.currentDate = date
            # 打开一个新的日志文件
            self.file = open(self.logPath + "." + self.currentDate, 'a')
            self.deleteLogFile()

        now = datetime.strftime(datetime.now(), "%H:%M:%S")
        level = int(level)
        if level == 1:
            levelStr = "INFO"
        elif level == 2:
            levelStr = "WARN"
        elif level == 3:
            levelStr = "ERRO"

        log = now + " - " + levelStr + " - [" + tag + "] - " + info
        print(log, file=self.file, flush=True)

    def deleteLogFile(self, _maxToKeep=30):
        serviceLog = "/data/prod/recall_ffm/service/logs/"
        validDirs = os.listdir(serviceLog)
        validDirs.sort()
        size = len(validDirs)
        if size > _maxToKeep:
            for d in validDirs[0:size - _maxToKeep]:
                print("cleaning: " + serviceLog + d)
                os.remove(serviceLog + d)
