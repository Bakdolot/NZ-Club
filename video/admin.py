from django.contrib import admin
from django.db.models import Q
from django.http.response import HttpResponseRedirect
from accounts.models import User
from video.models import *
from adminsortable2.admin import SortableAdminMixin
from django.contrib import messages
from nested_inline.admin import NestedModelAdmin, NestedTabularInline


class ServiceImageInline(NestedTabularInline):
    model = ServiceImage
    extra = 1


class ServiceInline(NestedTabularInline):
    model = Services
    extra = 1
    inlines = [ServiceImageInline]

    def has_add_permission(self, request, obj):
        return True

    def has_delete_permission(self, request, obj=None):
        return True

    def has_change_permission(self, request, obj=None):
        return True

    def has_view_permission(self, request, obj=None):
        return True


class TariffInline(admin.TabularInline):
    model = Tariff

    def has_add_permission(self, request, obj):
        return True

    def has_delete_permission(self, request, obj=None):
        return True

    def has_change_permission(self, request, obj=None):
        return True

    def has_view_permission(self, request, obj=None):
        return True


class ImageInline(admin.TabularInline):
    model = VideoImage
    fields = (('image', 'download_img'), 'video')
    readonly_fields = ('download_img', )

    def has_add_permission(self, request, obj):
        return True

    def has_delete_permission(self, request, obj=None):
        return True

    def has_change_permission(self, request, obj=None):
        return True

    def has_view_permission(self, request, obj=None):
        return True
    
    def download_img(self, obj):
        return mark_safe(f'<a href="{obj.image.url}" download >скачать</a>')

    download_img.short_description = 'Скачать изображение'


@admin.register(Video)
class VideoAdmin(NestedModelAdmin):
    list_display = ['owner', 'title', 'category', 'status', 'is_active',
                    'get_owner_region']
    list_select_related = ('owner', 'category')
    list_display_links = ['owner', 'title', 'category']
    search_fields = ['title', 'text']
    list_filter = ['owner__username']
    exclude = ('favorites', 'views', 'is_active', 'watched_videos')
    list_per_page = 50
    autocomplete_fields = ['owner']
    # list_editable = ['status', ]
    inlines = [ServiceInline, TariffInline, ImageInline]
    change_form_template = 'admin/changeform.html'
    save_on_top = True

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(owner=request.user)

    def make_activation(self, request, queryset):
        queryset.update(status='2')
    
    def response_change(self, request, obj):
        if request.user.is_superuser:
            video = Video.objects.get(id=obj.id)
            if 'approve' in request.POST:
                if video.video == 'null':
                    self.message_user(request, 'Вставьте ютуб ссылку в поле "Ютуб ссылка"', level=messages.ERROR)
                    return HttpResponseRedirect('.')
                video.status, video.is_active = '2', True
                video.save()
                self.message_user(request, 'Видео активна')
                return HttpResponseRedirect('.')
            elif 'disapprove' in request.POST:
                if not obj.video:
                    video.video, video.type = 'null', '1'
                video.status, video.is_active = '1', False
                video.save()
                self.message_user(request, 'Видео отключен')
                return HttpResponseRedirect('.')
        return super().response_change(request, obj)

    def get_owner_region(self, obj):
        return f'{obj.owner.profile.get_region_display()}'

    make_activation.short_description = 'Активировать'
    get_owner_region.short_description = 'Регион'

    def get_fields(self, request, obj=None):
        if request.user.is_superuser:
            return ['title', 'text', 'phone_1', 'phone_2', 'phone_3',
                    'instagram', 'facebook', 'web_site',
                    'video', 'category', 'type', 'is_top', 'image', 'owner',
                    'status']
        else:
            return ['title', 'text', 'phone_1', 'phone_2', 'phone_3',
                    'instagram', 'facebook', 'web_site',
                    'video', 'category', 'type', 'image', 'owner', ]

    def get_inline_instances(self, request, obj=None):
        if request.user.is_superuser:
            return [inline(self.model, self.admin_site) for inline in
                    self.inlines]
        return []

    def save_model(self, request, obj, form, change):
        if request.user.is_superuser:
            # do push notif soon
            obj.is_active = True
            super().save_model(request, obj, form, change)
        else:
            obj.status = '3'
            obj.is_active = False
            super().save_model(request, obj, form, change)


@admin.register(BookingServices)
class BookingRequestAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'entry_date', 'get_video_name','service', 'phone', 'accept']
    list_display_links = ['id', 'user', 'entry_date', 'service', 'phone', 'accept']

    def get_video_name(self, obj):
        return obj.service.video

    get_video_name.short_description = 'названия видео'


@admin.register(MyVideo)
class MyVideoAdmin(admin.ModelAdmin):
    list_display = ['owner', 'title', 'category', 'status', 'is_active']
    list_display_links = ['owner', 'title', 'category']
    search_fields = ['title', 'text']
    list_filter = ['owner__username']
    exclude = ('favorites', 'views', 'is_active', 'watched_videos')
    list_per_page = 50
    autocomplete_fields = ['owner', ]
    list_select_related = ['owner']
    # list_editable = ['status', ]
    inlines = [TariffInline]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(owner=request.user)

    def make_activation(self, request, queryset):
        queryset.update(status='2')

    make_activation.short_description = 'Активировать'

    def get_fields(self, request, obj=None):
        if request.user.is_superuser:
            return ['title', 'text', 'phone_1', 'phone_2', 'phone_3',
                    'instagram', 'facebook', 'web_site',
                    'video', 'category', 'type', 'is_top', 'image', 'owner']
        else:
            return ['title', 'text', 'phone_1', 'phone_2', 'phone_3',
                    'instagram', 'facebook', 'web_site',
                    'video', 'category', 'type', 'image', 'owner', ]

    def get_inline_instances(self, request, obj=None):
        if request.user.is_superuser:
            return [inline(self.model, self.admin_site) for inline in
                    self.inlines]
        return []

    def save_model(self, request, obj, form, change):
        obj.status = '2'
        obj.is_active = True
        super().save_model(request, obj, form, change)


@admin.register(Category)
class CategoryAdmin(SortableAdminMixin, admin.ModelAdmin):
    pass


class CommentAdmin(admin.ModelAdmin):
    list_display = ['user', 'text', 'create_at']
    search_fields = ['text']


class FAQAdmin(admin.ModelAdmin):
    list_display = ['question']
    search_fields = ['question', 'reply']


class ImageRequestInline(admin.TabularInline):
    model = VideoRequestImage
    fields = ('image', 'video', 'get_img')
    readonly_fields = ('get_img', )

    def has_add_permission(self, request, obj):
        return True

    def has_delete_permission(self, request, obj=None):
        return True

    def has_change_permission(self, request, obj=None):
        return True

    def has_view_permission(self, request, obj=None):
        return True
    
    def get_img(self, obj):
        return mark_safe(f'<img src={obj.image.url} style="width: 150px; height: fit-content; object-fit: contain;" />')

    get_img.short_description = 'изображение'


@admin.register(Request2)
class Request2Admin(admin.ModelAdmin):
    list_display = ['owner', 'title', 'category', 'status',]
    readonly_fields = ['create_at', 'download_video']
    list_display_links = ['owner', 'title', 'category']
    search_fields = ['title', 'text']
    list_filter = ['owner__username']
    change_form_template = 'admin/RequestChangeForm.html'
    inlines = [ImageRequestInline]
    save_on_top = True

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(owner=request.user)

    def response_change(self, request, obj):
        if request.user.is_superuser:
            req = Request2.objects.get(id=obj.id)
            if 'approve' in request.POST:
                video = Video.objects.create(title=obj.title,
                                    text=obj.text,
                                    phone_1=obj.phone,
                                    is_top=obj.is_top,
                                    category=obj.category,
                                    image=obj.image,
                                    owner=obj.owner
                                    )
                images = VideoRequestImage.objects.filter(video__id=obj.id)
                if images:
                    for image in images:
                        ad_image = VideoImage(video=video, image=image)
                        ad_image.save()
                    images.delete()
                req.delete()
                self.message_user(request, 'Видео создан')
                return HttpResponseRedirect('/admin/video/request2/')
            elif 'disapprove' in request.POST:
                images = VideoRequestImage.objects.filter(video__id=obj.id)
                if images:
                    images.delete()
                req.delete()
                self.message_user(request, 'Запрос откланен')
                return HttpResponseRedirect('/admin/video/request2/')
        return super().response_change(request, obj)

    def get_owner_region(self, obj):
        return f'{obj.owner.profile.get_region_display()}'

    def download_video(self, obj):
        return mark_safe(f'<a href="{obj.video.url}" id="down98" download >скачать</a>')

    download_video.short_description = 'скачать видео'
    get_owner_region.short_description = 'Регион'

    def get_fields(self, request, obj=None):
        if request.user.is_superuser:
            return ['title', 'text', 'phone', ('video', 'download_video'), 'is_top', 'category', 'image', 'create_at', 'status', 'owner']
        else:
            return ['title', 'text', 'phone', ('video', 'download_video'), 'category', 'image', 'owner', 'create_at']


@admin.register(ViewHistory)
class ViewHistoryAdmin(admin.ModelAdmin):
    list_display = ['user', 'bonus', 'video', 'create_at']
    list_display_links = list_display
    list_filter = ['user', 'video']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(video__owner=request.user)


class ViewBannerAdmin(admin.ModelAdmin):
    list_display = ['user', 'banner', 'create_at']
    list_display_links = list_display
    list_filter = ['user', 'banner']


class VideoTrainingAdmin(admin.ModelAdmin):
    list_display = ['title', 'video']
    list_display_links = list_display


@admin.register(Banner)
class BannerAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ['id', 'image', 'video']
    list_display_links =  ['id', 'image', 'video']
    exclude = ('views',)

    # def has_add_permission(self, request):
    #     if len(Banner.objects.all()) > 12:
    #         return False
    #     return True


admin.site.register(Comment, CommentAdmin)
admin.site.register(FAQ, FAQAdmin)
admin.site.register(ViewBanner, ViewBannerAdmin)
admin.site.register(VideoTraining, VideoTrainingAdmin)
admin.site.register(ComplaintBanner)
