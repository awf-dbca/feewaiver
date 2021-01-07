from django.conf import settings
from ledger.accounts.models import EmailUser,Address, Profile,EmailIdentity, EmailUserAction, EmailUserLogEntry, CommunicationsLogEntry
#from feewaiver.main_models import UserSystemSettings, Document
from feewaiver.main_models import Document
from feewaiver.helpers import is_feewaiver_admin 
from rest_framework import serializers
from ledger.accounts.utils import in_dbca_domain
from ledger.payments.helpers import is_payment_admin

class DocumentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Document
        fields = ('id','description','file','name','uploaded_date')

class UserAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = (
            'id',
            'line1',
            'locality',
            'state',
            'country',
            'postcode'
        )

#class UserSystemSettingsSerializer(serializers.ModelSerializer):
#    class Meta:
#        model = UserSystemSettings
#        fields = (
#            'one_row_per_park',
#        )


class UserFilterSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = EmailUser
        fields = (
            'id',
            'last_name',
            'first_name',
            'email',
            'name'
        )

    def get_name(self, obj):
        return obj.get_full_name()


class UserSerializer(serializers.ModelSerializer):
    residential_address = UserAddressSerializer()
    personal_details = serializers.SerializerMethodField()
    address_details = serializers.SerializerMethodField()
    contact_details = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()
    is_department_user = serializers.SerializerMethodField()
    is_payment_admin = serializers.SerializerMethodField()
    system_settings= serializers.SerializerMethodField()
    is_payment_admin = serializers.SerializerMethodField()
    is_feewaiver_admin = serializers.SerializerMethodField()    

    class Meta:
        model = EmailUser
        fields = (
            'id',
            'last_name',
            'first_name',
            'email',
            'residential_address',
            'phone_number',
            'mobile_number',
            'commercialoperator_organisations',
            'personal_details',
            'address_details',
            'contact_details',
            'full_name',
            'is_department_user',
            'is_payment_admin',
            'is_staff',
            'system_settings',
            'is_commercialoperator_admin',
        )

    def get_personal_details(self,obj):
        return True if obj.last_name  and obj.first_name else False

    def get_address_details(self,obj):
        return True if obj.residential_address else False

    def get_contact_details(self,obj):
        if obj.mobile_number and obj.email:
            return True
        elif obj.phone_number and obj.email:
            return True
        elif obj.mobile_number and obj.phone_number:
            return True
        else:
            return False

    def get_full_name(self, obj):
        return obj.get_full_name()

    def get_is_department_user(self, obj):
        if obj.email:
            return in_dbca_domain(obj)
        else:
            return False

    def get_is_payment_admin(self, obj):
        return is_payment_admin(obj)

    def get_system_settings(self, obj):
        try:
            user_system_settings = obj.system_settings.first()
            serialized_settings = UserSystemSettingsSerializer(
                user_system_settings).data
            return serialized_settings
        except:
            return None

    def get_is_feewaiver_admin(self, obj):
        request = self.context['request'] if self.context else None
        if request:
            return is_commercialoperator_admin(request)
        return False


class PersonalSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailUser
        fields = (
            'id',
            'last_name',
            'first_name',
        )

class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailUser
        fields = (
            'id',
            'email',
            'phone_number',
            'mobile_number',
        )

    def validate(self, obj):
        #Mobile and phone number for dbca user are updated from active directory so need to skip these users from validation.
        domain=None
        if obj['email']:
            domain = obj['email'].split('@')[1]
        if domain in settings.DEPT_DOMAINS:
            return obj
        else:
            if not obj.get('phone_number') and not obj.get('mobile_number'):
                raise serializers.ValidationError('You must provide a mobile/phone number')
        return obj

class EmailUserActionSerializer(serializers.ModelSerializer):
    who = serializers.CharField(source='who.get_full_name')

    class Meta:
        model = EmailUserAction
        fields = '__all__'

class EmailUserCommsSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailUserLogEntry
        fields = '__all__'

class CommunicationLogEntrySerializer(serializers.ModelSerializer):
    customer = serializers.PrimaryKeyRelatedField(queryset=EmailUser.objects.all(),required=False)
    documents = serializers.SerializerMethodField()
    class Meta:
        model = CommunicationsLogEntry
        fields = (
            'id',
            'customer',
            'to',
            'fromm',
            'cc',
            'log_type',
            'reference',
            'subject'
            'text',
            'created',
            'staff',
            'emailuser',
            'documents'
        )

    def get_documents(self,obj):
        return [[d.name,d._file.url] for d in obj.documents.all()]

class EmailUserLogEntrySerializer(CommunicationLogEntrySerializer):
    documents = serializers.SerializerMethodField()
    class Meta:
        model = EmailUserLogEntry
        fields = '__all__'
        read_only_fields = (
            'customer',
        )

    def get_documents(self,obj):
        return [[d.name,d._file.url] for d in obj.documents.all()]

