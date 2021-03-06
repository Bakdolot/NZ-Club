from django.conf import settings
from django.utils import timezone
from django.db import models
from datetime import datetime
from django.utils.translation import ugettext_lazy as _
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django_resized import ResizedImageField
from django.utils.safestring import mark_safe
from django.core.validators import FileExtensionValidator

import PIL
from PIL import Image

from fcm_django.models import FCMDevice
from rest_framework import status


class Category(models.Model):
    title = models.CharField(max_length=50, verbose_name="Название")
    image = ResizedImageField(upload_to='category/', verbose_name='Фотография',
                              size=[100, 100])
    order = models.PositiveIntegerField(default=0, blank=True, null=False)

    class Meta:
        verbose_name = _("Категория")
        verbose_name_plural = _("Категории")
        ordering = ('order',)

    def image_tag(self):
        return mark_safe('<img src={} width="200" />'.format(self.image.url))

    image_tag.short_description = 'Фотография'

    def __str__(self):
        return self.title


class Video(models.Model):
    STATUS = (
        ('1', 'Отклонено'),
        ('2', 'Активно'),
        ('3', 'В ожидании')
    )
    TYPE = (
        ('1', 'Обычный'),
        ('2', 'Премиум'),
        ('3', 'Благотворительность'),
    )
    title = models.CharField(max_length=100, verbose_name="Название")
    text = models.TextField(verbose_name="Описание")
    phone_1 = models.CharField(max_length=16, null=True, blank=True,
                               verbose_name="Телефон номер 1")
    phone_2 = models.CharField(max_length=16, null=True, blank=True,
                               verbose_name="Телефон номер 2")
    phone_3 = models.CharField(max_length=16, null=True, blank=True,
                               verbose_name="Телефон номер 3")
    instagram = models.CharField(max_length=50, null=True, blank=True,
                                 verbose_name="Инстаграм")
    facebook = models.CharField(max_length=50, null=True, blank=True,
                                verbose_name="Файсбук")
    web_site = models.CharField(max_length=50, null=True, blank=True,
                                verbose_name="Вебсайт")
    views = models.ManyToManyField(settings.AUTH_USER_MODEL,
                                   related_name='videos',
                                   verbose_name="Просмотров",
                                   through='VideoViews')
    watched_videos = models.ManyToManyField(settings.AUTH_USER_MODEL,
                                            related_name='watched_videos')
    favorites = models.ManyToManyField(settings.AUTH_USER_MODEL,
                                       related_name='favorites')
    likes = models.ManyToManyField(settings.AUTH_USER_MODEL, name='likes')
    # video = models.FileField(upload_to='media/videos/%Y/%m/%d/', verbose_name="Ютуб ссылка")
    video = models.CharField(max_length=255,
                             verbose_name="Ютуб ссылка",
                             help_text="Просмотр видео")
    category = models.ForeignKey(Category, on_delete=models.CASCADE,
                                 related_name='videos',
                                 verbose_name="Категория")
    type = models.CharField(verbose_name="Тип", choices=TYPE, max_length=20)
    status = models.CharField("Статус", max_length=20, choices=STATUS, default='3',
                              null=True, blank=True)
    create_at = models.DateTimeField(default=datetime.now,
                                     verbose_name="Дата создания")
    is_active = models.BooleanField(default=False, verbose_name="Активный")
    is_top = models.BooleanField(default=True, verbose_name="Топ")
    image = models.ImageField(upload_to='videos/', verbose_name="Обложка")
    owner = models.ForeignKey(settings.AUTH_USER_MODEL,
                              on_delete=models.CASCADE, related_name='users',
                              verbose_name="Владелец")

    class Meta:
        verbose_name = _("Видео")
        verbose_name_plural = _("Видео")

    def __str__(self):
        return self.title

    def get_views_count(self):
        return VideoViews.objects.filter(video__id=self.id).count()

    def save(self, *args, **kwargs):
        # try:
        #     this = Video.objects.get(id=self.id)
        #     if this.image != self.image:
        #         this.image.delete()
        # except:
        #     pass

        if self.status == '1':
            self.is_active = False
        if self.status == '2':
            self.is_active = True
        if self.status == '3':
            self.is_active = False

        super(Video, self).save(*args, **kwargs)
        img = Image.open(self.image)
        width, height = img.size
        if width > 1080:
            ratio = float(width / 1080)
            width = int(width / ratio)
            height = int(height / ratio)
            img = img.resize((width, height), PIL.Image.ANTIALIAS)
            img.save(self.image.path, quality=100, optimize=True)
        else:
            img.save(self.image.path, quality=100, optimize=True)


class VideoImage(models.Model):
    image = models.ImageField(verbose_name=_('Изображение'), upload_to='video/image/')
    video = models.ForeignKey(Video, verbose_name=_('Видео'),
                                  related_name='VideoImages', on_delete=models.CASCADE)

    class Meta:
        verbose_name = _('Изображение')
        verbose_name_plural = _('Список изображений')


class VideoViews(models.Model):
    video = models.ForeignKey(Video, related_name='videos', verbose_name="Видео", on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='Пользователь')
    create_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Просмотры")
        verbose_name_plural = _("Просмотры")
        unique_together = [['video', 'user']]
    
    def __str__(self):
        return f'user: {self.user}, video: {self.video}'


@receiver(pre_delete, sender=Video)
def delete_image(sender, instance, **kwargs):
    # Pass false so FileField doesn't save the model.
    instance.image.delete(False)


class Services(models.Model):
    name = models.CharField(max_length=100, verbose_name=_('Название'))
    description = models.TextField(verbose_name=_('Описание'))
    price = models.FloatField(verbose_name=_('Цена'))
    video = models.ForeignKey('Video', related_name='video_service', verbose_name=_('Видео'),
                                  on_delete=models.CASCADE)
    image = models.ImageField(verbose_name='Изображение товара', upload_to='video/service/')

    class Meta:
        verbose_name = 'Услуга и товар'
        verbose_name_plural = 'Услуги и товары'


class ServiceImage(models.Model):
    image = models.ImageField(verbose_name=_('Изображение'), upload_to='video/service/')
    service = models.ForeignKey(Services, verbose_name=_('Услуга'),
                                related_name='ServiceImages', on_delete=models.CASCADE)

    class Meta:
        verbose_name = _('Изображение')
        verbose_name_plural = _('Список изображений')


    def __str__(self):
        return self.name


class BookingServices(models.Model):
    TYPE_CHOICES = (
        ('card', 'card'),
        ('point', 'point')
    )

    entry_date = models.DateTimeField(default=datetime.now, verbose_name=_('Дата въезда'), blank=True, null=True)
    service = models.ForeignKey('Services', related_name='service', verbose_name=_('Услуга'),
                             on_delete=models.CASCADE)
    phone = models.CharField(max_length=12, verbose_name=_('Номер телефона'))
    comment = models.TextField(verbose_name=_('Коментарий'), blank=True)
    adult_count = models.IntegerField(verbose_name=_('Количество взрослых'), blank=True)
    kids_count = models.IntegerField(verbose_name=_('Количество детей'), blank=True)
    total_price = models.DecimalField(max_digits=7, decimal_places=2, verbose_name=_('Сумма брони'))
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE, related_name='booking_service_user',
                             verbose_name="Пользователь")
    accept = models.BooleanField(default=False)
    type = models.CharField(choices=TYPE_CHOICES, max_length=100)
    payment_id = models.CharField(max_length=200, blank=True)

    class Meta:
        verbose_name = _('Заявка рестаранов и услуг')
        verbose_name_plural = _('Заявки рестаранов и услуг')


class MyVideo(Video):
    class Meta:
        verbose_name = "Видео для неактивных"
        verbose_name_plural = "Видео для неактивных"
        proxy = True


class Tariff(models.Model):
    video = models.ForeignKey(Video, on_delete=models.CASCADE,
                              related_name='tariffs',
                              verbose_name="Ютуб ссылка")
    views = models.IntegerField(verbose_name="Просмотр")
    price = models.FloatField(verbose_name="Цена")

    class Meta:
        verbose_name = _("Тариф")
        verbose_name_plural = _("Тарифы")


class Comment(models.Model):
    video = models.ForeignKey(Video, on_delete=models.CASCADE,
                              related_name='comments',
                              verbose_name="Ютуб ссылка")
    text = models.TextField(verbose_name="Текст")
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE,
                             related_name='comments',
                             verbose_name="Пользователь")
    parent = models.ForeignKey('self', verbose_name="Родитель",
                               related_name='children',
                               on_delete=models.SET_NULL,
                               blank=True, null=True)
    create_at = models.DateTimeField(default=datetime.now,
                                     verbose_name="Дата создания")
    is_active = models.BooleanField(default=True, verbose_name="Активный")

    class Meta:
        verbose_name = _("Комментарий")
        verbose_name_plural = _("Комментарии")
        ordering = ('-create_at',)

    def __str__(self):
        return self.text


class FAQ(models.Model):
    question = models.TextField(verbose_name="Вопрос")
    reply = models.TextField(verbose_name="Ответ")


class Request(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE,
                                 related_name='categories',
                                 verbose_name="Категория")
    address = models.CharField(max_length=200, verbose_name="Адрес")
    phone = models.CharField(max_length=15, verbose_name="Телефон номер")
    sum = models.IntegerField(default=0, verbose_name="Цена")
    promo_code = models.CharField(max_length=40, blank=True,
                                  verbose_name="Промо код")
    create_at = models.DateTimeField(default=datetime.now,
                                     verbose_name="Дата создания")
    is_checked = models.BooleanField(default=False,
                                     verbose_name="Провереннный")

    class Meta:
        verbose_name = _("Заявка")
        verbose_name_plural = _("Заявки")


class Request2(models.Model):
    STATUS = (
    ('1', 'Отклонено'),
    ('2', 'Активно'),
    ('3', 'В ожидании')
    )

    title = models.CharField(max_length=100, verbose_name="Название")
    text = models.TextField(verbose_name="Описание")
    phone = models.CharField(max_length=16, null=True, blank=True,
                               verbose_name="Телефон номер 1")
    video = models.FileField(upload_to='videos_uploaded',
                                validators=[FileExtensionValidator(
                                    allowed_extensions=['MOV', 'avi', 'mp4', 'webm', 'mkv'])])
    is_top = models.BooleanField(default=False, verbose_name="Топ")
    category = models.ForeignKey(Category, on_delete=models.CASCADE,
                                 related_name='categories2',
                                 verbose_name="Категория")
    image = models.ImageField(upload_to='videos/', verbose_name="Обложка")
    status = models.CharField('Статус', choices=STATUS, default='3', max_length=20)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL,
                              on_delete=models.CASCADE, related_name='users2',
                              verbose_name="Владелец")
    create_at = models.DateTimeField(auto_now_add=True,
                                     verbose_name="Дата создания")

    class Meta:
            verbose_name = _("Заявка")
            verbose_name_plural = _("Заявки")
            ordering = ('-create_at',)


class VideoRequestImage(models.Model):
    image = models.ImageField(verbose_name=_('Изображение'), upload_to='video/image/')
    video = models.ForeignKey(Request2, verbose_name=_('Видео'),
                                  related_name='VideoRequestImages', on_delete=models.CASCADE)


class Banner(models.Model):
    video = models.CharField(max_length=255, null=True,
                             verbose_name="Ютуб ссылка")
    url = models.URLField(blank=True, null=True)
    image = models.ImageField(upload_to='banners/', verbose_name="Обложка")
    views = models.ManyToManyField(settings.AUTH_USER_MODEL,
                                   related_name='views')
    order = models.PositiveIntegerField(default=0)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Баннер")
        verbose_name_plural = _("Баннеры")
        ordering = ('order',)

    def __str__(self):
        return self.video

    def save(self, *args, **kwargs):
        try:
            this = Banner.objects.get(id=self.id)
            if this.image != self.image:
                this.image.delete()

        except:
            pass

        super(Banner, self).save(*args, **kwargs)
        img = Image.open(self.image)
        width, height = img.size
        if width > 1080:
            ratio = float(width / 1080)
            width = int(width / ratio)
            height = int(height / ratio)
            img = img.resize((width, height), PIL.Image.ANTIALIAS)
            img.save(self.image.path, quality=100, optimize=True)
        else:
            img.save(self.image.path, quality=100, optimize=True)


@receiver(pre_delete, sender=Banner)
def banner_image(sender, instance, **kwargs):
    # Pass false so FileField doesn't save the model.
    instance.image.delete(False)


class ViewBanner(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE,
                             related_name='banners',
                             verbose_name="Пользователь")
    banner = models.ForeignKey(Banner, on_delete=models.CASCADE,
                               related_name='banners',
                               verbose_name="Баннер видео")
    create_at = models.DateTimeField(default=datetime.now,
                                     verbose_name="Дата создания")

    class Meta:
        verbose_name = _("Просмотр история (Баннер)")
        verbose_name_plural = _("Просмотр истории (Баннер)")


class LikeBanner(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE,
                             related_name='like_banners',
                             verbose_name="Пользователь")
    banner = models.ForeignKey(Banner, on_delete=models.CASCADE,
                               related_name='like_banners',
                               verbose_name="Баннер видео")
    create_at = models.DateTimeField(default=datetime.now,
                                     verbose_name="Дата создания")

    class Meta:
        verbose_name = _("Лайк (Баннер)")
        verbose_name_plural = _("Лайк (Баннер)")
        unique_together = (('user', 'banner'),)


class ComplaintBanner(models.Model):
    TYPE_COMPLAINT = (
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
        ('4', '4'),
        ('5', '5'),
        ('6', '6'),
        ('7', '7'),
        ('8', '8'),
        ('9', '9'),
        ('10', '10'),
        ('11', '11')
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE,
                             related_name='complaint_banners',
                             verbose_name="Пользователь")
    banner = models.ForeignKey(Banner, on_delete=models.CASCADE,
                               related_name='complaint_banners',
                               verbose_name="Баннер видео")
    type = models.CharField("Типы жалоба", choices=TYPE_COMPLAINT,
                            max_length=2)
    text = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = _("Жалоб (Баннер)")
        verbose_name_plural = _("Жалоб (Баннер)")


class ViewHistory(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE,
                             related_name='histories',
                             verbose_name="Пользователь")
    bonus = models.IntegerField(default=0, verbose_name="Бонус")
    video = models.ForeignKey(Video, on_delete=models.CASCADE,
                              related_name='histories',
                              verbose_name="Ютуб ссылка")
    create_at = models.DateTimeField(default=datetime.now,
                                     verbose_name="Дата создания")

    class Meta:
        verbose_name = _("Просмотр история (Реклама))")
        verbose_name_plural = _("Просмотр истории (Реклама)")


class VideoTraining(models.Model):
    title = models.CharField(max_length=100, verbose_name="Название")
    video = models.CharField(max_length=255, null=True,
                             verbose_name="Ютуб ссылка")
    is_active = models.BooleanField(default=True, verbose_name="Активный")
    image = models.ImageField(upload_to='videos_training/',
                              verbose_name="Фотография")

    class Meta:
        verbose_name = _("Видео обучения")
        verbose_name_plural = _("Видео обучения")

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        try:
            this = VideoTraining.objects.get(id=self.id)
            if this.image != self.image:
                this.image.delete()

        except:
            pass

        super(VideoTraining, self).save(*args, **kwargs)
        img = Image.open(self.image)
        width, height = img.size
        if width > 1080:
            ratio = float(width / 1080)
            width = int(width / ratio)
            height = int(height / ratio)
            img = img.resize((width, height), PIL.Image.ANTIALIAS)
            img.save(self.image.path, quality=100, optimize=True)
        else:
            img.save(self.image.path, quality=100, optimize=True)


@receiver(pre_delete, sender=VideoTraining)
def video_training_image(sender, instance, **kwargs):
    # Pass false so FileField doesn't save the model.
    instance.image.delete(False)
