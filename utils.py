import json


# get image data
def get_slider_image(slider_image):
    with open(slider_image['link'], 'rb') as image_file:
        image_data = image_file.read()
        data = {'link': slider_image['link'], 'metadata': json.loads(slider_image['metadata']), 'image_data': image_data}
        return data