from django.db import models

from locker_server.api_orm.models.payments.country import CountryORM


class CustomerORM(models.Model):
    id = models.AutoField(primary_key=True)
    full_name = models.CharField(max_length=255, null=True)
    organization = models.CharField(max_length=128, blank=True, default="", null=True)
    address = models.CharField(max_length=255, blank=True, default="", null=True)
    city = models.CharField(max_length=128, blank=True, default="", null=True)
    state = models.CharField(max_length=128, blank=True, default="", null=True)
    postal_code = models.CharField(max_length=16, blank=True, default="", null=True)
    phone_number = models.CharField(max_length=32, blank=True, default="", null=True)
    last4 = models.CharField(max_length=10, blank=True, default="", null=True)
    brand = models.CharField(max_length=32, blank=True, default="", null=True)
    country = models.ForeignKey(CountryORM, on_delete=models.SET_NULL, related_name="customers", default=None, null=True)

    class Meta:
        db_table = 'cs_customers'

    @classmethod
    def create(cls, **data):
        """
        Create new customer object
        :param data: (dict) Customer data. It contains:
            {
              "full_name": (str) Customer full name,
              "organization": (str) Customer's organization,
              "address": (str) Customer's address,
              "city": (str) City address,
              "state": (str) State address,
              "postal_code": (str) Postal code,
              "last4": (str) Last 4 characters of customer card,
              "phone_number": (str) Customer's phone,
              "country": (str) Country code
        :return:
        """
        full_name = data.get("full_name")
        organization = data.get("organization", "")
        address = data.get("address", "")
        city = data.get("city", "")
        state = data.get("state", "")
        postal_code = data.get("postal_code", "")
        last4 = data.get("last4", "")
        phone_number = data.get("phone_number", "")
        if phone_number is not None:
            phone_number = phone_number.strip()
        country = data.get("country", None)  # This is country code
        brand = data.get("brand", "")

        new_customer = cls(
            full_name=full_name, organization=organization, address=address,
            city=city, state=state, phone_number=phone_number, postal_code=postal_code, last4=last4, brand=brand
        )
        new_customer.save()
        if (country is not None) and (country != ""):
            country_obj = CountryORM.objects.get(country_code=country)
            new_customer.country = country_obj
            new_customer.save()
        return new_customer
