from django.contrib import admin

from cashbox.models import *


class Pay24HistoryAdmin(admin.ModelAdmin):
    list_display = ['user', 'sum', 'create_at', 'get_all_sum']
    readonly_fields = ['get_all_sum']

    def get_all_sum(self, obj):
        query = Pay24History.objects.filter(user=obj.user).values_list('sum', flat=True)
        return sum(query)
    
    get_all_sum.short_description = 'Сумма всех пополнений'
    


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
