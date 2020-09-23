from django.shortcuts import render
from django.views.generic import View
from django.http import JsonResponse

from goods.models import Goods, GoodsSKU
from django_redis import get_redis_connection
from utils.mixin import LoginRequiredMixin


class CartAddView(View):
    '''加入购物车处理视图'''
    def post(self, request):
        user = request.user
        # 判断是否登录
        if not user.is_authenticated():
            return JsonResponse({'res':0, 'errmsg':'请先登陆'})

        # 接收数据
        sku_id = request.POST.get('sku_id')
        count = request.POST.get('count')

        # 校验数据
        # 数据是否完整
        if not all([sku_id, count]):
            return JsonResponse({'res': 1,'errmsg': '商品数据出错'})

        # 数量正确否
        try:
            count = int(count)
        except Exception as e:
            return JsonResponse({'res':2, 'errmsg':'商品数目出错'})

        # 商品是否存在
        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            return JsonResponse({'res':3, 'errmsg':'商品不存在'})

        # 逻辑处理：添加购物车
        # 连接redis
        conn = get_redis_connection('default')
        cart_key = 'cart_%d'%user.id
        # 获取原购物车中goods_id的数量
        cart_count = conn.hget(cart_key, sku_id)
        if cart_count:
            count += int(cart_count)

        # 判断是否超过库存
        if count > sku.stock:
            return JsonResponse({'res':4, 'errmsg':'商品库存不足'})

        # 将新数量保存至数据库
        conn.hset(cart_key, sku_id, count)

        # 返回数据
        return JsonResponse({'res':5, 'message':'添加成功'})


class CartInfoView(LoginRequiredMixin, View):
    '''购物车页面'''
    def get(self, request):
        '''显示'''
        # 获取登陆的用户
        user = request.user
        # 获取用户购物车中的商品信息
        conn = get_redis_connection('default')
        cart_key = 'cart_%d'%user.id
        # {'商品id'：商品数量}
        cart_dict = conn.hgetall(cart_key)

        skus = []
        # 保存购物车中商品的总数目和总价格
        total_count = 0
        total_price = 0
        # 遍历获取商品的信息
        for sku_id, count in cart_dict.items():
            # 根据商品的id获取商品信息
            sku = GoodsSKU.objects.get(id=sku_id)
            # 计算商品小计
            amount = sku.price*int(count)
            # 动态给sku对象增加一个属性amount,保存商品小计
            sku.amount = amount
            # 动态给sku对象增加一个属性count，保存购物车中对应商品的数量
            sku.count = count
            # 添加
            skus.append(sku)

            # 累计计算商品的总数目和总价格
            total_count += int(count)
            total_price += amount

        # 组织上下文
        context = {
            'total_count':total_count,
            'total_price':total_price,
            'skus':skus,
        }

        # 使用模板
        return render(request, 'cart.html', context)


# 更新购物车记录
# 采用ajax post请求
# 前端需要传递的参数：商品id（sku_id) 更新的商品数量（count）
# /cart/update
class CartUpdateView(View):
    '''购物车记录更新'''
    def post(self, request):
        '''购物车记录更新'''
        user = request.user
        if not user.is_authenticated():
            # 用户未登陆
            return JsonResponse({'res': 0, 'errmsg': '请先登录'})

        # 接收数据
        sku_id = request.POST.get('sku_id')
        count = request.POST.get('count')

        # 校验数据
        # 数据是否完整
        if not all([sku_id, count]):
            return JsonResponse({'res': 1, 'errmsg': '商品数据出错'})

        # 数量正确否
        try:
            count = int(count)
        except Exception as e:
            return JsonResponse({'res': 2, 'errmsg': '商品数目出错'})

        # 商品是否存在
        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            return JsonResponse({'res': 3, 'errmsg': '商品不存在'})

        # 业务处理，更新购物车记录
        conn = get_redis_connection('default')
        cart_key = 'cart_%d'%user.id

        # 校验商品库存
        if count > sku.stock:
            return JsonResponse({'res':4, 'errmsg':'库存不足'})

        # 更新
        conn.hset(cart_key, sku_id, count)

        # 计算用户购物车中的商品的总件数 {‘1’：5， ‘2’：3}
        total_count = 0
        vals = conn.hvals(cart_key)
        for val in vals:
            total_count += int(val)

        # 返回应答
        return JsonResponse({'res':5, 'total_count':total_count, 'errmsg':'更新成功'})


# 删除购物车记录
# 采用ajax post请求
# 前端需要传递的参数：商品id（sku_id) 更新的商品数量（count）
# /cart/delete
class CartDeleteView(View):
    '''购物车记录删除'''
    def post(self, request):
        user = request.user
        if not user.is_authenticated():
            return JsonResponse({'res':0, 'errmsg':'请先登陆'})

        # 接受参数
        sku_id = request.POST.get('sku_id')

        # 数据校验
        if not sku_id:
            return JsonResponse({'res':1, 'errmsg':'无效的商品id'})

        # 校验商品是否存在
        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            # 商品不存在
            return JsonResponse({'res':2, 'errmsg':'商品不存在'})

        # 业务处理，删除购物车记录
        conn = get_redis_connection('default')
        cart_key = 'cart_%d'%user.id

        # 删除 hdel
        conn.hdel(cart_key, sku_id)

        # 计算用户购物车中的商品的总件数 {‘1’：5， ‘2’：3}
        total_count = 0
        vals = conn.hvals(cart_key)
        for val in vals:
            total_count += int(val)

        # 返回应答
        return JsonResponse({'res':3, 'total_count':total_count, 'message':'删除成功'})



