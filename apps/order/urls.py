from django.conf.urls import url
from order.views import OrderPlaceView, OrderCommitView


urlpatterns = [
    url('^place$', OrderPlaceView.as_view(), name='place'), # 提交订单页面显示
    url('^commit', OrderCommitView.as_view(), name='commit'), # 订单创建


]
