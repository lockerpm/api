from rest_framework import serializers

from cystack_models.models.enterprises.payments.billing_contacts import EnterpriseBillingContact


class EnterpriseBillingContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = EnterpriseBillingContact
        fields = ('id', 'created_time', 'email')
        read_only_fields = ('id', 'created_time')

    def to_representation(self, instance):
        return super(EnterpriseBillingContactSerializer, self).to_representation(instance)
