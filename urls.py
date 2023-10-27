from django.urls import path
from .views import SliderViewSet, SliderImageViewSet

urlpatterns = [
    path('api/slider', SliderViewSet.as_view({'post': 'create_slider'}), name='create-slider'),
    path('api/slider/<int:pk>', SliderViewSet.as_view({'put': 'update_slider'}), name='update-slider'),
    path('api/slider/<int:pk>', SliderViewSet.as_view({'get': 'retrieve_slider'}), name='get-slider'),
    path('api/slider-images/upload', SliderImageViewSet.as_view({'post': 'upload_slider_image'}), name='upload-image'),
    path('api/slider-images/<int:pk>', SliderImageViewSet.as_view({'get': 'get_all_images'}), name='get-all-images'),
]