from rest_framework import serializers
from .models import Account, Address, BankAccount, SuperFund, EmergencyContact, Licenses, TFD

class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ('first_name','last_name','gender','email','number','color','date_of_birth','promotions','terms_conditions','privacy_policy','job_title')
        read_only_fields = ('email','terms_conditions','privacy_policy')

class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ('address','house_no','street','suburb','postcode','state','country')

class BankAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankAccount
        fields = ('account_type','account_bsb','account_number','account_name','bank_name')

class SuperFundSerializer(serializers.ModelSerializer):
    class Meta:
        model = SuperFund
        fields = ('fund_name','product_code','member_number','pay_to_fund')

class EContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmergencyContact
        fields = ('name','relationship','address','number')

class LicensesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Licenses
        fields = ('name','file','filename','filesize','obtained_date','expiry_date','date_created')
        read_only_fields = ('date_created',)

class TfdSerializer(serializers.ModelSerializer):
    class Meta:
        model = TFD
        fields = ('number','previous_name','employment_type','australian_resident','tax_free_threshold','is_approved_holiday','pensioners_tax_offset','overseas_forces','accumulated_stsl_debt','seasonal_worker','withholding_variation','medicare_levy','date_signed','lodgement_status')
