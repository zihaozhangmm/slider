import json
import os
import random
import uuid

from django.conf import settings
from django.core.cache import cache
from rest_framework import viewsets, status
from rest_framework.response import Response

from .models import Slider, SliderImage, SliderItem
from .utils import get_slider_image


class SliderViewSet(viewsets.ModelViewSet):

    # Create a slider
    def create_slider(self, request, *args, **kwargs):
        try:
            title = request.data.get('title', None)
            if not title:
                raise Exception('Please input tte title if the slider')

            slider_item_list = request.data['slider_item_list']

            # Create slider
            slider = Slider.objects.create(title=title)

            # Create each slider item
            for slider_item in slider_item_list:
                title = slider_item['title']
                description = slider_item['description']
                buttonText = slider_item['buttonText']
                component = slider_item['component']
                slider_image_id = slider_item['slider_image_id']
                slider_item = SliderItem.objects.create(
                    title=title,
                    description=description,
                    buttonText=buttonText,
                    component=component,
                    slider_image_id=slider_image_id,
                    slider_id=slider.id,
                )

            return Response(data={'status': 'success'}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    # Update a slider
    def update_slider(self, request, *args, **kwargs):
        try:
            slider_id = kwargs['pk']
            title = request.data['title']
            if not title:
                raise Exception('Please input tte title if the slider')

            # check if version matched
            if slider.version != request.data['version']:
                return Response(data={'error': 'Conflict - data is outdated.'}, status=status.HTTP_409_CONFLICT)
            
            # Update slider information   
            slider = Slider.objects.get(id=slider_id)
            slider.title = title
            slider.version += 1
            slider.save()

            slider_item_list = request.data['slider_item_list']
            slider_item_id_list = [item['id'] for item in slider_item_list]

            existing_items = SliderItem.objects.filter(slider_id=slider_id).all()

            # Delete redundant slider items
            for item in existing_items:
                if str(item.id) not in slider_item_id_list:
                    item.slider_image.delete()
                    item.delete()

            # upload each slider item
            for slider_item in slider_item_list:

                # If not updated, 'continue' to reduce access to database 
                if slider_item['updated'] == False:
                    continue

                # If the slider item exists, update it; otherwise, create a new item
                if SliderItem.objects.filter(id=slider_item['id']).exists():
                    SliderItem.objects.filter(id=slider_item['id']).update(
                        title=slider_item['title'],
                        description=slider_item['description'],
                        buttonText=slider_item['buttonText'],
                        component=slider_item['component'],
                        slider_image_id=slider_item['slider_image_id'],
                    )
                else:
                    SliderItem.objects.create(
                        title=slider_item['title'],
                        description=slider_item['description'],
                        buttonText=slider_item['buttonText'],
                        component=slider_item['component'],
                        slider_image_id=slider_item['slider_image_id'],
                        slider_id=request.data['slider_id'],
                    )
            # Delete cache
            cache.delete(f'slider_data_{slider_id}')
            
            return Response(data={'status': 'success'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    # Retrieve a slider
    def retrieve_slider(self, request, *args, **kwargs):
        try:
            slider_id = kwargs['pk']

            # Query cache based on slider_id 
            cache_key = f'slider_data_{slider_id}'
            cached_data = cache.get(cache_key)
            if cached_data:
                return Response(data=cached_data, status=status.HTTP_200_OK)

            # If not cached data, use lock to make sure only one request can access database
            lock_key = f'slider_lock_{slider_id}'
            lock_acquired = cache.set(lock_key, 'locked', nx=True)

            # If we can set 'lock_acquired' successfully, which means our request is the first and only one \
            # can access this slider and others will be rejected.
            # In the end we will set cache and delete lock_key, so other requests can get the cache.
            if lock_acquired:
                slider = Slider.objects.get(id=slider_id)
                data = {'id': slider_id, 'title': slider.title, 'slider_items': [], 'version': slider.version}
                
                # Fetch all slider items and images
                slider_item_list = SliderItem.objects.filter(slider_id=slider_id).all()
                slider_image_list = SliderImage.objects.filter(id__in=[s.slider_image.id for s in slider_item_list]).all()
                slider_images_dic = {s.id: s for s in slider_image_list}

                # Buile data structure
                for slider_item in slider_item_list:
                    data['slider_items'].append({
                        'title': slider_item.title,
                        'description': slider_item.description,
                        'button_text': slider_item.button_text,
                        'component': slider_item.component,
                        'slider_image': get_slider_image(slider_images_dic[slider_item.slider_image.id]),
                    })
                
                # Add cache
                cache.set(f'slider_data_{slider_id}', data, 600 + random.randint(-60, 60))
                cache.delete(lock_key)
                return Response(data=data, status=status.HTTP_200_OK)
            else:
                return Response(data={'status': 'waiting_for_lock'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    


class SliderImageViewSet(viewsets.ModelViewSet):

    # Upload an image
    def upload_slider_image(self, request, *args, **kwargs):
        try:
            image = request.data.get('image')
            metadata = request.data.get('metadata')
            slider_id = request.data.get('slider_id', None)

            # Save the uploaded image
            file_path = os.path.join(settings.SLIDER_IMAGE_FILE_PATH, f'{image.name}_{uuid.uuid4()}.jpg')
            with open(file_path, 'wb') as destination:
                for chunk in image.chunks():
                    destination.write(chunk)
            if slider_id:
            # Find the associated Slider
                slider = Slider.objects.get(id=slider_id)
            else:
                slider = Slider.objects.create()

            # Create a SliderImage object and associate it with the Slider
            slider_image = SliderImage.objects.create(link=file_path, metadata=json.dumps(metadata),slider_id=slider.id)
            slider_image.save()
            slider.image.add(slider_image) 
            slider.save()

            return Response(data={'status': 'success'}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    # Get all images belong to a slider
    def get_all_images(self, request, *args, **kwargs):
        try:
            slider_id = kwargs['pk']
            slider_image_list = SliderImage.objects.filter(slider_id=slider_id)
            data = [get_slider_image(slider_image) for slider_image in slider_image_list]
            return Response(data=data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
