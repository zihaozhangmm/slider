from django.test import TestCase
from django.core.cache import cache

from .models import Slider, SliderItem, SliderImage

class SliderViewSetTestCase(TestCase):

    def setUp(self):
        self.slider_data = {
            'title': 'Test Slider',
            'slider_item_list': [
                {
                    'title': 'Item 1',
                    'description': 'Description 1',
                    'buttonText': 'Button 1',
                    'component': 'Component 1',
                    'slider_image_id': 1,
                },
                {
                    'title': 'Item 2',
                    'description': 'Description 2',
                    'buttonText': 'Button 2',
                    'component': 'Component 2',
                    'slider_image_id': 2,
                }
            ]
        }
        self.slider_image = SliderImage.objects.create(link='/tmp/image_1.jpg')
        self.slider = Slider.objects.create(title='Existing Slider')

        self.slider_item = SliderItem.objects.create(
            title='Item 3',
            description='Description 3',
            buttonText='Button 3',
            component='Component 3',
            slider_image=self.slider_image,
            slider=self.slider,
        )

    def test_create_slider(self):
        request = self.client.post('api/slider', self.slider_data, format='json')
        self.assertEqual(request.status_code, 201)

    def test_update_slider(self):
        self.slider.version = 1
        self.slider.save()

        data = self.slider_data
        data['version'] = 1 
        request = self.client.put(f'api/slider/{self.slider.id}', data, format='json')
        self.assertEqual(request.status_code, 200)

    def test_retrieve_slider(self):
        cache.set(f'slider_data_{self.slider.id}', {'id': self.slider.id, 'title': self.slider.title, 'slider_items': []}, 600)

        request = self.client.get(f'api/slider/{self.slider.id}')
        self.assertEqual(request.status_code, 200)

class SliderImageViewSetTestCase(TestCase):

    def setUp(self):
        self.slider_image = SliderImage.objects.create(link='/tmp/image_1.jpg')
        self.slider = Slider.objects.create(title='Slider for Images')
        self.slider.image.add(self.slider_image)

    def test_upload_slider_image(self):
        file_path = '/tmp/image_2.jpg'
        with open(file_path, 'rb') as image_file:
            data = {'image': image_file, 'metadata': {}, 'slider_id': self.slider.id}
            request = self.client.post('api/slider-images/upload', data, format='multipart')
            self.assertEqual(request.status_code, 201)

    def test_get_all_images(self):
        request = self.client.get(f'api/slider-images/{self.slider.id}')
        self.assertEqual(request.status_code, 200)