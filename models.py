from django.db import models


class Slider(models.Model):
    title =  models.CharField(null=True, blank=True, max_length=255, help_text="Title of the slider")
    version = models.IntegerField(default=0, help_text="Version user for optimistic lock")

    class Meta:
        app_label = 'slider'

class SliderImage(models.Model):

    link = models.CharField(null=False, blank=False, max_length=255, help_text="Image path")
    metadata = models.TextField(help_text="Additional metadata as JSON")
    slider = models.ForeignKey(Slider, on_delete=models.CASCADE, help_text="Associated slider")

    class Meta:
        app_label = 'slider'


class SliderItem(models.Model):

    title = models.CharField(null=False, blank=False, max_length=255, help_text="Title of the slider item")
    description = models.TextField(null=True, blank=True, help_text="Description of the slider item")
    button_text = models.CharField(null=True, blank=True, max_length=50, help_text="Text for the button on the slider item")
    component = models.CharField(null=True, blank=True, max_length=100, help_text="Component information for the slider item")
    slider_image = models.ForeignKey(
        SliderImage, on_delete=models.CASCADE, help_text="Background image associated with this slider item"
    )
    slider = models.ForeignKey(Slider, on_delete=models.CASCADE, help_text="Associated slider")

    class Meta:
        app_label = 'slider'

