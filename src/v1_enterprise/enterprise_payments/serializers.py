from rest_framework import serializers

from cystack_models.models.payments.payments import Payment


class InvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ('id', 'payment_id', 'created_time', 'total_price', 'discount', 'status', 'payment_method',
                  'duration', 'currency')
        read_only_field = ('id', 'created_time', 'total_price', 'discount', 'status', 'payment_method',
                           'duration', 'currency', )

    def to_representation(self, instance):
        return super(InvoiceSerializer, self).to_representation(instance)


