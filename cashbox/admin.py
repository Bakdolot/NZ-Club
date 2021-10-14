from django.contrib import admin

from django.contrib.admin import DateFieldListFilter

from cashbox.models import *


class Pay24HistoryAdmin(admin.ModelAdmin):
    list_display = ['user', 'sum', 'create_at']
    change_list_template  = 'admin/custom_change_list.html'
    list_filter = (('create_at', DateFieldListFilter),)

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        if request.GET:
            extra_context['hello'] = sum(Pay24History.objects.filter(create_at__range=[request.GET['create_at__gte'], request.GET['create_at__lt']]).values_list('sum', flat=False))
        else:
            extra_context['hello'] = sum(Pay24History.objects.all())
        return super().changelist_view(request, extra_context=extra_context)


class CashBoxAdmin(admin.ModelAdmin):
    list_display = ['user', 'method', 'operator', 'props_number', 'amount', 'is_paid', 'create_at']
    list_display_links = list_display
    list_filter = ['method', 'operator', 'is_paid']


class TransferAdmin(admin.ModelAdmin):
    list_display = ['sender', 'receiver', 'amount', 'code', 'is_paid', 'is_read', 'create_at']
    list_display_links = list_display
    list_filter = ['sender', 'receiver', 'is_paid']


class PromoCodeAdmin(admin.ModelAdmin):
    list_display = ['user', 'code', 'create_at']
    list_display_links = list_display
    list_filter = ['user']
    search_fields = ['code']


admin.site.register(Pay24History, Pay24HistoryAdmin)
admin.site.register(CashBox, CashBoxAdmin)
admin.site.register(Transfer, TransferAdmin)
admin.site.register(PromoCode, PromoCodeAdmin)
