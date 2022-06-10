import datetime
import time
import uuid
import pendulum
import pymysql.cursors
from src.NewTun.Connection import Connection
from src.NewTun.JgdyQuery import JgdyQuery
from src.NewTun.RunTimeExecute import RunTimeExecute
from src.NewTun.StockFetch import StockFetch


class StockInfoSyn:

    #是否拉取机构调研消息
    isJgdy=False

    stockMap={}

    #tushare code转化为baostock code
    def tuShareCode2BaoStockCode(self,tuShareCode):
        code=tuShareCode.lower().split('.')
        realCode=code[1]+"."+code[0]
        return realCode

    #baostock code转tushare code
    def BaoStockCode2tuShareCode(self,BaoCode):
        code=BaoCode.upper().split('.')
        realCode=code[1]+"."+code[0]
        return realCode


    #获取基本股票
    def getBiscicStock(self):
        stockList=[]
        connection=Connection()
        connect = pymysql.Connect(
            host=connection.host,
            port=connection.port,
            user=connection.user,
            passwd=connection.passwd,
            db=connection.db,
            charset=connection.charset
        )
        cursor = connect.cursor()
        allStockBasic = "select * from stock_basic"
        # allStockBasic = "select * from stock_basic where ts_code='300377.sz'"
        cursor.execute(allStockBasic)
        for row in cursor.fetchall():
            realCode = self.tuShareCode2BaoStockCode(row[0])
            temp=[]
            temp.append(realCode)
            temp.append(row[2])
            temp.append(row[3])
            temp.append(row[4])
            stockList.append(temp)
        cursor.close()
        connect.close()
        return stockList

    def doSyn(self,i,stockTemp,endTime):
        # 获取游标
        connection = Connection()
        connect = pymysql.Connect(
            host=connection.host,
            port=connection.port,
            user=connection.user,
            passwd=connection.passwd,
            db=connection.db,
            charset=connection.charset
        )
        cursor = connect.cursor()
        startTime = ''

        fectExecute = StockFetch()

        #开始运行的时间
        markRunTimeHour=RunTimeExecute().fetchMarkRunTimeHour()

        for row in stockTemp:
            isToady = False
            print("thread-" + str(i) +" - " + row)
            realCode = self.tuShareCode2BaoStockCode(row)
            tableCheckSql = "show tables like '" + realCode + "'"
            cursor.execute(tableCheckSql)
            if len(list(cursor)) == 0:
                print("no data of " + realCode)
                startTime = '2015-01-01'
            else:
                # 查找股票的最近时间
                sql = "SELECT * FROM `%s` order by date desc limit 1;"
                data = (realCode)
                cursor.execute(sql % data)
                # 如果没有数据那么设置为1997年开始
                for row in cursor.fetchall():
                    startTime1 = row[0]
                    if startTime1 == endTime:
                        isToady = True
                        continue
                    str_p = startTime1 + ' 0:29:08'
                    dateTime_p = datetime.datetime.strptime(str_p, '%Y-%m-%d %H:%M:%S')
                    startTime = (dateTime_p + datetime.timedelta(days=+1)).strftime("%Y-%m-%d")
            if isToady == True:
                print(realCode + "--不需要同步了。。")
            else:
                if markRunTimeHour < 15:
                    print("syn "+realCode+"\t to runTimeCache")
                else:
                    print("syn  " + realCode+"\t to mysql")
                # 优先从通达信获取数据
                if connection.tdxDayPath == '':
                    #没有表，需要重新创建表
                    t=pendulum.parse(endTime).day_of_week
                    subDay=self.dayofyear(startTime, endTime)
                    #相差一天以上，而且在周内。则先用baostock跑，再添加上腾讯当时数据
                    if subDay>1 and t<6:
                        fectExecute.fetchByStartAndEndTime(realCode, startTime, endTime)
                        add_hour = datetime.datetime.now()
                        now_hour = add_hour.strftime('%H')
                        if int(now_hour) < 18:
                            # 查找股票的最近时间
                            sql = "SELECT * FROM `%s` order by date desc limit 1;"
                            data = (realCode)

                            connection = Connection()
                            connect = pymysql.Connect(
                                host=connection.host,
                                port=connection.port,
                                user=connection.user,
                                passwd=connection.passwd,
                                db=connection.db,
                                charset=connection.charset
                            )
                            cursor = connect.cursor()

                            cursor.execute(sql % data)
                            innnerNow=False
                            # 如果没有数据那么设置为1997年开始
                            for row in cursor.fetchall():
                                startTime1 = row[0]
                                if startTime1 == endTime:
                                    innnerNow = True
                                break
                            #不是当日，采用拼接的方式
                            if innnerNow==False:
                                fectExecute.fetchDataFromEasyquotation(realCode, endTime)
                    elif subDay>1 and t>=6:
                        #周末跑数据，直接走baostock
                        fectExecute.fetchByStartAndEndTime(realCode, startTime, endTime)
                    elif subDay==1 and t<6:
                        #相隔一天的周内数据，直接走腾讯
                        fectExecute.fetchDataFromEasyquotation(realCode, endTime)
                else:
                    fectExecute.parseDataFromCvs(connection.tdxDayPath, realCode, startTime, endTime)
            if self.isJgdy == 'True':
                jgdy = JgdyQuery()
                jgdy.printJgdyInfo(realCode.split('.')[1], 1)

    #两个时间的差
    def dayofyear(self,startTime,endTime):
        a=startTime.split("-")
        b=endTime.split("-")
        date1 = datetime.date(year=int(a[0]), month=int(a[1]), day=int(a[2]))
        date2 = datetime.date(year=int(b[0]), month=int(b[1]), day=int(b[2]))
        return (date2 - date1).days + 1



    def synStockInfo(self):
        # 获取游标
        connection=Connection()
        connect = pymysql.Connect(
            host=connection.host,
            port=connection.port,
            user=connection.user,
            passwd=connection.passwd,
            db=connection.db,
            charset=connection.charset
        )
        cursor = connect.cursor()
        allStockBasic='select * from stock_basic'
        cursor.execute(allStockBasic)
        endTime=time.strftime('%Y-%m-%d',time.localtime(time.time()))
        stockCodeList=[]

        stockCodeList.append("sh.000001")
        for row in cursor.fetchall():
            stockCodeList.append(row[0])
        self.doSyn(1,stockCodeList,endTime)
        print("--------------syn---------end....")
        cursor.close()
        connect.close()

    def fanzhuanTatalSyn(self):
        # 获取游标
        connection = Connection()
        connect = pymysql.Connect(
            host=connection.host,
            port=connection.port,
            user=connection.user,
            passwd=connection.passwd,
            db=connection.db,
            charset=connection.charset
        )
        cursor = connect.cursor()
        tableCheckSql = "show tables like 'a_fan_zhuan_size'"
        cursor.execute(tableCheckSql)
        if len(list(cursor)) == 0:
            print("no table fanzhuan... ")
            print("create table a_fan_zhuan_size... ")
            createTable = "create table a_fan_zhuan_size(id varchar(64) primary key not null,collect_date varchar(64),count int,other varchar(45))"
            cursor.execute(createTable)
        endTime = time.strftime('%Y-%m-%d', time.localtime(time.time()))
        fanzhuanSql="select * from a_fan_zhuan_size where collect_date='"+endTime+"'"
        cursor.execute(fanzhuanSql)
        count =len(cursor.fetchall())
        if count<=0:
            sql = "INSERT INTO a_fan_zhuan_size (id,collect_date,count) VALUES ( '%s', '%s' ,%i)"
            data = (uuid.uuid1(), endTime, 0)
            cursor.execute(sql % data)
            connect.commit()
            print("insert into a_fan_zhuan_size :"+endTime)


