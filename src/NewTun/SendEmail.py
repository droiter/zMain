import datetime
import os
import smtplib
import time
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header

from src.NewTun.Connection import Connection
from src.NewTun.JgdyQuery import JgdyQuery
from src.NewTun.JingJu import JingJu
from src.NewTun.QueryStock import QueryStock


class SendEmail:
    tendown=[]
    other=[]
    Zsm=[]
    GSM=[]
    jingju=JingJu()


    def sendYouCanBuy(self,currentPath):
        query=QueryStock()
        codes=query.queryYouCanBuyStock()
        print(codes)

        self.tendown=[]
        self.other=[]
        for item in codes:
            temp=[]
            price=query.todayKlineByCode(item[0])
            temp.append(item[0])
            temp.append(item[1])
            temp.append(item[4])
            temp.append(item[5])
            temp.append(price)
            temp.append("")   #5
            temp.append(0)   #6
            temp.append(item[3])   #7



            if price<=10:
                self.tendown.append(temp)
            else:
                self.other.append(temp)
            #主力、散户、反转信号

            #机构调研
            self.getJgdy(item,temp)

            if item[5]==1:
                self.Zsm.append(temp)
            if item[5]==2:
                self.GSM.append(temp)

        self.tendown=sorted(self.tendown, key=lambda s: s[2],reverse=False)
        self.other=sorted(self.other, key=lambda s: s[2],reverse=False)
        self.Zsm=sorted(self.Zsm, key=lambda s: s[6],reverse=True)
        self.GSM=sorted(self.GSM, key=lambda s: s[6],reverse=True)
        self.doSendStockInfoBeautiful(self.Zsm,currentPath,"\t001回踩反弹")
        self.doSendStockInfoBeautiful(self.GSM,currentPath,"\t002底部吸筹")
        self.doSendStatisticForZsm()
        # self.doSendStockInfoBeautiful(self.tendown,currentPath,"   10+元以内")
        # self.doSendStockInfoBeautiful(self.other,currentPath,"  10-元以上")
        # self.doSendStatisticPaper()

        #行业统计
    def getHytj(self,list):
        hytj={}
        hyStock={}
        for item in list:
            if hytj.__contains__(item[7]):
                hytj[item[7]] = int(hytj.get(item[7])) + 1
                hyStock[item[7]] = hyStock.get(item[7])+","+item[1]+"("+item[0]+")"
            else:
                hytj[item[7]] = 1
                hyStock[item[7]] = item[1]+"("+item[0]+")"
        hytjResult=[]
        for hj in sorted(hytj.items(), key=lambda x: x[1], reverse=True):
            hyTemp=[]
            hyTemp.append(hj[0])
            hyTemp.append(str(hj[1]))
            hyTemp.append(hyStock.get(hj[0]))
            hytjResult.append(hyTemp)
        return hytjResult,hyStock,hytj
    #机构调研
    def getJgdy(self,item,temp):
        jgdy = JgdyQuery()
        current = jgdy.printJgdyInfo(item[0].split('.')[1], 1)
        if len(current) > 0:
            diaoy = '<b>1.机构调研：</b></br>'
            for z in current:
                jgdyDate = z[8]
                str_p = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
                dateTime_p = datetime.datetime.strptime(str_p, '%Y-%m-%d %H:%M:%S')
                startTime = (dateTime_p + datetime.timedelta(days=-100)).strftime("%Y-%m-%d")
                if jgdyDate > startTime:
                    ztemp = z[8] + "&nbsp;&nbsp;" + z[11] + "&nbsp;&nbsp;" + z[15] + "</br>"
                    diaoy = diaoy + ztemp
            if diaoy != '<b>1.机构调研：</b></br>':
                temp[5] = diaoy
                temp[6] = len(current)
            else:
                temp[6] = 0
        else:
            temp[5] = ""
            temp[6] = 0


    def getJingjuNext(self):
        return self.jingju.readOneJinju()

    def doSendStockInfoBeautiful(self,codes,currentPath,subject):
        con=Connection()
        myContent="<h4><font color = 'red' > " + self.getJingjuNext() + " </font ></h4></br>"

        htmls = myContent + "<h2>1.行业分类(个股数量："+str(len(codes))+")</h2><table border='1'>"
        htmls = htmls + "<tr><td>行业</td><td>数量</td><td>待选股票</td><td>结论</td></tr>"

        hytjResult,hyStock,hytj=self.getHytj(codes)
        for row in hytjResult:
            htmls = htmls + "<tr>"
            if float(row[1]) >=4:
                for item in row:
                    htmls = htmls + "<td bgcolor='#FFCC66'><font color='red' font-size=8px >" + str(item) + "</font></td>"
                htmls = htmls + "<td bgcolor='#FFCC66'><font color='red' font-size=8px>黑马行业</font></td>"
            elif float(row[1])==3:
                for item in row:
                    htmls = htmls + "<td bgcolor='FFCC66'><font color='orange' font-size=8px>" + str(item) + "</font></td>"
                htmls = htmls + "<td bgcolor='#FFCC66'><font color='orange' font-size=8px>优势行业</font></td>"
            else:
                for item in row:
                    htmls = htmls + "<td bgcolor='FFCC66'><font color='green' font-size=8px>" + str(item) + "</font></td>"
                htmls = htmls + "<td bgcolor='#FFCC66'><font color='green' font-size=8px>一般行业</font></td>"


            htmls=htmls+"</tr>"
        htmls=htmls+"</table>"
        imgsOKstr = htmls+"<h2>2.股票详情</h2><p>"
        count=80
        #前二十的股票提供图片显示
        for item in codes:
            hy=hytj.get(item[7])
            myhy=item[7]
            myhyColor="<font color = 'black' >"
            if int(hy)>=3:
                myhy=myhy+"&nbsp;&nbsp;🔺"
                myhyColor="<font color = 'red' >"
            if count>0:
                imgsOKstr = imgsOKstr + "<p>"+myhyColor + str(item[0]) + "&nbsp;"+str(item[1])+"&nbsp;&nbsp;"+str(item[2])+"&nbsp;&nbsp;"+str(item[4])+"&nbsp;&nbsp;&nbsp;"+myhy+"</font></br>"+str(item[5])+"<img src='cid:"+item[0]+"'></p>"
            else:
                imgsOKstr = imgsOKstr + "<p>"+myhyColor + str(item[0]) + "&nbsp;"+str(item[1])+"&nbsp;&nbsp;"+str(item[2])+"&nbsp;&nbsp;"+str(item[4])+"&nbsp;&nbsp;&nbsp;</br>"+myhy+"</font></br>"+str(item[5])+"</p>"
            count=count-1

        endDate = time.strftime('%Y-%m-%d', time.localtime(time.time()))
        my_pass = con.emailPass
        my_user = con.emaialUser
        sender = con.sender
        receivers = con.receivers
        msgRoot = MIMEMultipart('related')
        msgRoot['From'] = Header(str(endDate) + subject, 'utf-8')
        msgRoot['To'] = Header("测试", 'utf-8')
        subject = str(endDate) + subject
        msgRoot['Subject'] = Header(subject, 'utf-8')

        msgAlternative = MIMEMultipart('alternative')
        msgRoot.attach(msgAlternative)
        mail_msg = imgsOKstr
        msgAlternative.attach(MIMEText(mail_msg, 'html', 'utf-8'))

        # 指定图片为当前目录
        count = 80
        for item in codes:
            if count>0:
                pngPath=currentPath+'\\temp\\' + item[0] + ".png"
                if os.path.exists(pngPath):
                    fp = open(pngPath, 'rb')
                    msgImage = MIMEImage(fp.read())
                    fp.close()
                    temp = "<" + item[0] + ">"
                    # 定义图片 ID，在 HTML 文本中引用
                    msgImage.add_header('Content-ID', temp)
                else:
                    fp = open(currentPath+"\\temp\\zMain.png", 'rb')
                    msgImage = MIMEImage(fp.read())
                    fp.close()
                    temp = "<" + item[0] + ">"
                    # 定义图片 ID，在 HTML 文本中引用
                    msgImage.add_header('Content-ID', temp)
                msgRoot.attach(msgImage)
            count=count-1
        try:
            users=receivers.split(',')
            for item in users:
                smtpObj = smtplib.SMTP()
                smtpObj.connect('smtp.qq.com', 25)  # 25 为 SMTP 端口号
                smtpObj.login(my_user, my_pass)
                smtpObj.sendmail(sender, item, msgRoot.as_string())
            print("邮件发送成功")
        except smtplib.SMTPException:
            print("Error: 无法发送邮件")




    def sendStockInfo(self,codes,currentPath):
        con=Connection()
        myContent="<h4><font color = 'red' > " + self.getJingjuNext() + " </font ></h4></br>"
        imgsOKstr = myContent+"当下可选股票："
        count=60
        #前二十的股票提供图片显示
        for item in codes:
            if count>0:
                imgsOKstr = imgsOKstr + "<p>" + str(item[0]) + "&nbsp;"+str(item[1])+"&nbsp;&nbsp;"+str(item[2])+"&nbsp;&nbsp;"+str(item[3])+"&nbsp;<img src='cid:"+item[0]+"'></p>"
            else:
                imgsOKstr = imgsOKstr + "<p>" + str(item[0]) + "&nbsp;"+str(item[1])+"&nbsp;&nbsp;"+str(item[2])+"</p>"
            count=count-1

        endDate = time.strftime('%Y-%m-%d', time.localtime(time.time()))
        my_pass = con.emailPass
        my_user = con.emaialUser
        sender = con.sender
        receivers = con.receivers
        msgRoot = MIMEMultipart('related')
        msgRoot['From'] = Header(str(endDate) + " 股票推荐", 'utf-8')
        msgRoot['To'] = Header("测试", 'utf-8')
        subject = str(endDate) + ' 股市有风险，投资需谨慎'
        msgRoot['Subject'] = Header(subject, 'utf-8')

        msgAlternative = MIMEMultipart('alternative')
        msgRoot.attach(msgAlternative)
        mail_msg = imgsOKstr
        msgAlternative.attach(MIMEText(mail_msg, 'html', 'utf-8'))

        # 指定图片为当前目录
        count = 20
        for item in codes:
            if count>0:
                fp = open(currentPath+'\\temp\\' + item[0] + ".png", 'rb')
                msgImage = MIMEImage(fp.read())
                fp.close()
                temp = "<" + item[0] + ">"
                # 定义图片 ID，在 HTML 文本中引用
                msgImage.add_header('Content-ID', temp)
                msgRoot.attach(msgImage)
            count=count-1
        try:
            users=receivers.split(',')
            for item in users:
                smtpObj = smtplib.SMTP()
                smtpObj.connect('smtp.qq.com', 25)  # 25 为 SMTP 端口号
                smtpObj.login(my_user, my_pass)
                smtpObj.sendmail(sender, item, msgRoot.as_string())
            print("邮件发送成功")
        except smtplib.SMTPException:
            print("Error: 无法发送邮件")
    # os.system('shutdown -s -f -t 180')

    #发送统计信息
    def doSendStatisticPaper(self):
        query = QueryStock()
        #暂时统计0.618以下的
        result = query.queryStockYouBrought("is_down_line=1 and profit!=0 and price<=10 and price>3")
        self.sendStatistic(result," zMain吸筹统计")

    #回踩反弹策略历史统计
    def doSendStatisticForZsm(self):
        query = QueryStock()
        result = query.queryStockYouBrought("zsm=1")
        self.sendStatistic(result," 001回踩反弹-统计")
        result = query.queryStockYouBrought("zsm=2")
        self.sendStatistic(result," 002底部吸筹-统计")

    # 发送邮件
    def sendStatistic(self,result,title):
        successCount=0
        myContent="<h4><font color = 'red' > " + self.getJingjuNext() + " </font ></h4></br>"
        htmls = myContent+"<table border='1'>"
        htmls=htmls+"<tr><td>代码</td><td>名称</td><td>买入时间</td><td>grad</td><td>cv</td><td>买价</td><td>价格</td><td>增幅100%</td></tr>"
        todayCount=0
        for item in result:
            htmls=htmls+"<tr>"
            if None!=item[7] and float(item[7]) > 0:
                successCount = successCount + 1
            elif None!=item[7] and float(item[7]) == 0:
                todayCount=todayCount+1
            for vo in range(len(item)):
                if float(item[7])>0:
                    htmls=htmls+"<td bgcolor='#FFCC66'><font color='red'>" + str(item[vo]) + "</font></td>"
                elif float(item[7])<0:
                    htmls = htmls + "<td bgcolor='#00FF00'><font color='blue'>" + str(item[vo]) + "</font></td>"
                else:
                    htmls = htmls + "<td><font color='red'>" + str(item[vo]) + "</font></td>"
            htmls=htmls+"</tr>"
        htmls=htmls+"</table>"
        totalCount=len(result)-todayCount
        if totalCount==0:
            totalCount=1
        endHtml="增长个数:"+str(successCount)+"&nbsp&nbsp&nbsp&nbsp总共个数："+str(totalCount)+"                </br> 百分比："+str(successCount*100/totalCount)+"%"+htmls
        con = Connection()
        endDate = time.strftime('%Y-%m-%d', time.localtime(time.time()))
        my_pass = con.emailPass
        my_user = con.emaialUser
        sender = con.sender
        receivers = con.receivers
        msgRoot = MIMEMultipart('related')
        msgRoot['From'] = Header(str(endDate) + " 股票统计", 'utf-8')
        msgRoot['To'] = Header("测试", 'utf-8')
        subject = str(endDate) + title
        msgRoot['Subject'] = Header(subject, 'utf-8')
        msgAlternative = MIMEMultipart('alternative')
        msgRoot.attach(msgAlternative)
        mail_msg = endHtml
        msgAlternative.attach(MIMEText(mail_msg, 'html', 'utf-8'))
        try:
            users=receivers.split(',')
            for item in users:
                smtpObj = smtplib.SMTP()
                smtpObj.connect('smtp.qq.com', 25)  # 25 为 SMTP 端口号
                smtpObj.login(my_user, my_pass)
                smtpObj.sendmail(sender, item, msgRoot.as_string())
            print("邮件发送成功")
        except smtplib.SMTPException:
            print("Error: 无法发送邮件")



