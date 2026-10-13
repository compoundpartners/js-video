from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import filer.fields.image


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.FILER_IMAGE_MODEL),
        ('djangocms_video', '0012_videoplayer_description_videoplayer_duration_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='videoplayer',
            name='play_button_image',
            field=filer.fields.image.FilerImageField(blank=True, help_text='Overrides the site-wide play button for this video. Takes precedence over the play button icon.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.FILER_IMAGE_MODEL, verbose_name='Play button image'),
        ),
        migrations.AddField(
            model_name='videoplayer',
            name='play_button_icon',
            field=models.CharField(blank=True, help_text='Overrides the site-wide play button for this video, unless a play button image is set above.', max_length=255, verbose_name='Play button icon'),
        ),
        migrations.AlterField(
            model_name='videoplayer',
            name='poster',
            field=filer.fields.image.FilerImageField(blank=True, help_text='Shown over the video until the visitor clicks play. Leave blank to use the thumbnail published by YouTube or Vimeo.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.FILER_IMAGE_MODEL, verbose_name='Poster'),
        ),
    ]
