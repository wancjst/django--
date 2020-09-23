# 使用celery
from celery import Celery
from django.core.mail import send_mail
from django.conf import settings
from django.template import loader, RequestContext
import time

import os

from goods.models import GoodsType, IndexGoodsBanner, IndexTypeGoodsBanner, IndexPromotionBanner
from django_redis import get_redis_connection

# 创建一个Celery类的实例对象
app = Celery('celery_tasks.tasks', broker='redis://127.0.0.1:6379/8')

# 定义任务函数
@app.task
def send_register_active_email(to_email, username, token):
    '''发送邮件'''
    # 组织邮件信息
    subject = '天天生鲜欢迎信息'
    message = ''
    sender = settings.EMAIL_FROM
    receiver = [to_email]
    html_message = '<h1>%s,欢迎您成为会员<h1>请点击链接激活<br/><a href="http://127.0.0.1:8000/user/active/%s">http://127.0.0.1:8000/user/active/%s<a>' % (
    username, token, token)

    send_mail(subject, message, sender, receiver, html_message=html_message)
    time.sleep(5)

@app.task()
def gennerate_static_index_html():
    '''产生首页静态页面'''
    # 获取商品种类
    types = GoodsType.objects.all()

    # 获取首页轮播商品信息
    goods_banners = IndexGoodsBanner.objects.all().order_by('index')

    # 获取首页促销活动信息
    promotion_banners = IndexPromotionBanner.objects.all().order_by('index')

    # 获取首页分类商品展示信息
    for type in types:
        image_banners = IndexTypeGoodsBanner.objects.filter(type=type, display_type=1)
        titi_banners = IndexTypeGoodsBanner.objects.filter(type=type, display_type=0)

        # 动态给type增加属性，分别保存首页分类商品的图片展示信息和文字信息
        type.image_banners = image_banners
        type.title_banners = titi_banners

    # 组织模板上下文
    context = {
        'types': types,
        'goods_banners': goods_banners,
        'promotion_banners': promotion_banners,
    }

    # 使用模板
    # 1.加载模板文件，返回模板对象
    temp = loader.get_template('static_index.html')
    # 2.模板渲染
    static_index_html = temp.render(context)

    # 生成首页对应静态文件
    save_path = os.path.join(settings.BASE_DIR, 'static/index.html')
    with open(save_path, 'w') as f:
        f.write(static_index_html)
