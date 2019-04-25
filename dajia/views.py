from django.shortcuts import render
from django.utils import timezone
import pytz
import os
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.http import HttpResponse
from django.db.models import Count
from django.db.models import Max
from django.db.models import Sum
from .models import User,Team,Steam,Cutting,Need,Membership,Sign,Giftorder,Gift
from .models import Order
from .models import Comment
from .models import Period
from .models import Production
from .models import Merchant
from dss.Serializer import serializer
import requests
import json
import random
import datetime
import uuid
import  time


def justtry(request):
    if request.method == 'GET':
        steamid=request.GET.get('steamid')
        member=Steam.objects.filter(steamid=steamid).values('member__name',"member__picture", \
                                                            "membership__cutprice","membership__time")
        member=serializer(member)
        print(member)
        return JsonResponse({"success":True})


def handle_upload_file(file,filename,path):
    allpath = 'uploads/'+path
    #上传文件的保存路径，可以自己指定任意的路径
    if not os.path.exists(allpath):
        os.makedirs(allpath)
    with open(allpath+filename,'wb+')as destination:
        for chunk in file.chunks():
            destination.write(chunk)
    return path+filename

@csrf_exempt
def login(request):
    if request.method == "GET":
        pic=request.GET.get('pic')
        code = request.GET.get('code')
        nickname = request.GET.get('nickname')
        gender=request.GET.get('gender')
        appid = 'wx2b21ee85de8b10a9'
        appSecret = 'e3ce059551daa9fdd4657a6445d2b265'
        data = {
            'appid': appid,
            'secret': appSecret,
            'js_code': code,
            'grant_type': 'authorization_code',
        }
        url = "https://api.weixin.qq.com/sns/jscode2session?appid=%s&secret=%s&js_code=%s&grant_type=authorization_code" % (
            appid, appSecret, code)
        r = requests.get(url=url)
        response = r.json()
        openid = response['openid']
        account = User.objects.filter(openid=openid).exists()
        if account:

            newaccount = User.objects.get(openid=openid)
            if newaccount.status == 0:
                return JsonResponse({"userid": newaccount.userid,"status":0})
            else:
                return JsonResponse({"userid": newaccount.userid,"name":newaccount.name, \
                                     "team_name":newaccount.team.teamname, \
                                     "account":newaccount.account,"number":newaccount.number[0:4],"status":1})

        else:

            newaccount=User.objects.create(openid=openid, nickname=nickname, picture=pic, gender=gender, status=0)
            return JsonResponse({"userid":newaccount.userid,"status":0})



#实名认证验证通过
#未注册给定注册以及返回数据
#已注册返回该账户已注册
def verify(request):
    if request.method == 'GET':
        puserid=request.GET.get('puserid','')
        userid = request.GET.get('userid', '')  # openid
        teamid = request.GET.get('teamid', '')  # teamid
        name = request.GET.get('name', '')  # 姓名
        number = request.GET.get('number', '')  # 学号
        department = request.GET.get('department', '')  # 院系
        telephone = request.GET.get('telephone', '')  # 电话号码
        team = Team.objects.get(teamid=teamid)
        if User.objects.filter(userid=userid,status=1):
            return JsonResponse({"userid": userid, "name": name, "team_name": team.teamname,
                                 "number": number[0:4], "status": 1, 'account': 50})
        else:
            if (puserid):
                P_User = User.objects.get(userid=puserid)
                P_User.account += 30
                P_User.save()  # 邀请人加上30贝壳
                User.objects.filter(userid=userid).update(name=name, number=number, department=department,
                                                          telephone=telephone, status=1, team=team, parentuser=P_User,account=50)
                return JsonResponse({"userid": userid, "name": name, "team_name": team.teamname,
                                     "number": number[0:4], "status": 1, 'account': 50})
            else:
                User.objects.filter(userid=userid).update(name=name, number=number, department=department,
                                                          telephone=telephone, status=1, team=team,account=50)
                return JsonResponse({"userid": userid, "name": name, "team_name": team.teamname,
                                     "number": number[0:4], "status": 1, 'account': 50})




#home页boat组件的信息获取

def home(request):
    if request.method == 'GET':
        pass
        teamid=request.GET.get('teamid','')
        maindata=Period.objects.filter(production__team_id=teamid,status=1).select_related('production','production__merchant').values('periodid','production','production__name', \
                                                                                   'production__introduction','production__introductionpic',\
                                                                               'startprice','starttime','endtime','type', \
                                                                               'production__merchant__location',\
                                                                               'production__merchant__latitude', 'production__merchant__longitude', \
                                                                               'number','cutnumber','saveprice','production__merchant__pic1', \
                                                                                   'cutprice',
                                                                                   'production__merchant__pic2' \
                                                                                   ,'production__reputation','production__merchant__pic3')
        maindata=serializer(maindata)
        return JsonResponse(maindata,safe=False)

#点击进入详情页，只需获取评论内容
#给定评论id，返回评论详情
#对datetime中用serializer库进行序列化用返回
#成功

def firstcomment(request):
    if request.method == 'GET':
        productionid = request.GET.get('productionid', '')
        data=Comment.objects.filter(production_id=productionid,status=1).select_related('user','user__team').values( 'context','user__name', \
                                                                                 'user__department','user__picture', \
                                                                                 'user__team__teamname','time','pic1','pic2','pic3').all()[0:50]
        data=serializer(data)
        return JsonResponse({'success': True, 'data': data})





def scancomment(request):
    if request.method == 'GET':
        number=request.GET.get('number','')
        number=int(number)
        periodid = request.GET.get('periodid', '')
        period = Period.objects.get(periodid=periodid)
        comments = Comment.objects.filter(production_id=period.production_id, status=1).select_related("user", \
                                                                                                       "user__team").values("user__team__logo",  \
                                                                                               "user__name","user__department" \
                                                                                               ,'user__team__teamname',"context", \
                                                                                               "time").all()[number:number+5]
        comments = serializer(comments)
        return JsonResponse({'success': True, 'data': comments})
#查看我的团和分享页展示内容
def getperiod(request):
    if request.method == 'GET':
        orderid=request.GET.get('orderid','')
        #每期都需要有自己的logo
        order=Order.objects.filter(orderid=orderid).select_related('period','production').values('period_id','production__logo','production__name', \
                                                           'period__number','period__startprice','period__cutprice', \
                                                           'period__endtime','status')

        period=serializer(order)
        return JsonResponse(period,safe=False)

#查询订单细节
#接口正常运行，细节的雕琢
def orderlist(request):
    if request.method == 'GET':
        userid = request.GET.get('userid', '')
        order=Order.objects.filter(user_id=userid).values('orderid','production__logo','production__name', \
                                                           'production__reputation','period__number','status', \
                                                           'period__endtime','period__starttime', \
                                                          'period_id','endprice',
                                                           'period__startprice','period__cutprice', \
                                                          'steam_id','steam__cutprice', \
                                                          'production__team__teamname','production__distance', \
                                                          'time1','time2','time3','time4','time5','time6')
        if order:
            order = serializer(order)
            return JsonResponse({"response":True,"period": order})
        else:
            return JsonResponse({"response":False})



def orderdetail(request):
    if request.method == 'GET':
        steamid = request.GET.get('steamid', '')
        onecut = Steam.objects.filter(steamid=steamid).values('member__userid','member__name', "member__picture", \
                                                              "membership__cutprice", "membership__time","member__department","time")
        twocut=Cutting.objects.filter(steamid=steamid).select_related("audience").values('audience__picture','audience__nickname','audience__name','cutprice')
        onecut = serializer(onecut)
        twocut = serializer(twocut)
        return JsonResponse({'onecut': onecut, 'twocut': twocut})

#对取消接口进行验证
#取消接口验证完成

def cancel(request):
    if request.method == 'GET':
        orderid=request.GET.get('orderid','')
        order=Order.objects.get(orderid=orderid)
        order.status=0
        nowtime = timezone.now()
        order.time6 = nowtime
        order.save()

        return JsonResponse({'success':True})
#评论
#验证成功
#立即靠岸
def completeorder(request):
    if request.method=='GET':
        orderid=request.GET.get('orderid','')
        order = Order.objects.get(orderid=orderid)
        order.status = 4
        nowtime = timezone.now()
        order.time4 = nowtime
        order.endprice = order.period.startprice - order.period.cutprice - order.steam.cutprice
        order.save()
        return JsonResponse({'success': True})


def comment(request):
    if request.method == 'POST':
        path = 'comment/'
        filename=str(uuid.uuid4())+'.jpg'
        pic = handle_upload_file(request.FILES['file'], filename, path)
        orderid=request.POST.get('orderid','')
        order=Order.objects.get(orderid=orderid)
        comment=order.comment
        if comment:
            if not comment.pic1:
                comment.pic1=pic
                comment.save()
                return JsonResponse({'success': 'pic1'})
            elif not comment.pic2:
                comment.pic2 = pic
                comment.save()
                return JsonResponse({'success': 'pic2'})
            elif not comment.pic3:
                comment.pic3=pic
                comment.save()
                return JsonResponse({'success':'pic3'})
            return JsonResponse({'success': False})
        else:
            context = request.POST.get('context', '')
            judge1 = request.POST.get('judge1', '')
            commenModel=Comment(context=context,user=order.user,status=0, \
                                production=order.production,judge1=judge1,judge2=5,pic1=pic)
            nowtime = timezone.now()
            commenModel.save()
            order.time5 = nowtime
            order.comment=commenModel
            order.status=5
            order.save()
            return JsonResponse({'success': True})
    if request.method == 'GET':
        return JsonResponse({'get': True})

#给定openid,teamid,
#验证成功
def buyalone(request):
    if request.method =='GET':
        userid= request.GET.get('userid', '')
        periodid = request.GET.get('periodid', '')
        period = Period.objects.get(periodid=periodid)
        user = User.objects.get(userid=userid)

        now = datetime.datetime.now()
        initial=period.startprice-period.bottomprice
        price = random.randint(int(0.1*initial), int(0.14*initial))  # 砍价金额


        period.number = period.number + 1
        period.cutnumber = period.cutnumber + 1
        period.saveprice += price
        period.save()


        #每人砍价
        if period.number<=100:
            cutprice = 0.001 * initial
            period.cutprice += cutprice
        period.save()
        steam = Steam.objects.create(cutprice=price, steamnumber=1)
        membership=Membership.objects.create(user=user,steam=steam,cutprice=price)
        order = Order.objects.create( user=user, period=period, status=1, steam=steam, cutprice=price,
                      production=period.production)
        return JsonResponse({'success': True, 'orderid':order.orderid,'steamid':steam.steamid, 'price': price})



def buytogether(request):
    userid= request.GET.get('userid', '')
    steamid = request.GET.get('steamid', '')
    periodid = request.GET.get('periodid', '')
    period = Period.objects.get(periodid=periodid)
    user = User.objects.get(userid=userid)
    # 差价初值
    initial = period.startprice - period.bottomprice
    price = random.randint(int(0.1 * initial), int(0.14 * initial))  # 砍价金额
    steam = Steam.objects.get(steamid=steamid)
    if steam.steamnumber < 5:
        period.cutnumber = period.cutnumber + 1
        period.saveprice += price
        period.save()
        steam.steamnumber = steam.steamnumber + 1
        steam.cutprice += price
        steam.save()
        period.number = period.number + 1
        if period.number <= 100:
            cutprice = 0.0001 * initial
            period.cutprice += cutprice
        order = Order.objects.create(user=user, period=period, status=1, steam=steam, cutprice=price,
                                     production=period.production)
        membership = Membership.objects.create(user=user, steam=steam, cutprice=price)
        period.save()
        return JsonResponse({'success': True, 'orderid':order.orderid, 'steamid':steamid,'price': price})
    else:
        return JsonResponse({'success': False, 'reason': '团队人数已满'})



#团队外成员砍价
def cutprice(request):
    if request.method == 'GET':
        userid=request.GET.get('userid','')
        steamid=request.GET.get('steamid','')
        periodid=request.GET.get('periodid','')
        period=Period.objects.get(periodid=periodid)
        # 差价初值
        initial = period.startprice - period.bottomprice
        user=User.objects.get(userid=userid)
        steam=Steam.objects.get(steamid=steamid)

        if steam.cutprice<=0.7:
            price=random.randint(int(0.1*initial),int(0.7*initial))
        elif steam.cutprice<=0.8:
            price = random.randint(int(0.05 * initial), int(0.3 * initial))
        else:
            price = random.randint(int(0.01 * initial), int(0.1 * initial))

        price=price/100
        period.cutprice+=price
        period.cutnumber=period.cutnumber+1
        period.save()
        judge=Cutting.objects.filter(steamid=steamid,audience_id=userid).exists()

        if judge:
            return JsonResponse({'success': False})
        else:
            steam.cutprice += price
            steam.save()
            cutting=Cutting.objects.create(audience=user,steamid=steamid, cutprice=price)
            return JsonResponse({'success': True, 'price': price})


def need(request):
    if request.method =="POST":
        path = 'need/'
        pic = handle_upload_file(request.FILES['file'], str(request.FILES['file']),path)
        userid=request.POST.get('userid',"")
        user=User.objects.get(userid=userid)
        nowtime = timezone.now()
        teamname=User.team.teamname
        Need.objects.create(user=user,time=nowtime,teamname=teamname)
        return JsonResponse({'success': True})

def sign(request):
    if request.method == 'GET':
        userid = request.GET.get('userid', "")
        user = User.objects.get(userid=userid)
        gain=User.objects.get('gain','')
#异常捕获
        try:
            Sign.objects.create(user=user,gain=gain)
            user.account+=gain
            return JsonResponse({'success': "签到成功"})
        except:
            return JsonResponse({'success': "签到成功"})

#抽奖礼物获得，奖项几率有待商榷
def getgift(request):
    if request.method == 'GET':
        userid=request.GET.get('userid','')
        user=User.objects.get(userid=userid)
        if user.account>=30:
            # 随机数
            new = random.randint(1, 100)
            if new == 1:
                gift = Gift.objects.get(id=1)
                user.account=user.account-30
                user.save()
                order = Giftorder.objects.create(user=user, gift=gift, status=0)
                return JsonResponse({'prize': 1,'account':user.account})
            elif new == 2:
                gift = Gift.objects.get(id=2)
                user.account = user.account - 30
                user.save()
                order = Giftorder.objects.create(user=user, gift=gift, status=0)
                return JsonResponse({'prize': 2,'account':user.account})
            elif new == 3:
                gift = Gift.objects.get(id=3)
                user.account = user.account - 30
                user.save()
                order = Giftorder.objects.create(user=user, gift=gift, status=0)
                return JsonResponse({'prize': 3,'account':user.account})
            elif new in range(4, 9):
                gift = Gift.objects.get(id=4)
                user.account = user.account+30
                user.save()
                order = Giftorder.objects.create(user=user, gift=gift, status=0)
                return JsonResponse({'prize': 4,'account':user.account})
            elif new in range(9, 15):
                gift = Gift.objects.get(id=5)
                user.account = user.account - 30
                user.save()
                order = Giftorder.objects.create(user=user, gift=gift, status=0)
                return JsonResponse({'prize': 5,'account':user.account})
            elif new in range(15, 50):
                gift = Gift.objects.get(id=6)
                user.account = user.account - 30
                user.save()
                order = Giftorder.objects.create(user=user, gift=gift, status=0)
                return JsonResponse({'prize': 6,'account':user.account})
            else:
                gift = Gift.objects.get(id=7)
                user.account = user.account - 25
                user.save()
                order = Giftorder.objects.create(user=user, gift=gift, status=0)
                return JsonResponse({'prize': 7,'account':user.account})
        else:
            return JsonResponse({'error': "账户余额不足"})



def accountdetail(request):
    if request.method=='GET':
        userid=request.GET.get('userid','')
        invitation=User.objects.filter(puser__userid=userid).values('puser__name')
        invitation=serializer(invitation)
        sign=Sign.objects.filter(userid=userid).values("time","gain")
        sign=serializer(sign)
        gorder=Giftorder.objects.filter(user_id=userid).values("gift__name",'time')
        gorder=serializer(gorder)
        return JsonResponse({'invitation': invitation,"sign":sign,"gorder":gorder})

















