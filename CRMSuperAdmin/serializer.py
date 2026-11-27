import json
from uuid import uuid4
from decimal import Decimal, ROUND_HALF_UP
import time
from pyexpat import model
from rest_framework import serializers
from django.db import transaction
from django.db.models import Q
from django.contrib.auth.models import Group, Permission
from .models import *
from CRMUserAdmin.models import *




class Addonserializer(serializers.ModelSerializer):
    Product_Compatibility_Type = serializers.ChoiceField(
        choices=('compatible', 'incompatible'), required=False, write_only=True,
    )

    @transaction.atomic
    def create(self, validated_data):
        rule_type = validated_data.pop('Product_Compatibility_Type', 'compatible')
        products = validated_data.get('Products', [])
        addon = super().create(validated_data)
        self.sync_product_rules(addon, products, set(), rule_type)
        return addon

    @transaction.atomic
    def update(self, instance, validated_data):
        addon = AddonMaster.objects.select_for_update().get(pk=instance.pk)
        products = validated_data.get('Products')
        previous_ids = set(addon.Products.values_list('pk', flat=True)) if products is not None else set()
        addon = super().update(addon, validated_data)
        if products is not None:
            self.sync_product_rules(addon, products, previous_ids, 'compatible')
        return addon

    def sync_product_rules(self, addon, products, previous_ids, rule_type):
        selected = {product.pk: product for product in products}
        if not (selected or previous_ids):
            return
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        actor_id = user.pk if getattr(user, 'is_authenticated', False) else addon.Updated_By_id or addon.Created_By_id
        if not actor_id:
            raise serializers.ValidationError({'Products': 'A valid user is required to update compatibility rules.'})

        today = timezone.localdate()
        rules = {rule.Product_id: rule for rule in AddonProductCompatibility.objects.select_for_update().filter(
            Addon=addon, Product_id__in=selected.keys() | previous_ids,
        )}
        for product_id in previous_ids - selected.keys():
            rule = rules.get(product_id)
            if rule and not rule.Is_Deleted and rule.Compatibility_Type != 'incompatible' and rule.Is_Compatible:
                rule.Is_Deleted = True
                rule.Is_Active = False
                rule.Updated_By_id = actor_id
                rule.Updated_Date = today
                rule.save(update_fields=['Is_Deleted', 'Is_Active', 'Updated_By', 'Updated_Date'])

        for product_id, product in selected.items():
            rule = rules.get(product_id)
            if rule and rule_type == 'compatible' and rule.Is_Compatible and rule.Compatibility_Type != 'incompatible':
                if rule.Is_Active and not rule.Is_Deleted:
                    continue
                rule.Is_Active = True
                rule.Is_Deleted = False
                rule.Updated_By_id = actor_id
                rule.Updated_Date = today
                rule.save(update_fields=['Is_Active', 'Is_Deleted', 'Updated_By', 'Updated_Date'])
                continue

            fields = {
                'Addon_Name': addon.Addon_Name, 'Product_Name': product.Product_Name,
                'Compatibility_Type': rule_type, 'Is_Compatible': rule_type == 'compatible',
                'Is_Active': True, 'Is_Deleted': False, 'Updated_By_id': actor_id, 'Updated_Date': today,
            }
            if rule:
                for name, value in fields.items():
                    setattr(rule, name, value)
                rule.save(update_fields=fields.keys())
            else:
                AddonProductCompatibility.objects.create(
                    Addon=addon, Product=product, Created_By_id=actor_id, **fields,
                )

        if rule_type == 'incompatible':
            addon.Products.remove(*selected.keys())

    Started_Date = serializers.DateField(required=False, default=date.today)
    product_name = serializers.SerializerMethodField(read_only=True)
    product_code = serializers.SerializerMethodField(read_only=True)
    products_details = serializers.SerializerMethodField(read_only=True)
    plans_details = serializers.SerializerMethodField(read_only=True)
    created_by_name = serializers.SerializerMethodField(read_only=True)
    updated_by_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = AddonMaster
        fields = '__all__'

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if self.instance is not None and 'Product_Compatibility_Type' in attrs:
            raise serializers.ValidationError({'Product_Compatibility_Type': 'Edit existing rules in Product Compatibility.'})
        if 'Product_Compatibility_Type' in attrs:
            request = self.context.get('request')
            if request is None or not request.user.is_authenticated:
                raise serializers.ValidationError({'Product_Compatibility_Type': 'Sign in before creating rules.'})
        if any(product.Is_Deleted for product in attrs.get('Products', [])):
            raise serializers.ValidationError({'Products': 'Select available products.'})
        if self.instance is not None and 'Trial_Available' not in attrs and 'Trial_Days' not in attrs:
            return attrs

        available = attrs.get('Trial_Available', getattr(self.instance, 'Trial_Available', False))
        days = attrs.get('Trial_Days', getattr(self.instance, 'Trial_Days', 0))
        if available and days < 1:
            raise serializers.ValidationError({'Trial_Days': 'Enter at least one day for an enabled trial.'})
        if not available:
            attrs['Trial_Days'] = 0
        return attrs

    def to_internal_value(self, data):
        if hasattr(data, 'dict'):
            data = data.dict()
        elif hasattr(data, 'copy'):
            data = data.copy()

        # Backward compatibility: Addon_Id mapped to Addon_Code
        if 'Addon_Id' in data and not data.get('Addon_Code'):
            data['Addon_Code'] = data['Addon_Id']

        # Products resolution (can be list, single string, int ID, JSON string)
        prod_val = None
        if 'Products' in data:
            prod_val = data.pop('Products')
        elif 'products' in data:
            prod_val = data.pop('products')
        elif 'Product' in data:
            prod_val = data.pop('Product')
        elif 'product' in data:
            prod_val = data.pop('product')

        if prod_val is not None:
            if isinstance(prod_val, str):
                try:
                    prod_val = json.loads(prod_val)
                except Exception:
                    prod_val = [p.strip() for p in prod_val.split(',') if p.strip()]
            if not isinstance(prod_val, list):
                prod_val = [prod_val] if prod_val else []

            resolved_prod_ids = []
            for item in prod_val:
                if isinstance(item, int) or (isinstance(item, str) and item.isdigit()):
                    resolved_prod_ids.append(int(item))
                elif isinstance(item, str) and item:
                    prod = ProductMaster.objects.filter(
                        Q(Product_Code__iexact=item) | Q(Product_Name__iexact=item)
                    ).first()
                    if prod:
                        resolved_prod_ids.append(prod.id)
                elif hasattr(item, 'id'):
                    resolved_prod_ids.append(item.id)
            data['Products'] = resolved_prod_ids

        # Cloudflare_Public_Id resolution (supports list of IDs, JSON string, or single ID)
        if 'Cloudflare_Public_Id' in data:
            cf_val = data['Cloudflare_Public_Id']
            if isinstance(cf_val, str):
                try:
                    cf_val = json.loads(cf_val)
                except Exception:
                    cf_val = [c.strip() for c in cf_val.split(',') if c.strip()]
            if not isinstance(cf_val, list):
                cf_val = [cf_val] if cf_val else []
            data['Cloudflare_Public_Id'] = cf_val

        # Features resolution
        if 'Features' in data and isinstance(data['Features'], str):
            try:
                data['Features'] = json.loads(data['Features'])
            except Exception:
                data['Features'] = [f.strip() for f in data['Features'].split(',') if f.strip()]

        # Plans resolution (can be list, stringified JSON, or comma-separated string)
        if 'Plans' in data or 'plans' in data or 'Plan_Id' in data:
            plans_val = data.get('Plans') if 'Plans' in data else (data.get('plans') or data.get('Plan_Id'))
            if isinstance(plans_val, str):
                try:
                    plans_val = json.loads(plans_val)
                except Exception:
                    plans_val = [p.strip() for p in plans_val.split(',') if p.strip()]
            if not isinstance(plans_val, list):
                plans_val = [plans_val] if plans_val else []

            resolved_plan_ids = []
            for p in plans_val:
                if isinstance(p, int) or (isinstance(p, str) and p.isdigit()):
                    resolved_plan_ids.append(int(p))
                elif isinstance(p, str) and p:
                    plan_obj = Plan.objects.filter(Q(Plan_Id__iexact=p) | Q(Plan_Name__iexact=p)).first()
                    if plan_obj:
                        resolved_plan_ids.append(plan_obj.id)
            data['Plans'] = resolved_plan_ids

        # Default fallback for Organization_Id, Created_By, Updated_By if missing
        if not data.get('Organization_Id'):
            first_org = Userorganizationmaster.objects.first()
            if first_org:
                data['Organization_Id'] = first_org.id
        if not data.get('Created_By'):
            first_user = UserAdmin.objects.first()
            if first_user:
                data['Created_By'] = first_user.id
        if not data.get('Updated_By'):
            data['Updated_By'] = data.get('Created_By')

        return super().to_internal_value(data)

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        # Ensure backwards-compatibility for frontend / consumers
        ret['Addon_Id'] = instance.Addon_Code
        prods = list(instance.Products.all())
        if prods:
            ret['Product'] = ", ".join([p.Product_Name or p.Product_Code for p in prods if (p.Product_Name or p.Product_Code)])
            ret['Product_id'] = prods[0].id
        else:
            ret['Product'] = None
            ret['Product_id'] = None
        return ret

    def get_product_name(self, obj):
        try:
            prods = list(obj.Products.all())
            return ", ".join([p.Product_Name for p in prods if p.Product_Name]) if prods else None
        except Exception:
            return None

    def get_product_code(self, obj):
        try:
            prods = list(obj.Products.all())
            return ", ".join([p.Product_Code for p in prods if p.Product_Code]) if prods else None
        except Exception:
            return None

    def get_products_details(self, obj):
        try:
            return [
                {
                    "id": p.id,
                    "Product_Id": p.Product_Id,
                    "Product_Code": p.Product_Code,
                    "Product_Name": p.Product_Name,
                }
                for p in obj.Products.all()
            ]
        except Exception:
            return []

    def get_plans_details(self, obj):
        try:
            return [
                {
                    "id": p.id,
                    "Plan_Id": p.Plan_Id,
                    "Plan_Name": p.Plan_Name or p.Plan_Id,
                }
                for p in obj.Plans.all()
            ]
        except Exception:
            return []

    def get_created_by_name(self, obj):
        try:
            if obj.Created_By:
                first = getattr(obj.Created_By, 'First_Name', '') or ''
                last = getattr(obj.Created_By, 'Last_Name', '') or ''
                full = f"{first} {last}".strip()
                return full or getattr(obj.Created_By, 'username', '')
        except Exception:
            pass
        return None

    def get_updated_by_name(self, obj):
        try:
            if obj.Updated_By:
                first = getattr(obj.Updated_By, 'First_Name', '') or ''
                last = getattr(obj.Updated_By, 'Last_Name', '') or ''
                full = f"{first} {last}".strip()
                return full or getattr(obj.Updated_By, 'username', '')
        except Exception:
            pass
        return None


class ProductCategorySerializer(serializers.ModelSerializer):
    created_by_name = serializers.SerializerMethodField(read_only=True)
    updated_by_name = serializers.SerializerMethodField(read_only=True)
    organization_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ProductCategory
        fields = '__all__'

    def to_internal_value(self, data):
        if hasattr(data, 'dict'):
            data = data.dict()
        elif hasattr(data, 'copy'):
            data = data.copy()

        # Handle Category_Id / Category_Code mapping
        if 'Category_Id' in data and not data.get('Category_Code'):
            data['Category_Code'] = data['Category_Id']
        elif 'Category_Code' in data and not data.get('Category_Id'):
            data['Category_Id'] = data['Category_Code']

        # Default fallback for Organization_Id, Created_By, Updated_By if missing
        if not data.get('Organization_Id'):
            first_org = Userorganizationmaster.objects.first()
            if first_org:
                data['Organization_Id'] = first_org.id
        if not data.get('Created_By'):
            first_user = UserAdmin.objects.first()
            if first_user:
                data['Created_By'] = first_user.id
        if not data.get('Updated_By'):
            data['Updated_By'] = data.get('Created_By')

        return super().to_internal_value(data)

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        cat_id = getattr(instance, 'Category_Id', None) or getattr(instance, 'Category_Code', None)
        ret['Category_Id'] = cat_id
        if not ret.get('Category_Code'):
            ret['Category_Code'] = cat_id
        return ret

    def get_created_by_name(self, obj):
        try:
            if obj.Created_By:
                first = getattr(obj.Created_By, 'First_Name', '') or ''
                last = getattr(obj.Created_By, 'Last_Name', '') or ''
                full = f"{first} {last}".strip()
                return full or getattr(obj.Created_By, 'username', '')
        except Exception:
            pass
        return None

    def get_updated_by_name(self, obj):
        try:
            if obj.Updated_By:
                first = getattr(obj.Updated_By, 'First_Name', '') or ''
                last = getattr(obj.Updated_By, 'Last_Name', '') or ''
                full = f"{first} {last}".strip()
                return full or getattr(obj.Updated_By, 'username', '')
        except Exception:
            pass
        return None

    def get_organization_name(self, obj):
        try:
            if obj.Organization_Id:
                return getattr(obj.Organization_Id, 'Organization_Name', None) or str(obj.Organization_Id)
        except Exception:
            pass
        return None


class ProductFeatureSerializer(serializers.ModelSerializer):
    created_by_name = serializers.SerializerMethodField(read_only=True)
    updated_by_name = serializers.SerializerMethodField(read_only=True)
    organization_name = serializers.SerializerMethodField(read_only=True)
    product_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ProductFeature
        fields = '__all__'

    def to_internal_value(self, data):
        if hasattr(data, 'dict'):
            data = data.dict()
        elif hasattr(data, 'copy'):
            data = data.copy()

        # Handle Feature_Id / Feature_Code mapping
        if 'Feature_Id' in data and not data.get('Feature_Code'):
            data['Feature_Code'] = data['Feature_Id']
        elif 'Feature_Code' in data and not data.get('Feature_Id'):
            data['Feature_Id'] = data['Feature_Code']

        # Product resolution if string or dict
        if 'Product_Id' in data or 'Product' in data or 'product_id' in data:
            prod_val = data.get('Product_Id') or data.get('Product') or data.get('product_id')
            if isinstance(prod_val, str) and not prod_val.isdigit():
                prod = ProductMaster.objects.filter(Q(Product_Code__iexact=prod_val) | Q(Product_Name__iexact=prod_val)).first()
                if prod:
                    data['Product_Id'] = prod.id
            elif isinstance(prod_val, int) or (isinstance(prod_val, str) and prod_val.isdigit()):
                data['Product_Id'] = int(prod_val)
            elif hasattr(prod_val, 'id'):
                data['Product_Id'] = prod_val.id

        # Default fallback for Organization_Id, Created_By, Updated_By if missing
        if not data.get('Organization_Id'):
            first_org = Userorganizationmaster.objects.first()
            if first_org:
                data['Organization_Id'] = first_org.id
        if not data.get('Created_By'):
            first_user = UserAdmin.objects.first()
            if first_user:
                data['Created_By'] = first_user.id
        if not data.get('Updated_By'):
            data['Updated_By'] = data.get('Created_By')

        return super().to_internal_value(data)

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        feat_id = getattr(instance, 'Feature_Id', None) or getattr(instance, 'Feature_Code', None)
        ret['Feature_Id'] = feat_id
        if not ret.get('Feature_Code'):
            ret['Feature_Code'] = feat_id
        return ret

    def get_created_by_name(self, obj):
        try:
            if obj.Created_By:
                first = getattr(obj.Created_By, 'First_Name', '') or ''
                last = getattr(obj.Created_By, 'Last_Name', '') or ''
                full = f"{first} {last}".strip()
                return full or getattr(obj.Created_By, 'username', '')
        except Exception:
            pass
        return None

    def get_updated_by_name(self, obj):
        try:
            if obj.Updated_By:
                first = getattr(obj.Updated_By, 'First_Name', '') or ''
                last = getattr(obj.Updated_By, 'Last_Name', '') or ''
                full = f"{first} {last}".strip()
                return full or getattr(obj.Updated_By, 'username', '')
        except Exception:
            pass
        return None

    def get_organization_name(self, obj):
        try:
            if obj.Organization_Id:
                return getattr(obj.Organization_Id, 'Organization_Name', None) or str(obj.Organization_Id)
        except Exception:
            pass
        return None

    def get_product_name(self, obj):
        try:
            if obj.Product_Id:
                return getattr(obj.Product_Id, 'Product_Name', None) or str(obj.Product_Id)
        except Exception:
            pass
        return None


class PlanFeatureSerializer(serializers.ModelSerializer):
    created_by_name = serializers.SerializerMethodField(read_only=True)
    updated_by_name = serializers.SerializerMethodField(read_only=True)
    organization_name = serializers.SerializerMethodField(read_only=True)
    plan_name = serializers.SerializerMethodField(read_only=True)
    feature_name = serializers.SerializerMethodField(read_only=True)
    feature_code = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = PlanFeature
        fields = '__all__'

    def to_internal_value(self, data):
        if hasattr(data, 'dict'):
            data = data.dict()
        elif hasattr(data, 'copy'):
            data = data.copy()

        # Resolve Plan_Id
        if 'Plan_Id' in data and isinstance(data['Plan_Id'], str) and not data['Plan_Id'].isdigit():
            p = Plan.objects.filter(Q(Plan_Id__iexact=data['Plan_Id']) | Q(Plan_Name__iexact=data['Plan_Id'])).first()
            if p:
                data['Plan_Id'] = p.id
        elif 'Plan' in data and 'Plan_Id' not in data:
            val = data.get('Plan')
            if isinstance(val, str) and not val.isdigit():
                p = Plan.objects.filter(Q(Plan_Id__iexact=val) | Q(Plan_Name__iexact=val)).first()
                if p:
                    data['Plan_Id'] = p.id
            elif isinstance(val, (int, str)) and str(val).isdigit():
                data['Plan_Id'] = int(val)

        # Resolve Feature_Id
        if 'Feature_Id' in data and isinstance(data['Feature_Id'], str) and not data['Feature_Id'].isdigit():
            f = ProductFeature.objects.filter(Q(Feature_Id__iexact=data['Feature_Id']) | Q(Feature_Code__iexact=data['Feature_Id']) | Q(Feature_Name__iexact=data['Feature_Id'])).first()
            if f:
                data['Feature_Id'] = f.id
        elif 'Feature' in data and 'Feature_Id' not in data:
            val = data.get('Feature')
            if isinstance(val, str) and not val.isdigit():
                f = ProductFeature.objects.filter(Q(Feature_Id__iexact=val) | Q(Feature_Code__iexact=val) | Q(Feature_Name__iexact=val)).first()
                if f:
                    data['Feature_Id'] = f.id
            elif isinstance(val, (int, str)) and str(val).isdigit():
                data['Feature_Id'] = int(val)

        # Default fallback for Organization_Id, Created_By, Updated_By if missing
        if not data.get('Organization_Id'):
            first_org = Userorganizationmaster.objects.first()
            if first_org:
                data['Organization_Id'] = first_org.id
        if not data.get('Created_By'):
            first_user = UserAdmin.objects.first()
            if first_user:
                data['Created_By'] = first_user.id
        if not data.get('Updated_By'):
            data['Updated_By'] = data.get('Created_By')

        return super().to_internal_value(data)

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['PlanFeature_Id'] = getattr(instance, 'PlanFeature_Id', None)
        return ret

    def get_created_by_name(self, obj):
        try:
            if obj.Created_By:
                first = getattr(obj.Created_By, 'First_Name', '') or ''
                last = getattr(obj.Created_By, 'Last_Name', '') or ''
                full = f"{first} {last}".strip()
                return full or getattr(obj.Created_By, 'username', '')
        except Exception:
            pass
        return None

    def get_updated_by_name(self, obj):
        try:
            if obj.Updated_By:
                first = getattr(obj.Updated_By, 'First_Name', '') or ''
                last = getattr(obj.Updated_By, 'Last_Name', '') or ''
                full = f"{first} {last}".strip()
                return full or getattr(obj.Updated_By, 'username', '')
        except Exception:
            pass
        return None

    def get_organization_name(self, obj):
        try:
            if obj.Organization_Id:
                return getattr(obj.Organization_Id, 'Organization_Name', None) or str(obj.Organization_Id)
        except Exception:
            pass
        return None

    def get_plan_name(self, obj):
        try:
            if obj.Plan_Id:
                return getattr(obj.Plan_Id, 'Plan_Name', None) or str(obj.Plan_Id)
        except Exception:
            pass
        return None

    def get_feature_name(self, obj):
        try:
            if obj.Feature_Id:
                return getattr(obj.Feature_Id, 'Feature_Name', None) or str(obj.Feature_Id)
        except Exception:
            pass
        return None

    def get_feature_code(self, obj):
        try:
            if obj.Feature_Id:
                return getattr(obj.Feature_Id, 'Feature_Code', None) or str(obj.Feature_Id)
        except Exception:
            pass
        return None


class PlanLimitSerializer(serializers.ModelSerializer):
    created_by_name = serializers.SerializerMethodField(read_only=True)
    updated_by_name = serializers.SerializerMethodField(read_only=True)
    organization_name = serializers.SerializerMethodField(read_only=True)
    plan_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = PlanLimit
        fields = '__all__'

    def to_internal_value(self, data):
        if hasattr(data, 'dict'):
            data = data.dict()
        elif hasattr(data, 'copy'):
            data = data.copy()

        # Handle PlanLimit_Id / Limit_Code mapping
        if 'PlanLimit_Id' in data and not data.get('Limit_Code'):
            data['Limit_Code'] = data['PlanLimit_Id']

        # Resolve Plan_Id
        if 'Plan_Id' in data and isinstance(data['Plan_Id'], str) and not data['Plan_Id'].isdigit():
            p = Plan.objects.filter(Q(Plan_Id__iexact=data['Plan_Id']) | Q(Plan_Name__iexact=data['Plan_Id'])).first()
            if p:
                data['Plan_Id'] = p.id
        elif 'Plan' in data and 'Plan_Id' not in data:
            val = data.get('Plan')
            if isinstance(val, str) and not val.isdigit():
                p = Plan.objects.filter(Q(Plan_Id__iexact=val) | Q(Plan_Name__iexact=val)).first()
                if p:
                    data['Plan_Id'] = p.id
            elif isinstance(val, (int, str)) and str(val).isdigit():
                data['Plan_Id'] = int(val)

        # Default fallback for Organization_Id, Created_By, Updated_By if missing
        if not data.get('Organization_Id'):
            first_org = Userorganizationmaster.objects.first()
            if first_org:
                data['Organization_Id'] = first_org.id
        if not data.get('Created_By'):
            first_user = UserAdmin.objects.first()
            if first_user:
                data['Created_By'] = first_user.id
        if not data.get('Updated_By'):
            data['Updated_By'] = data.get('Created_By')

        return super().to_internal_value(data)

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['PlanLimit_Id'] = getattr(instance, 'PlanLimit_Id', None)
        return ret

    def get_created_by_name(self, obj):
        try:
            if obj.Created_By:
                first = getattr(obj.Created_By, 'First_Name', '') or ''
                last = getattr(obj.Created_By, 'Last_Name', '') or ''
                full = f"{first} {last}".strip()
                return full or getattr(obj.Created_By, 'username', '')
        except Exception:
            pass
        return None

    def get_updated_by_name(self, obj):
        try:
            if obj.Updated_By:
                first = getattr(obj.Updated_By, 'First_Name', '') or ''
                last = getattr(obj.Updated_By, 'Last_Name', '') or ''
                full = f"{first} {last}".strip()
                return full or getattr(obj.Updated_By, 'username', '')
        except Exception:
            pass
        return None

    def get_organization_name(self, obj):
        try:
            if obj.Organization_Id:
                return getattr(obj.Organization_Id, 'Organization_Name', None) or str(obj.Organization_Id)
        except Exception:
            pass
        return None

    def get_plan_name(self, obj):
        try:
            if obj.Plan_Id:
                return getattr(obj.Plan_Id, 'Plan_Name', None) or str(obj.Plan_Id)
        except Exception:
            pass
        return None


class ProductConfigurationSerializer(serializers.ModelSerializer):
    created_by_name = serializers.SerializerMethodField(read_only=True)
    updated_by_name = serializers.SerializerMethodField(read_only=True)
    organization_name = serializers.SerializerMethodField(read_only=True)
    product_name = serializers.SerializerMethodField(read_only=True)
    product_code = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ProductConfiguration
        fields = '__all__'

    def to_internal_value(self, data):
        if hasattr(data, 'dict'):
            data = data.dict()
        elif hasattr(data, 'copy'):
            data = data.copy()

        # Product resolution if string or dict
        if 'Product_Id' in data or 'Product' in data or 'product_id' in data:
            prod_val = data.get('Product_Id') or data.get('Product') or data.get('product_id')
            if isinstance(prod_val, str) and not prod_val.isdigit():
                prod = ProductMaster.objects.filter(Q(Product_Code__iexact=prod_val) | Q(Product_Name__iexact=prod_val)).first()
                if prod:
                    data['Product_Id'] = prod.id
            elif isinstance(prod_val, int) or (isinstance(prod_val, str) and prod_val.isdigit()):
                data['Product_Id'] = int(prod_val)
            elif hasattr(prod_val, 'id'):
                data['Product_Id'] = prod_val.id

        # JSON field parsing if passed as string
        for json_field in ['General_Settings', 'Module_Configuration', 'Feature_Controls', 'Integrations', 'Branding', 'Advanced_Settings']:
            if json_field in data and isinstance(data[json_field], str):
                try:
                    data[json_field] = json.loads(data[json_field])
                except Exception:
                    data[json_field] = {}

        # Default fallback for Organization_Id, Created_By, Updated_By if missing
        if not data.get('Organization_Id'):
            first_org = Userorganizationmaster.objects.first()
            if first_org:
                data['Organization_Id'] = first_org.id
        if not data.get('Created_By'):
            first_user = UserAdmin.objects.first()
            if first_user:
                data['Created_By'] = first_user.id
        if not data.get('Updated_By'):
            data['Updated_By'] = data.get('Created_By')

        return super().to_internal_value(data)

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['Configuration_Id'] = getattr(instance, 'Configuration_Id', None)
        return ret

    def get_created_by_name(self, obj):
        try:
            if obj.Created_By:
                first = getattr(obj.Created_By, 'First_Name', '') or ''
                last = getattr(obj.Created_By, 'Last_Name', '') or ''
                full = f"{first} {last}".strip()
                return full or getattr(obj.Created_By, 'username', '')
        except Exception:
            pass
        return None

    def get_updated_by_name(self, obj):
        try:
            if obj.Updated_By:
                first = getattr(obj.Updated_By, 'First_Name', '') or ''
                last = getattr(obj.Updated_By, 'Last_Name', '') or ''
                full = f"{first} {last}".strip()
                return full or getattr(obj.Updated_By, 'username', '')
        except Exception:
            pass
        return None

    def get_organization_name(self, obj):
        try:
            if obj.Organization_Id:
                return getattr(obj.Organization_Id, 'Organization_Name', None) or str(obj.Organization_Id)
        except Exception:
            pass
        return None

    def get_product_name(self, obj):
        try:
            if obj.Product_Id:
                return getattr(obj.Product_Id, 'Product_Name', None) or str(obj.Product_Id)
        except Exception:
            pass
        return None

    def get_product_code(self, obj):
        try:
            if obj.Product_Id:
                return getattr(obj.Product_Id, 'Product_Code', None) or str(obj.Product_Id)
        except Exception:
            pass
        return None


class ProductEditionSerializer(serializers.ModelSerializer):
    created_by_name = serializers.SerializerMethodField(read_only=True)
    updated_by_name = serializers.SerializerMethodField(read_only=True)
    organization_name = serializers.SerializerMethodField(read_only=True)
    product_name = serializers.SerializerMethodField(read_only=True)
    product_code = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ProductEdition
        fields = '__all__'

    def to_internal_value(self, data):
        if hasattr(data, 'dict'):
            data = data.dict()
        elif hasattr(data, 'copy'):
            data = data.copy()

        # Handle Edition_Id / Edition_Code mapping
        if 'Edition_Id' in data and not data.get('Edition_Code'):
            data['Edition_Code'] = data['Edition_Id']
        elif 'Edition_Code' in data and not data.get('Edition_Id'):
            data['Edition_Id'] = data['Edition_Code']

        # Product resolution if string or dict
        if 'Product_Id' in data or 'Product' in data or 'product_id' in data:
            prod_val = data.get('Product_Id') or data.get('Product') or data.get('product_id')
            if isinstance(prod_val, str) and not prod_val.isdigit():
                prod = ProductMaster.objects.filter(Q(Product_Code__iexact=prod_val) | Q(Product_Name__iexact=prod_val)).first()
                if prod:
                    data['Product_Id'] = prod.id
            elif isinstance(prod_val, int) or (isinstance(prod_val, str) and prod_val.isdigit()):
                data['Product_Id'] = int(prod_val)
            elif hasattr(prod_val, 'id'):
                data['Product_Id'] = prod_val.id

        # Fallback to first ProductMaster if missing
        if not data.get('Product_Id'):
            first_prod = ProductMaster.objects.first()
            if first_prod:
                data['Product_Id'] = first_prod.id

        # Default fallback for Organization_Id, Created_By, Updated_By if missing
        if not data.get('Organization_Id'):
            first_org = Userorganizationmaster.objects.first()
            if first_org:
                data['Organization_Id'] = first_org.id
        if not data.get('Created_By'):
            first_user = UserAdmin.objects.first()
            if first_user:
                data['Created_By'] = first_user.id
        if not data.get('Updated_By'):
            data['Updated_By'] = data.get('Created_By')

        return super().to_internal_value(data)

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ed_id = getattr(instance, 'Edition_Id', None) or getattr(instance, 'Edition_Code', None)
        ret['Edition_Id'] = ed_id
        if not ret.get('Edition_Code'):
            ret['Edition_Code'] = ed_id
        return ret

    def get_created_by_name(self, obj):
        try:
            if obj.Created_By:
                first = getattr(obj.Created_By, 'First_Name', '') or ''
                last = getattr(obj.Created_By, 'Last_Name', '') or ''
                full = f"{first} {last}".strip()
                return full or getattr(obj.Created_By, 'username', '')
        except Exception:
            pass
        return None

    def get_updated_by_name(self, obj):
        try:
            if obj.Updated_By:
                first = getattr(obj.Updated_By, 'First_Name', '') or ''
                last = getattr(obj.Updated_By, 'Last_Name', '') or ''
                full = f"{first} {last}".strip()
                return full or getattr(obj.Updated_By, 'username', '')
        except Exception:
            pass
        return None

    def get_organization_name(self, obj):
        try:
            if obj.Organization_Id:
                return getattr(obj.Organization_Id, 'Organization_Name', None) or str(obj.Organization_Id)
        except Exception:
            pass
        return None

    def get_product_name(self, obj):
        try:
            if obj.Product_Id:
                return getattr(obj.Product_Id, 'Product_Name', None) or str(obj.Product_Id)
        except Exception:
            pass
        return None

    def get_product_code(self, obj):
        try:
            if obj.Product_Id:
                return getattr(obj.Product_Id, 'Product_Code', None) or str(obj.Product_Id)
        except Exception:
            pass
        return None


class ProductMasterSerializer(serializers.ModelSerializer):
    created_by_name = serializers.SerializerMethodField(read_only=True)
    updated_by_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ProductMaster
        fields = '__all__'

    def to_internal_value(self, data):
        if hasattr(data, 'dict'):
            data = data.dict()
        elif hasattr(data, 'copy'):
            data = data.copy()

        # Backward compatibility: Product_Id mapped to Product_Code
        if 'Product_Id' in data and not data.get('Product_Code'):
            data['Product_Code'] = data['Product_Id']

        # Cloudflare_Public_Id resolution (supports list, JSON string, or legacy Cloudinary_Public_Id)
        if 'Cloudflare_Public_Id' in data or 'Cloudinary_Public_Id' in data:
            cf_val = data.get('Cloudflare_Public_Id') or data.get('Cloudinary_Public_Id')
            if isinstance(cf_val, str):
                try:
                    cf_val = json.loads(cf_val)
                except Exception:
                    cf_val = [c.strip() for c in cf_val.split(',') if c.strip()]
            if not isinstance(cf_val, list):
                cf_val = [cf_val] if cf_val else []
            data['Cloudflare_Public_Id'] = cf_val

        # Features resolution
        if 'Features' in data and isinstance(data['Features'], str):
            try:
                data['Features'] = json.loads(data['Features'])
            except Exception:
                data['Features'] = [f.strip() for f in data['Features'].split(',') if f.strip()]

        # Clean legacy keys
        data.pop('Image', None)
        data.pop('Images', None)
        data.pop('Cloudinary_Public_Id', None)

        # Default fallback for Organization_Id, Created_By, Updated_By if missing
        if not data.get('Organization_Id'):
            first_org = Userorganizationmaster.objects.first()
            if first_org:
                data['Organization_Id'] = first_org.id
        if not data.get('Created_By'):
            first_user = UserAdmin.objects.first()
            if first_user:
                data['Created_By'] = first_user.id
        if not data.get('Updated_By'):
            data['Updated_By'] = data.get('Created_By')

        return super().to_internal_value(data)

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['Product_Id'] = instance.Product_Code  # backward compatibility alias
        return ret

    def get_created_by_name(self, obj):
        try:
            if obj.Created_By:
                first = getattr(obj.Created_By, 'First_Name', '') or ''
                last = getattr(obj.Created_By, 'Last_Name', '') or ''
                full = f"{first} {last}".strip()
                return full or getattr(obj.Created_By, 'username', '')
        except Exception:
            pass
        return None

    def get_updated_by_name(self, obj):
        try:
            if obj.Updated_By:
                first = getattr(obj.Updated_By, 'First_Name', '') or ''
                last = getattr(obj.Updated_By, 'Last_Name', '') or ''
                full = f"{first} {last}".strip()
                return full or getattr(obj.Updated_By, 'username', '')
        except Exception:
            pass
        return None


def resolve_product_id(data):
    prod_val = None
    for key in ['Product_Id', 'Product_id', 'product_id', 'Product', 'product', 'product_type', 'Producttype']:
        if key in data and data[key] is not None and str(data[key]).strip() != '':
            prod_val = data[key]
            break
    if prod_val is not None:
        if isinstance(prod_val, str) and not str(prod_val).isdigit():
            prod = ProductMaster.objects.filter(
                Q(Product_Code__iexact=prod_val) | Q(Product_Name__iexact=prod_val)
            ).first()
            if prod:
                return prod.id
        elif isinstance(prod_val, int) or (isinstance(prod_val, str) and str(prod_val).isdigit()):
            return int(prod_val)
        elif hasattr(prod_val, 'id'):
            return prod_val.id
    return None


def enrich_product_representation(instance, ret):
    prod = getattr(instance, 'Product_Id', None)
    if not prod:
        # Check if model has 'Product' attribute as FK (like Plan)
        prod = getattr(instance, 'Product', None)
        if hasattr(prod, 'id') and not isinstance(prod, ProductMaster):
            # In case Product is something else
            pass
    if prod and hasattr(prod, 'id'):
        ret['Product_Id'] = prod.id
        ret['Product_id'] = prod.id
        ret['Product_name'] = getattr(prod, 'Product_Name', None)
        ret['Product_code'] = getattr(prod, 'Product_Code', None)
        ret['product_name'] = getattr(prod, 'Product_Name', None)
        ret['product_code'] = getattr(prod, 'Product_Code', None)
        ret['Product'] = getattr(prod, 'Product_Name', None) or getattr(prod, 'Product_Code', None)
    else:
        ret['Product_Id'] = None
        ret['Product_id'] = None
        ret['Product_name'] = None
        ret['Product_code'] = None
        ret['product_name'] = None
        ret['product_code'] = None
        ret['Product'] = None
    return ret


def normalize_tax_fields(data, instance=None, base_amount_keys=None, serializer_instance=None):
    if hasattr(data, 'dict'):
        data = data.dict()
    elif hasattr(data, 'copy'):
        data = data.copy()

    # Normalize Tax key
    if 'tax' in data and 'Tax' not in data:
        data['Tax'] = data['tax']

    # Normalize TaxPercentage key
    for k in ['tax_percentage', 'taxpercentage', 'tax_percent']:
        if k in data and 'TaxPercentage' not in data:
            data['TaxPercentage'] = data[k]
            break

    # Normalize TaxAmount key
    for k in ['tax_amount', 'taxamount']:
        if k in data and 'TaxAmount' not in data:
            data['TaxAmount'] = data[k]
            break

    # Normalize TotalAmount key
    for k in ['total_amount', 'totalamount']:
        if k in data and 'TotalAmount' not in data:
            data['TotalAmount'] = data[k]
            break

    # Auto-calculate TaxAmount and TotalAmount if base amount & TaxPercentage available
    try:
        tax_pct = None
        if 'TaxPercentage' in data and data['TaxPercentage'] is not None and str(data['TaxPercentage']).strip() != '':
            tax_pct = float(data['TaxPercentage'])
        elif instance and getattr(instance, 'TaxPercentage', None) is not None:
            tax_pct = float(instance.TaxPercentage)

        base_amount = None
        candidate_keys = base_amount_keys or [
            'UnitPrice', 'Price', 'Amount_Per_User', 'Total_Amount',
            'addonTotalAmount', 'addonPerAmount', 'UserTotalAmount', 'UserPerAmount',
            'storageTotalAmount', 'storagePerAmount', 'PlanNetAmount', 'PlangrossAmount'
        ]
        for bk in candidate_keys:
            if bk in data and data[bk] is not None and str(data[bk]).strip() != '':
                base_amount = float(data[bk])
                break
            elif instance and getattr(instance, bk, None) is not None:
                base_amount = float(getattr(instance, bk))
                break

        if base_amount is not None and tax_pct is not None:
            if 'TaxAmount' not in data or data['TaxAmount'] is None or str(data['TaxAmount']).strip() == '':
                data['TaxAmount'] = round(base_amount * tax_pct / 100.0, 2)
            else:
                data['TaxAmount'] = float(data['TaxAmount'])

            # Only set TotalAmount if model has TotalAmount field or it was provided
            model_cls = None
            if serializer_instance:
                model_cls = getattr(getattr(serializer_instance, 'Meta', None), 'model', None)
            has_total_field = False
            if model_cls:
                try:
                    model_cls._meta.get_field('TotalAmount')
                    has_total_field = True
                except Exception:
                    pass

            if has_total_field or 'TotalAmount' in data or (instance and hasattr(instance, 'TotalAmount')):
                if 'TotalAmount' not in data or data['TotalAmount'] is None or str(data['TotalAmount']).strip() == '':
                    data['TotalAmount'] = round(base_amount + float(data['TaxAmount']), 2)
                else:
                    data['TotalAmount'] = float(data['TotalAmount'])
    except (ValueError, TypeError):
        pass
    return data


def enrich_tax_representation(instance, ret):
    if hasattr(instance, 'Tax'):
        ret['Tax'] = instance.Tax
    if hasattr(instance, 'TaxPercentage'):
        ret['TaxPercentage'] = instance.TaxPercentage or 0
    if hasattr(instance, 'TaxAmount'):
        ret['TaxAmount'] = instance.TaxAmount or 0
    if hasattr(instance, 'TotalAmount'):
        ret['TotalAmount'] = instance.TotalAmount or 0
    return ret


class ProductMasterSerializerMixin:
    def to_internal_value(self, data):
        if hasattr(data, 'dict'):
            data = data.dict()
        elif hasattr(data, 'copy'):
            data = data.copy()
        prod_id = resolve_product_id(data)
        if prod_id is not None:
            data['Product_Id'] = prod_id
        data = normalize_tax_fields(data, getattr(self, 'instance', None), serializer_instance=self)
        return super().to_internal_value(data)

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        enrich_product_representation(instance, ret)
        enrich_tax_representation(instance, ret)
        return ret


class Planserializer(serializers.ModelSerializer):
    product_name = serializers.SerializerMethodField(read_only=True)
    product_code = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Plan
        fields = '__all__'

    def to_internal_value(self, data):
        if hasattr(data, 'dict'):
            data = data.dict()
        elif hasattr(data, 'copy'):
            data = data.copy()

        # Backward compatibility for PlanDetails -> Description
        if 'PlanDetails' in data and not data.get('Description'):
            data['Description'] = data['PlanDetails']
        data.pop('PlanDetails', None)
        data.pop('Addstorage', None)

        # Normalize billing_cycle from either 'billing_cycle' or 'Billing_Cycle'
        bc = data.get('billing_cycle') if 'billing_cycle' in data else data.get('Billing_Cycle')
        if bc is not None:
            normalized_bc = str(bc).strip().lower().replace(' ', '_').replace('-', '_')
            valid_bc = {'monthly', 'quarterly', 'half_yearly', 'yearly', 'one_time'}
            if normalized_bc in valid_bc:
                data['billing_cycle'] = normalized_bc
            else:
                label_map = {
                    'halfyearly': 'half_yearly',
                    'semi_annual': 'half_yearly',
                    'semi_annually': 'half_yearly',
                    'annual': 'yearly',
                    'annually': 'yearly',
                    'year': 'yearly',
                    'month': 'monthly',
                    'onetime': 'one_time',
                    'lifetime': 'one_time',
                }
                data['billing_cycle'] = label_map.get(normalized_bc, 'monthly')

        # Normalize is_limited
        if 'is_limited' in data or 'Is_Limited' in data or 'islimited' in data:
            raw_lim = data.get('is_limited') if 'is_limited' in data else (data.get('Is_Limited') if 'Is_Limited' in data else data.get('islimited'))
            if isinstance(raw_lim, str):
                data['is_limited'] = raw_lim.strip().lower() in ('true', '1', 'yes')
            else:
                data['is_limited'] = bool(raw_lim)

        # Normalize Tax / TaxPercentage / TaxAmount / TotalAmount keys
        if 'tax' in data and 'Tax' not in data:
            data['Tax'] = data['tax']
        if 'tax_percentage' in data and 'TaxPercentage' not in data:
            data['TaxPercentage'] = data['tax_percentage']
        elif 'taxpercentage' in data and 'TaxPercentage' not in data:
            data['TaxPercentage'] = data['taxpercentage']
        if 'tax_amount' in data and 'TaxAmount' not in data:
            data['TaxAmount'] = data['tax_amount']
        elif 'taxamount' in data and 'TaxAmount' not in data:
            data['TaxAmount'] = data['taxamount']
        if 'total_amount' in data and 'TotalAmount' not in data:
            data['TotalAmount'] = data['total_amount']
        elif 'totalamount' in data and 'TotalAmount' not in data:
            data['TotalAmount'] = data['totalamount']

        # Auto-calculate TaxAmount and TotalAmount if not provided
        try:
            unit_price = None
            if 'UnitPrice' in data and data['UnitPrice'] is not None and str(data['UnitPrice']).strip() != '':
                unit_price = float(data['UnitPrice'])
            elif self.instance and self.instance.UnitPrice is not None:
                unit_price = float(self.instance.UnitPrice)

            tax_pct = None
            if 'TaxPercentage' in data and data['TaxPercentage'] is not None and str(data['TaxPercentage']).strip() != '':
                tax_pct = float(data['TaxPercentage'])
            elif self.instance and self.instance.TaxPercentage is not None:
                tax_pct = float(self.instance.TaxPercentage)

            if unit_price is not None and tax_pct is not None:
                if 'TaxAmount' not in data or data['TaxAmount'] is None or str(data['TaxAmount']).strip() == '':
                    data['TaxAmount'] = round(unit_price * tax_pct / 100.0, 2)
                else:
                    data['TaxAmount'] = float(data['TaxAmount'])

                if 'TotalAmount' not in data or data['TotalAmount'] is None or str(data['TotalAmount']).strip() == '':
                    data['TotalAmount'] = round(unit_price + float(data['TaxAmount']), 2)
                else:
                    data['TotalAmount'] = float(data['TotalAmount'])
        except (ValueError, TypeError):
            pass

        # Resolve Product (can be PK ID, or string code/name like 'CRM')
        if 'Product' in data and data['Product']:
            val = data['Product']
            if isinstance(val, str) and not val.isdigit():
                prod = ProductMaster.objects.filter(
                    Q(Product_Code__iexact=val) | Q(Product_Name__iexact=val)
                ).first()
                if prod:
                    data['Product'] = prod.id
            elif isinstance(val, int) or (isinstance(val, str) and val.isdigit()):
                data['Product'] = int(val)
            elif hasattr(val, 'id'):
                data['Product'] = val.id

        return super().to_internal_value(data)

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        # Backward compatibility properties
        ret['PlanDetails'] = instance.Description or ""
        ret['Addstorage'] = 0
        ret['Billing_Cycle'] = instance.billing_cycle
        ret['billing_cycle'] = instance.billing_cycle
        ret['Tax'] = instance.Tax
        ret['TaxPercentage'] = instance.TaxPercentage or 0
        ret['TaxAmount'] = instance.TaxAmount or 0
        ret['TotalAmount'] = instance.TotalAmount or 0
        ret['is_limited'] = bool(instance.is_limited)

        if instance.Product:
            ret['Product_id'] = instance.Product.id
            ret['Product_name'] = instance.Product.Product_Name
            ret['Product_code'] = instance.Product.Product_Code
            ret['Product'] = instance.Product.Product_Name or instance.Product.Product_Code
        else:
            ret['Product_id'] = None
            ret['Product_name'] = None
            ret['Product_code'] = None
            ret['Product'] = None
        return ret

    def get_product_name(self, obj):
        return obj.Product.Product_Name if obj.Product else None

    def get_product_code(self, obj):
        return obj.Product.Product_Code if obj.Product else None


from rest_framework import serializers
from authapp.models import Menu
from .models import Plan


class Planserializers(serializers.ModelSerializer):
    menu_tree = serializers.SerializerMethodField()
    product_name = serializers.SerializerMethodField(read_only=True)
    product_code = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Plan
        fields = "__all__"
        depth = 1

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        # Backward compatibility properties
        ret['PlanDetails'] = instance.Description or ""
        ret['Addstorage'] = 0
        ret['Billing_Cycle'] = instance.billing_cycle
        ret['billing_cycle'] = instance.billing_cycle
        ret['Tax'] = instance.Tax
        ret['TaxPercentage'] = instance.TaxPercentage or 0
        ret['TaxAmount'] = instance.TaxAmount or 0
        ret['TotalAmount'] = instance.TotalAmount or 0
        ret['is_limited'] = bool(instance.is_limited)

        if instance.Product:
            ret['Product_id'] = instance.Product.id
            ret['Product_name'] = instance.Product.Product_Name
            ret['Product_code'] = instance.Product.Product_Code
            if isinstance(ret.get('Product'), dict):
                ret['Product_details'] = ret['Product']
                ret['Product'] = instance.Product.Product_Name or instance.Product.Product_Code
        else:
            ret['Product_id'] = None
            ret['Product_name'] = None
            ret['Product_code'] = None
            ret['Product'] = None
        return ret

    def get_product_name(self, obj):
        return obj.Product.Product_Name if obj.Product else None

    def get_product_code(self, obj):
        return obj.Product.Product_Code if obj.Product else None

    def get_menu_tree(self, obj):
        selected_menu_ids = obj.menu.values_list("id", flat=True)

        root_menus = Menu.objects.filter(
            id__in=selected_menu_ids,
            parent__isnull=True,
            Is_Deleted=False,
            is_active=True
        ).order_by("display_order")

        return self.build_tree(root_menus, selected_menu_ids)

    def build_tree(self, menus, selected_menu_ids):
        tree = []

        for menu in menus:
            children = Menu.objects.filter(
                parent=menu,
                Is_Deleted=False,
                is_active=True
            ).order_by("display_order")

            tree.append({
                "id": menu.id,
                "name": menu.name,
                "code": menu.code,
                "menu_type": menu.menu_type,
                "icon": menu.icon,
                "route": menu.route,
                "selected": menu.id in selected_menu_ids,
                "children": self.build_tree(children, selected_menu_ids)
            })

        return tree

#     def get_role_details(self, obj):
#         if not obj.role:
#             return None

#         from authapp.serializers import RoleSerializer, MenuSerializer
#         from authapp.models import Menu

#         role_data = RoleSerializer(obj.role).data
#         try:
#             permissions = obj.role.permissions
#             permission_codes = permissions.permission_codes
#             role_data['permissions'] = permission_codes

#             # Fetch all active menus matching the permission codes
#             all_permitted = Menu.objects.filter(code__in=permission_codes, is_active=True)

#             # Find menus that act as roots (either no parent, or parent is not in permissions)
#             root_menus = [
#                 m for m in all_permitted
#                 if not m.parent or m.parent.code not in permission_codes
#             ]
#             role_data['menus'] = MenuSerializer(root_menus, many=True, context={'permission_codes': permission_codes}).data
#         except Exception:
#             role_data['permissions'] = []
#             role_data['menus'] = []

#         return role_data

class Subscriptionserializer(ProductMasterSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = Subscriptions
        fields = '__all__'

class Subscriptionserializers(ProductMasterSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = Subscriptions
        fields = '__all__'
        depth = 1

class Storagemasterserializer(ProductMasterSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = Storagemaster
        fields = '__all__'


class InvoiceLineItemSerializer(ProductMasterSerializerMixin, serializers.ModelSerializer):
    Product_Name = serializers.SerializerMethodField(read_only=True)
    Product_Code = serializers.SerializerMethodField(read_only=True)
    Plan_Name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = InvoiceLineItem
        fields = '__all__'

    def get_Product_Name(self, obj):
        try:
            return obj.Product_Id.Product_Name if obj.Product_Id else ""
        except Exception:
            return ""

    def get_Product_Code(self, obj):
        try:
            return obj.Product_Id.Product_Code if obj.Product_Id else ""
        except Exception:
            return ""

    def get_Plan_Name(self, obj):
        try:
            return obj.Plan_Id.Plan_Name if obj.Plan_Id else ""
        except Exception:
            return ""


class Invoiceserializer(ProductMasterSerializerMixin, serializers.ModelSerializer):
    Customer_Name = serializers.SerializerMethodField()
    items = InvoiceLineItemSerializer(many=True, read_only=True)
    InvoiceAmount = serializers.FloatField(required=False, default=0.0)
    TaxAmount = serializers.FloatField(required=False, default=0.0)
    NetAmount = serializers.FloatField(required=False, default=0.0)

    class Meta:
        model = Invoice
        fields = '__all__'

    def get_Customer_Name(self, obj):
        try:
            if obj.Customer_Id:
                return (
                    obj.Customer_Id.Contact_Name or
                    obj.Customer_Id.Account_Owner or
                    obj.Customer_Id.Organization_Name or
                    ""
                )
        except Exception:
            pass
        return ""

    def to_internal_value(self, data):
        if hasattr(data, 'dict'):
            data = data.dict()
        elif hasattr(data, 'copy'):
            data = data.copy()

        items = data.get('items', [])
        if items and isinstance(items, list):
            calc_inv_amt = 0.0
            calc_tax_amt = 0.0
            for item in items:
                qty = float(item.get('Quantity', 1) or 1)
                unit_price = float(item.get('UnitPrice', 0) or 0)
                line_base = qty * unit_price
                tax_pct = float(item.get('TaxPercentage', 0) or 0)
                line_tax = round(line_base * (tax_pct / 100.0), 2)
                calc_inv_amt += line_base
                calc_tax_amt += line_tax
            
            if 'InvoiceAmount' not in data or data.get('InvoiceAmount') is None or data.get('InvoiceAmount') == '':
                data['InvoiceAmount'] = round(calc_inv_amt, 2)
            if 'TaxAmount' not in data or data.get('TaxAmount') is None or data.get('TaxAmount') == '':
                data['TaxAmount'] = round(calc_tax_amt, 2)
            if 'NetAmount' not in data or data.get('NetAmount') is None or data.get('NetAmount') == '':
                data['NetAmount'] = round(float(data['InvoiceAmount']) + float(data['TaxAmount']), 2)
            if len(items) > 1:
                data['Is_Combined'] = True

        return super().to_internal_value(data)

    def create(self, validated_data):
        items_data = self.initial_data.get('items', [])

        # If items are provided in raw request data, calculate totals if not given
        if items_data and isinstance(items_data, list):
            calc_inv_amt = 0.0
            calc_tax_amt = 0.0
            for item in items_data:
                qty = float(item.get('Quantity', 1) or 1)
                unit_price = float(item.get('UnitPrice', 0) or 0)
                line_base = qty * unit_price
                tax_pct = float(item.get('TaxPercentage', 0) or 0)
                line_tax = round(line_base * (tax_pct / 100.0), 2)
                calc_inv_amt += line_base
                calc_tax_amt += line_tax
            
            if 'InvoiceAmount' not in validated_data or not validated_data.get('InvoiceAmount'):
                validated_data['InvoiceAmount'] = round(calc_inv_amt, 2)
            if 'TaxAmount' not in validated_data or not validated_data.get('TaxAmount'):
                validated_data['TaxAmount'] = round(calc_tax_amt, 2)
            if 'NetAmount' not in validated_data or not validated_data.get('NetAmount'):
                validated_data['NetAmount'] = round(validated_data['InvoiceAmount'] + validated_data['TaxAmount'], 2)
            if len(items_data) > 1:
                validated_data['Is_Combined'] = True

        invoice = super().create(validated_data)

        # Create line items
        if items_data and isinstance(items_data, list):
            for item in items_data:
                prod_id = item.get('Product_Id') or item.get('product_id')
                if isinstance(prod_id, dict):
                    prod_id = prod_id.get('id')
                
                sub_id = item.get('Subscription_Id') or item.get('subscription_id')
                if isinstance(sub_id, dict):
                    sub_id = sub_id.get('id')

                plan_id = item.get('Plan_Id') or item.get('plan_id')
                if isinstance(plan_id, dict):
                    plan_id = plan_id.get('id')

                qty = int(item.get('Quantity', 1) or 1)
                unit_price = float(item.get('UnitPrice', 0) or 0)
                line_base = qty * unit_price
                tax_pct = float(item.get('TaxPercentage', 0) or 0)
                tax_amt = float(item.get('TaxAmount', 0) or round(line_base * (tax_pct / 100.0), 2))
                tot_amt = float(item.get('TotalAmount', 0) or round(line_base + tax_amt, 2))

                try:
                    product_obj = ProductMaster.objects.get(id=prod_id) if prod_id else None
                except Exception:
                    product_obj = None

                try:
                    sub_obj = Subscriptions.objects.get(id=sub_id) if sub_id else None
                except Exception:
                    sub_obj = None

                try:
                    plan_obj = Plan.objects.get(id=plan_id) if plan_id else None
                except Exception:
                    plan_obj = None

                if product_obj:
                    InvoiceLineItem.objects.create(
                        Invoice_Id=invoice,
                        Product_Id=product_obj,
                        Subscription_Id=sub_obj,
                        Plan_Id=plan_obj,
                        Item_Type=item.get('Item_Type', 'plan'),
                        Description=item.get('Description', ''),
                        Quantity=qty,
                        UnitPrice=unit_price,
                        Tax=item.get('Tax', ''),
                        TaxPercentage=tax_pct,
                        TaxAmount=tax_amt,
                        TotalAmount=tot_amt
                    )
                    invoice.Products.add(product_obj)

                if sub_obj:
                    invoice.Subscriptions.add(sub_obj)

        return invoice


class Invoiceserializerdepth(ProductMasterSerializerMixin, serializers.ModelSerializer):
    Customer_Name = serializers.SerializerMethodField()
    items = InvoiceLineItemSerializer(many=True, read_only=True)

    class Meta:
        model = Invoice
        fields = '__all__'
        depth = 1

    def get_Customer_Name(self, obj):
        try:
            if obj.Customer_Id:
                return (
                    obj.Customer_Id.Contact_Name or
                    obj.Customer_Id.Account_Owner or
                    obj.Customer_Id.Organization_Name or
                    ""
                )
        except Exception:
            pass
        return ""


class Invoiceserializers(ProductMasterSerializerMixin, serializers.ModelSerializer):
    items = InvoiceLineItemSerializer(many=True, read_only=True)

    class Meta:
        model = Invoice
        fields = '__all__'
        depth = 2


class AddsubscriptionrequestSerializer(ProductMasterSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = Addsubscriptionrequest
        fields = '__all__'


class AddsubscriptionrequestSerializers(ProductMasterSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = Addsubscriptionrequest
        fields = '__all__'
        depth = 2


class Paymentsserializer(ProductMasterSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = Payments
        fields = '__all__'

class Paymentsserializers(ProductMasterSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = Payments
        fields = '__all__'
        depth = 2

class Additionalstoragerequestserializer(ProductMasterSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = Additionalstoragerequest
        fields = '__all__'


class Additionalstoragerequestserializers(ProductMasterSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = Additionalstoragerequest
        fields = '__all__'
        depth = 1

class Renewalserializer(ProductMasterSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = Renewal
        fields = '__all__'

class Renewalserializers(ProductMasterSerializerMixin, serializers.ModelSerializer):
    RenewalDate = serializers.SerializerMethodField()
    Plan_Name = serializers.SerializerMethodField()
    RenewalAmount = serializers.SerializerMethodField()

    class Meta:
        model = Renewal
        fields = '__all__'
        depth = 1

    def get_RenewalDate(self, obj):
        if obj.Customer_Id and getattr(obj.Customer_Id, 'Next_Renewal', None):
            return str(obj.Customer_Id.Next_Renewal)
        return str(obj.Created_Date.date()) if obj.Created_Date else None

    def get_Plan_Name(self, obj):
        if obj.RequestedPlan_Id:
            return getattr(obj.RequestedPlan_Id, 'Plan_Name', '') or ''
        if obj.Customer_Id and getattr(obj.Customer_Id, 'Subscribed_Plan', None):
            return obj.Customer_Id.Subscribed_Plan
        return ''

    def get_RenewalAmount(self, obj):
        return obj.PlanNetAmount or obj.PlangrossAmount or 0

class CancelplansSerializer(ProductMasterSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = Cancelplans
        fields = '__all__'


class CancelplansSerializers(ProductMasterSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = Cancelplans
        fields = '__all__'
        depth = 2

class InstanceRequestserializer(ProductMasterSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = InstanceRequest
        fields = '__all__'

class InstanceRequestserializers(ProductMasterSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = InstanceRequest
        fields = '__all__'
        depth = 1

class Instance_CreationSerializer(ProductMasterSerializerMixin, serializers.ModelSerializer):

    class Meta:
        model = Instance_Creation
        fields = '__all__'

class Instance_CreationSerializers(ProductMasterSerializerMixin, serializers.ModelSerializer):

    class Meta:
        model = Instance_Creation
        fields = '__all__'
        depth = 1


class WebsiteVistorsserializer(serializers.ModelSerializer):
    class Meta:
        model = WebsiteVistors
        fields = '__all__'
class WebsiteVistorsserializers(serializers.ModelSerializer):
    class Meta:
        model = WebsiteVistors
        fields = '__all__'
        depth = 1




class AdditionallicenserequestSerializer(ProductMasterSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = Additionallicenserequest
        fields = '__all__'


class AdditionallicenserequestSerializers(ProductMasterSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = Additionallicenserequest
        fields = '__all__'
        depth = 1


# for documentmaster
class DocumentMasterSerializer(serializers.ModelSerializer):
    File = serializers.FileField(required=False, allow_null=True)

    class Meta:
        model = DocumentMaster
        fields = '__all__'


class DocumentMasterSerializers(serializers.ModelSerializer):
    class Meta:
        model = DocumentMaster
        fields = '__all__'
        depth = 1


class AccountSerializer(ProductMasterSerializerMixin, serializers.ModelSerializer):
    Account_Id = serializers.CharField(required=False, allow_blank=True, max_length=20)
    Document_Id = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Account
        fields = '__all__'

    def get_Document_Id(self, obj):
        return list(obj.documents.filter(Is_Deleted=False).values_list('Document_Id', flat=True))


class AccountSerializers(ProductMasterSerializerMixin, serializers.ModelSerializer):
    documents = serializers.SerializerMethodField()
    Document_Id = serializers.SerializerMethodField()

    class Meta:
        model = Account
        fields = '__all__'
        depth = 1

    def get_Document_Id(self, obj):
        return list(obj.documents.filter(Is_Deleted=False).values_list('Document_Id', flat=True))

    def get_documents(self, obj):
        docs = obj.documents.filter(Is_Deleted=False).order_by('-id')
        return DocumentMasterSerializers(docs, many=True).data


##done by 26.03.2026
class AccountMailMasterSerializer(serializers.ModelSerializer):

    class Meta:
        model =AccountMailMaster
        fields = '__all__'

class AccountMailMasterSerializers(serializers.ModelSerializer):

    class Meta:
        model =AccountMailMaster
        fields = '__all__'
        depth = 1

class AccountAddressSerializer(serializers.ModelSerializer):

    class Meta:
        model =AccountAddress
        fields = '__all__'

class AccountAddressSerializers(serializers.ModelSerializer):

    class Meta:
        model =AccountAddress
        fields = '__all__'
        depth = 1

class AccountCommunicationSerializer(serializers.ModelSerializer):

    class Meta:
        model =AccountCommunication
        fields = '__all__'

class AccountCommunicationSerializers(serializers.ModelSerializer):

    class Meta:
        model =AccountCommunication
        fields = '__all__'
        depth = 1

class AccountCallsSerializer(serializers.ModelSerializer):

    class Meta:
        model =AccountCalls
        fields = '__all__'

class AccountCallsSerializers(serializers.ModelSerializer):

    class Meta:
        model =AccountCalls
        fields = '__all__'
        depth = 1



class AccountMeetingSerializer(serializers.ModelSerializer):

    class Meta:
        model =AccountMeeting
        fields = '__all__'

class AccountMeetingSerializers(serializers.ModelSerializer):

    class Meta:
        model =AccountMeeting
        fields = '__all__'
        depth = 1

class AccountMeetingSerializerss(serializers.ModelSerializer):

    class Meta:
        model =AccountMeeting
        fields = '__all__'
        depth = 2


class AccountNotesSerializer(serializers.ModelSerializer):

    class Meta:
        model =AccountNotes
        fields = '__all__'

class AccountNotesSerializers(serializers.ModelSerializer):

    class Meta:
        model =AccountNotes
        fields = '__all__'
        depth = 1


class UserMailConfigurationSerializer(serializers.ModelSerializer):

    class Meta:
        model =UserMailConfiguration
        fields = '__all__'

class UserMailConfigurationSerializers(serializers.ModelSerializer):

    class Meta:
        model =UserMailConfiguration
        fields = '__all__'
        depth = 1

class UserRemainderSerializer(serializers.ModelSerializer):
    class Meta:
        model =UserRemainder
        fields = '__all__'

class UserRemainderSerializers(serializers.ModelSerializer):

    class Meta:
        model =UserRemainder
        fields = '__all__'
        depth = 1

class UserFilesandUrlsSerializer(serializers.ModelSerializer):
    class Meta:
        model =UserFilesandUrls
        fields = '__all__'

class UserFilesandUrlsSerializers(serializers.ModelSerializer):
    class Meta:
        model =UserFilesandUrls
        fields = '__all__'
        depth = 1

class ModuleMasterSerializer(serializers.ModelSerializer):
    created_by_name = serializers.SerializerMethodField(read_only=True)
    updated_by_name = serializers.SerializerMethodField(read_only=True)
    organization_name = serializers.SerializerMethodField(read_only=True)
    submodules = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ModuleMaster
        fields = '__all__'

    def to_internal_value(self, data):
        if hasattr(data, 'dict'):
            data = data.dict()
        elif hasattr(data, 'copy'):
            data = data.copy()

        # Handle Module_Code / Module_key / ModuleMasterId mapping
        if 'Module_Code' in data and not data.get('Module_key'):
            data['Module_key'] = data['Module_Code']
        elif 'Module_key' in data and not data.get('Module_Code'):
            data['Module_Code'] = data['Module_key']

        # Handle Module_Name / Module_name mapping
        if 'Module_Name' in data and not data.get('Module_name'):
            data['Module_name'] = data['Module_Name']
        elif 'Module_name' in data and not data.get('Module_Name'):
            data['Module_Name'] = data['Module_name']

        # Handle Status / Is_active mapping
        if 'Status' in data and data.get('Status'):
            st = str(data['Status']).strip().lower()
            if st == 'active':
                data['Is_active'] = True
            elif st in ['inactive', 'disabled']:
                data['Is_active'] = False
        elif 'Is_active' in data and data.get('Is_active') is not None:
            data['Status'] = 'Active' if data['Is_active'] else 'Inactive'

        # Default Product if missing
        if not data.get('Product'):
            data['Product'] = 'it'

        # Default fallback for Organization_Id, Created_By, Updated_By if missing
        if not data.get('Organization_Id'):
            first_org = Userorganizationmaster.objects.first()
            if first_org:
                data['Organization_Id'] = first_org.id
        if not data.get('Created_By'):
            first_user = UserAdmin.objects.first()
            if first_user:
                data['Created_By'] = first_user.id
        if not data.get('Updated_By'):
            data['Updated_By'] = data.get('Created_By')

        return super().to_internal_value(data)

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        mod_id = getattr(instance, 'ModuleMasterId', None)
        ret['ModuleMasterId'] = mod_id
        if not ret.get('Module_Code'):
            ret['Module_Code'] = getattr(instance, 'Module_key', None) or mod_id
        if not ret.get('Module_Name'):
            ret['Module_Name'] = getattr(instance, 'Module_name', None) or ''
        if not ret.get('Status'):
            ret['Status'] = 'Active' if getattr(instance, 'Is_active', True) else 'Inactive'
        return ret

    def get_created_by_name(self, obj):
        try:
            if obj.Created_By:
                first = getattr(obj.Created_By, 'First_Name', '') or ''
                last = getattr(obj.Created_By, 'Last_Name', '') or ''
                full = f"{first} {last}".strip()
                return full or getattr(obj.Created_By, 'username', '')
        except Exception:
            pass
        return None

    def get_updated_by_name(self, obj):
        try:
            if obj.Updated_By:
                first = getattr(obj.Updated_By, 'First_Name', '') or ''
                last = getattr(obj.Updated_By, 'Last_Name', '') or ''
                full = f"{first} {last}".strip()
                return full or getattr(obj.Updated_By, 'username', '')
        except Exception:
            pass
        return None

    def get_organization_name(self, obj):
        try:
            if obj.Organization_Id:
                return getattr(obj.Organization_Id, 'Organization_Name', None) or str(obj.Organization_Id)
        except Exception:
            pass
        return None

    def get_submodules(self, obj):
        try:
            if hasattr(obj, 'submodules'):
                children = obj.submodules.filter(Is_Deleted=False, Is_active=True).order_by('id')
                return ModuleMasterSerializer(children, many=True).data
        except Exception:
            pass
        return []


class ModuleMasterserializer(ModuleMasterSerializer):
    pass


class ModuleMasterserializers(ModuleMasterSerializer):
    class Meta(ModuleMasterSerializer.Meta):
        depth = 1

class AdditionalUserMasterSerializer(ProductMasterSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model =AdditionalUserMaster
        fields = '__all__'

class AdditionalUserMasterSerializers(ProductMasterSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model =AdditionalUserMaster
        fields = '__all__'
        depth = 1


class UserActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model =UserActivity
        fields = '__all__'

class UserActivitySerializers(serializers.ModelSerializer):
    class Meta:
        model =UserActivity
        fields = '__all__'
        depth = 1

class UserNotificationSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserNotification
        fields = '__all__'

class UserNotificationSerializers(serializers.ModelSerializer):

    class Meta:
        model = UserNotification
        fields = '__all__'
        depth = 1

class AccountActivitiesSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccountActivities
        fields = '__all__'

class AccountActivitiesSerializers(serializers.ModelSerializer):
    class Meta:
        model = AccountActivities
        fields = '__all__'
        depth = 1

class AccountHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = AccountHistory
        fields = '__all__'

class AccountHistorySerializers(serializers.ModelSerializer):
    class Meta:
        model = AccountHistory
        fields = '__all__'
        depth = 1

class InboxEmailSerializer(serializers.ModelSerializer):

    class Meta:

        model = InboxEmail
        fields = '__all__'

class InboxEmailSerializers(serializers.ModelSerializer):

    class Meta:

        model = InboxEmail
        fields = '__all__'
        depth = 1

class Nonproject_TaskManagementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Nonproject_TaskManagement
        fields ='__all__'

class  Nonproject_TaskManagementSerializers(serializers.ModelSerializer):
    class Meta:
        model = Nonproject_TaskManagement
        fields = '__all__'
        depth = 1


class TicketManagementSerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketManagement
        fields = '__all__'

class TicketManagementSerializers(serializers.ModelSerializer):

    class Meta:
        model = TicketManagement
        fields = '__all__'
        depth = 1

class ProformaInvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProformaInvoice
        fields = '__all__'

class ProformaInvoiceSerializers(serializers.ModelSerializer):

    class Meta:
        model = ProformaInvoice
        fields = '__all__'
        depth = 1


# AuditHistory Serializers
class AuditHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditHistory
        fields = '__all__'


class AuditHistorySerializers(serializers.ModelSerializer):
    class Meta:
        model = AuditHistory
        fields = '__all__'
        depth = 1




# add -ons serialize 

class AddonCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = AddonCategory
        fields = '__all__'

class AddonCategorySerializers(serializers.ModelSerializer):

    class Meta:
        model = AddonCategory
        fields = '__all__'
        depth = 1


class AddonProductCompatibilitySerializer(serializers.ModelSerializer):
    Dependencies = serializers.ListField(child=serializers.IntegerField(min_value=1), required=False)

    class Meta:
        model = AddonProductCompatibility
        fields = '__all__'
        read_only_fields = ('AddonProductCompatibility_Id', 'Addon_Name', 'Product_Name', 'Is_Deleted',
                            'Created_By', 'Updated_By', 'Created_Date', 'Updated_Date')
        validators = []

    def validate(self, attrs):
        def value(name, default=None):
            return attrs.get(name, getattr(self.instance, name, default))

        addon, product = value('Addon'), value('Product')
        if addon is None or addon.Is_Deleted:
            raise serializers.ValidationError({'Addon': 'Select an available add-on.'})
        if product is None or product.Is_Deleted:
            raise serializers.ValidationError({'Product': 'Select an available product.'})

        dependencies = list(dict.fromkeys(value('Dependencies', [])))
        if 'Dependencies' in attrs:
            if addon.pk in dependencies or AddonMaster.objects.filter(pk__in=dependencies, Is_Deleted=False).count() != len(dependencies):
                raise serializers.ValidationError({'Dependencies': 'Select other available add-ons.'})
            attrs['Dependencies'] = dependencies

        if attrs.get('Compatibility_Type'):
            attrs['Is_Compatible'] = attrs['Compatibility_Type'] != 'incompatible'
        elif 'Is_Compatible' in attrs:
            attrs['Compatibility_Type'] = 'compatible' if attrs['Is_Compatible'] else 'incompatible'
        if value('Compatibility_Type') == 'dependency' and not dependencies:
            raise serializers.ValidationError({'Dependencies': 'Select at least one required add-on.'})
        if value('Version_Constraint') and not (value('Minimum_Version') or value('Maximum_Version')):
            raise serializers.ValidationError({'Version_Constraint': 'Enter a minimum or maximum version.'})
        attrs.update(Addon_Name=addon.Addon_Name, Product_Name=product.Product_Name)
        return attrs


class AddonProductCompatibilitySerializers(serializers.ModelSerializer):

    class Meta:
        model = AddonProductCompatibility
        fields = '__all__'
        depth = 1



class TemplateTierSerializer(serializers.Serializer):
    Name = serializers.CharField(max_length=100)
    Min_Employees = serializers.IntegerField(min_value=0, max_value=2147483647)
    Max_Employees = serializers.IntegerField(min_value=0, max_value=2147483647)
    Tier_Price = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal('0'))

    Storage = serializers.CharField(max_length=100, allow_blank=True, required=False)
    Features = serializers.CharField(max_length=500, allow_blank=True, required=False)
    Unit_Price = serializers.DecimalField(max_digits=14, decimal_places=4, min_value=Decimal('0'), required=False, allow_null=True)
    Discount = serializers.DecimalField(max_digits=5, decimal_places=2, min_value=Decimal('0'), max_value=Decimal('100'), required=False, allow_null=True)

    def validate(self, attrs):
        if attrs['Min_Employees'] > attrs['Max_Employees']:
            raise serializers.ValidationError('Maximum employees must be at least the minimum.')
        return attrs


def validate_tier_ranges(tiers):
    ordered = sorted(tiers, key=lambda tier: tier['Min_Employees'])
    if any(left['Max_Employees'] >= right['Min_Employees'] for left, right in zip(ordered, ordered[1:])):
        raise serializers.ValidationError('Employee ranges must not overlap.')
    return ordered


class AddonPriceTemplateSerializer(serializers.ModelSerializer):
    Tiers = TemplateTierSerializer(many=True, required=False)
    Discount_Percentage = serializers.DecimalField(
        max_digits=5, decimal_places=2, min_value=Decimal('0'),
        max_value=Decimal('100'), required=False, allow_null=True,
    )
    Applied_Addons = serializers.SerializerMethodField()

    def get_fields(self):
        fields = super().get_fields()
        if self.context.get('exclude_tiers'):
            fields.pop('Tiers')
        return fields

    def get_Applied_Addons(self, instance):
        return list(instance.AddonPrices.filter(Is_Deleted=False, Addon__Is_Deleted=False)
                    .order_by('Addon_id').values_list('Addon_id', flat=True).distinct())

    def validate_Tiers(self, tiers):
        return [
            {key: str(value) if isinstance(value, Decimal) else value for key, value in tier.items()}
            for tier in validate_tier_ranges(tiers)
        ]

    class Meta:
        model = AddonPriceTemplate
        fields = '__all__'

class AddonPriceTemplateSerializers(serializers.ModelSerializer):

    class Meta:
        model = AddonPriceTemplate
        fields = '__all__'
        depth = 1



class EditionRateSerializer(serializers.Serializer):
    Plan = serializers.IntegerField(min_value=1)
    Rate = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal('0'))
    Trial_Days = serializers.IntegerField(min_value=0, max_value=2147483647)
    Active = serializers.BooleanField()


class PricingOptionsSerializer(serializers.Serializer):
    Billing_Cycle = serializers.ChoiceField(choices=['Monthly', 'Annual'], required=False)
    Allow_Annual_Billing = serializers.BooleanField(required=False)
    Require_Approval = serializers.BooleanField(required=False)
    Model = serializers.ChoiceField(choices=['Fixed', 'Per Tenant', 'Per User', 'Per Usage', 'Tiered'], required=False)
    Marketplace_Visible = serializers.BooleanField(required=False)
    Allow_Trial = serializers.BooleanField(required=False)
    Annual_Discount = serializers.DecimalField(max_digits=5, decimal_places=2, min_value=Decimal('0'), max_value=Decimal('100'), allow_null=True, required=False)
    Edition_Rates = EditionRateSerializer(many=True, required=False)


class TierScheduleDetailsSerializer(serializers.Serializer):
    Code = serializers.CharField(max_length=50)
    Name = serializers.CharField(max_length=150)
    Billing_Cycle = serializers.ChoiceField(choices=['Monthly', 'Annual'])
    Method = serializers.ChoiceField(choices=['Volume Based', 'Graduated (Tiered)'])
    Usage_Metric = serializers.CharField(max_length=80)


def replace_pricing_tiers(pricing, tiers, active, user):
    # Caller holds the pricing row lock for the duration of the transaction.
    existing = list(pricing.Tiers.filter(Is_Deleted=False).order_by('Min_Employees', 'pk'))
    for index, tier in enumerate(tiers):
        fields = {
            'Name': tier['Name'],
            'Rate_Details': {
                key: str(tier[key]) if tier[key] is not None else None
                for key in ('Storage', 'Features', 'Unit_Price', 'Discount') if key in tier
            },
            'Min_Employees': tier['Min_Employees'],
            'Max_Employees': tier['Max_Employees'],
            'Tier_Price': tier['Tier_Price'],
            'Is_Active': active,
            'Updated_By': user,
            'Updated_Date': timezone.now(),
        }
        if index < len(existing):
            pricing.Tiers.filter(pk=existing[index].pk).update(**fields)
        else:
            pricing.Tiers.create(Created_By=user, Created_Date=timezone.now(), **fields)
    pricing.Tiers.filter(pk__in=[tier.pk for tier in existing[len(tiers):]]).update(Is_Deleted=True)


class AddonPricingSerializer(serializers.ModelSerializer):
    Pricing_Options = PricingOptionsSerializer(required=False)
    Tier_Schedule = serializers.JSONField(read_only=True)
    Tiers = TemplateTierSerializer(many=True, required=False, write_only=True)

    def validate_Tiers(self, tiers):
        return validate_tier_ranges(tiers)

    def validate_Pricing_Options(self, value):
        return PricingOptionsSerializer(value).data

    Base_Price = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal('0'))

    def validate(self, attrs):
        addon = attrs.get('Addon', getattr(self.instance, 'Addon', None))
        template = attrs.get('Price_Template', getattr(self.instance, 'Price_Template', None))
        rates = attrs.get('Pricing_Options', {}).get('Edition_Rates', [])
        plans = [row['Plan'] for row in rates]
        if plans and (not addon or len(set(plans)) != len(plans) or set(plans) - set(addon.Plans.values_list('pk', flat=True))):
            raise serializers.ValidationError({'Pricing_Options': 'Edition rates must reference distinct plans linked to the add-on.'})
        if addon and addon.Is_Deleted:
            raise serializers.ValidationError({'Addon': 'Select an available add-on.'})
        if template and template.Is_Deleted and (self.instance is None or self.instance.Price_Template_id != template.pk):
            raise serializers.ValidationError({'Price_Template': 'Select an available template.'})
        start = attrs.get('Effective_From', getattr(self.instance, 'Effective_From', None))
        end = attrs.get('Effective_To', getattr(self.instance, 'Effective_To', None))
        if start and end and start > end:
            raise serializers.ValidationError({'Effective_To': 'End date cannot precede the start date.'})
        return attrs

    @transaction.atomic
    def save(self, **kwargs):
        addon = self.validated_data.get('Addon', getattr(self.instance, 'Addon', None))
        template = self.validated_data.get('Price_Template', getattr(self.instance, 'Price_Template', None))
        template = AddonPriceTemplate.objects.select_for_update().get(pk=template.pk)
        if template.Is_Deleted and (self.instance is None or self.instance.Price_Template_id != template.pk):
            raise serializers.ValidationError({'Price_Template': 'Select an available template.'})
        addon = AddonMaster.objects.select_for_update().get(pk=addon.pk)
        if addon.Is_Deleted:
            raise serializers.ValidationError({'Addon': 'Select an available add-on.'})
        base_price = self.validated_data.get('Base_Price')
        update_master = base_price is not None and (
            self.instance is None
            or base_price != self.instance.Base_Price
            or addon.pk != self.instance.Addon_id
            or template.Currency != self.instance.Price_Template.Currency
        )
        tiers = self.validated_data.pop('Tiers', None)
        if self.instance is not None:
            self.instance = AddonPricing.objects.select_for_update().get(pk=self.instance.pk)
        record = super().save(
            Addon=addon, Addon_Name=addon.Addon_Name,
            Price_Template=template, Price_Template_Name=template.Template_Name, **kwargs,
        )
        if update_master:
            tax_rate = Decimal(str(addon.TaxPercentage or 0))
            tax = (record.Base_Price * tax_rate / 100).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            addon.Price = record.Base_Price
            addon.Currency_code = template.Currency.partition(' ')[0] or addon.Currency_code
            addon.TaxAmount = tax
            addon.TotalAmount = record.Base_Price + tax
            addon.Updated_By = record.Updated_By
            addon.Updated_Date = timezone.now()
            addon.save(update_fields=['Price', 'Currency_code', 'TaxAmount', 'TotalAmount', 'Updated_By', 'Updated_Date'])
        if tiers is not None:
            current_tiers = record.Tiers.filter(Is_Deleted=False)
            active = current_tiers.filter(Is_Active=True).exists() if current_tiers.exists() else record.Is_Active
            replace_pricing_tiers(record, tiers, active, record.Updated_By)
            record.Tier_Schedule = {**(record.Tier_Schedule or {}), 'Customized': True}
            record.save(update_fields=['Tier_Schedule'])
        return record

    class Meta:
        model = AddonPricing
        fields = '__all__'

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        tiers = sorted(
            (tier for tier in instance.Tiers.all() if tier.Is_Deleted is False),
            key=lambda tier: (tier.Min_Employees, tier.pk),
        )
        ret['Tiers'] = [
            {
                **TemplateTierSerializer({
                    **(tier.Rate_Details or {}),
                    'Name': tier.Name,
                    'Min_Employees': tier.Min_Employees,
                    'Max_Employees': tier.Max_Employees,
                    'Tier_Price': tier.Tier_Price,
                }).data,
                'id': tier.pk,
                'Is_Active': tier.Is_Active,
            }
            for tier in tiers
        ]
        try:
            if instance.Addon:
                ret['Category'] = getattr(instance.Addon, 'Category', '') or ''
                ret['Addon_Code'] = instance.Addon.Addon_Code or instance.Addon.AddonMaster_Id
                ret['License_Model'] = getattr(instance.Addon, 'License_Model', '') or 'Per Tenant'
            if instance.Price_Template:
                ret['Pricing_Model'] = (instance.Pricing_Options or {}).get('Model') or instance.Addon.License_Model or ''
                ret['Billing_Cycle'] = (instance.Pricing_Options or {}).get('Billing_Cycle') or instance.Price_Template.Billing_Cycle
                ret['Currency'] = getattr(instance.Price_Template, 'Currency', '') or 'INR'
                ret['Template_Code'] = getattr(instance.Price_Template, 'Template_Code', '') or ''
                ret['Price_Template_Name'] = getattr(instance.Price_Template, 'Template_Name', '') or ret.get('Price_Template_Name') or ''
        except Exception:
            pass
        return ret

class AddonPricingSerializers(serializers.ModelSerializer):

    class Meta:
        model = AddonPricing
        fields = '__all__'
        depth = 1



class AddonTieredPricingSerializer(serializers.ModelSerializer):
    class Meta:
        model = AddonTieredPricing
        fields = '__all__'

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        try:
            if instance.Addon_Pricing:
                ret['Addon_Name'] = instance.Addon_Pricing.Addon_Name or ''
                ret['Pricing_Id'] = instance.Addon_Pricing.id
                ret['Addon_Code'] = getattr(instance.Addon_Pricing.Addon, 'AddonMaster_Id', '') if instance.Addon_Pricing.Addon else ''
                ret['Category'] = getattr(instance.Addon_Pricing.Addon, 'Category', '') if instance.Addon_Pricing.Addon else ''
                if instance.Addon_Pricing.Price_Template:
                    ret['Billing_Cycle'] = instance.Addon_Pricing.Price_Template.Billing_Cycle or 'Monthly'
                    ret['Currency'] = instance.Addon_Pricing.Price_Template.Currency or 'INR'
                    ret['Template_Code'] = instance.Addon_Pricing.Price_Template.Template_Code or ''
            ret['Tier_Price_Display'] = f"₹{float(instance.Tier_Price):,.2f}" if instance.Tier_Price else '₹0.00'
            ret['Status'] = 'Active' if instance.Is_Active else 'Inactive'
        except Exception:
            pass
        return ret

class AddonTieredPricingSerializers(serializers.ModelSerializer):

    class Meta:
        model = AddonTieredPricing
        fields = '__all__'
        depth = 1



class AddonDiscountCouponSerializer(serializers.ModelSerializer):
    Coupon_Code = serializers.CharField(max_length=50, required=False)
    Status = serializers.SerializerMethodField()

    class Meta:
        model = AddonDiscountCoupon
        fields = '__all__'
        read_only_fields = ('AddonDiscountCoupon_Id', 'Created_By', 'Updated_By', 'Created_Date', 'Updated_Date', 'Is_Deleted')

    def validate(self, attrs):
        def field(name, default=None):
            return attrs.get(name, getattr(self.instance, name, default))

        errors = {}
        kind = field('Kind', 'Coupon')
        if kind == 'Discount' and not field('Name'):
            errors['Name'] = 'Enter a discount name.'
        if self.instance and kind != self.instance.Kind:
            errors['Kind'] = 'The offer type cannot be changed.'
        if kind == 'Coupon':
            code = field('Coupon_Code')
            if 'Coupon_Code' in attrs:
                attrs['Coupon_Code'] = code.upper()
            if not code:
                errors['Coupon_Code'] = 'Enter a coupon code.'
            elif AddonDiscountCoupon.objects.filter(Coupon_Code__iexact=code).exclude(pk=getattr(self.instance, 'pk', None)).exists():
                errors['Coupon_Code'] = 'This coupon code already exists.'
        if kind == 'Discount':
            attrs.pop('Coupon_Code', None)
        value = field('Discount_Value')
        discount_type = field('Discount_Type')
        if discount_type not in ('Percentage', 'Flat Amount') and ('Discount_Type' in attrs or not self.instance):
            errors['Discount_Type'] = 'Choose Percentage or Flat Amount.'
        if value is not None and (value <= 0 or (discount_type == 'Percentage' and value > 100)):
            errors['Discount_Value'] = 'Enter a positive value. A percentage cannot exceed 100.'
        start, end = field('Valid_From'), field('Valid_To')
        if start and end and start > end:
            errors['Valid_To'] = 'Validity end must be on or after the start.'
        for key in ('Usage_Limit', 'Per_Customer_Limit'):
            if field(key) is not None and field(key) < 1:
                errors[key] = 'Enter a limit greater than zero.'
        applicability = field('Applicability', 'Add-on')
        if applicability == 'Subscription' and attrs.get('Applicable_Addons'):
            errors['Applicable_Addons'] = 'Select add-ons only for Add-on or All.'
        if applicability == 'Add-on' and attrs.get('Applicable_Products'):
            errors['Applicable_Products'] = 'Select products only for Subscription or All.'
        for key in ('Applicable_Products', 'Applicable_Addons', 'Applicable_Plans'):
            if any(item.Is_Deleted for item in attrs.get(key, [])):
                errors[key] = 'Select records that are available.'
        products = {item.pk for item in field('Applicable_Products', [])} if 'Applicable_Products' in attrs else (
            set(self.instance.Applicable_Products.values_list('pk', flat=True)) if self.instance else set()
        )
        if products and any(plan.Product_id not in products for plan in attrs.get('Applicable_Plans', [])):
            errors['Applicable_Plans'] = 'Select plans from the chosen products.'
        if errors:
            raise serializers.ValidationError(errors)
        return attrs

    def create(self, validated_data):
        if validated_data.get('Kind') == 'Discount':
            validated_data['Coupon_Code'] = f'DIS-{uuid4().hex}'
        validated_data['AddonDiscountCoupon_Id'] = f'ADC{uuid4().int:039d}'
        return super().create(validated_data)

    def get_Status(self, instance):
        now = timezone.now()
        if not instance.Is_Active:
            return 'Draft'
        if instance.Valid_From > now:
            return 'Scheduled'
        if instance.Valid_To < now:
            return 'Expired'
        return 'Active'

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        try:
            val_num = float(instance.Discount_Value) if instance.Discount_Value else 0
            if instance.Discount_Type == 'Percentage' or '%' in str(instance.Discount_Type or ''):
                ret['Formatted_Value'] = f"{int(val_num) if val_num.is_integer() else val_num}%"
            else:
                ret['Formatted_Value'] = f"₹{int(val_num) if val_num.is_integer() else val_num:,.2f}"
            ret['Applicable_Addon_Names'] = [a.Addon_Name for a in instance.Applicable_Addons.all()]
            ret['Addon_Count'] = instance.Applicable_Addons.count()
            ret['Status'] = 'Active' if instance.Is_Active else 'Inactive'
        except Exception:
            pass
        return ret

class AddonDiscountCouponSerializers(serializers.ModelSerializer):

    class Meta:
        model = AddonDiscountCoupon
        fields = '__all__'
        depth = 1




class AddonPriceHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = AddonPriceHistory
        fields = '__all__'

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        try:
            pricing = getattr(instance, 'Addon_Pricing', None)
            addon = getattr(pricing, 'Addon', None) if pricing else None

            addon_name = (
                getattr(pricing, 'Addon_Name', None)
                or (getattr(addon, 'Addon_Name', None) if addon else None)
                or 'Add-on'
            )
            ret['Addon_Name'] = addon_name
            ret['Pricing_Id'] = pricing.id if pricing else None

            product_name = 'Pegatto CRM'
            if addon and hasattr(addon, 'Products'):
                prod = addon.Products.first()
                if prod and getattr(prod, 'Product_Name', None):
                    product_name = prod.Product_Name
            ret['Product'] = product_name

            category_name = 'Communication'
            if addon and getattr(addon, 'Category', None):
                category_name = addon.Category
            elif pricing and getattr(pricing, 'Category', None):
                category_name = pricing.Category
            ret['Category'] = category_name

            old_price = float(instance.Old_Base_Price) if instance.Old_Base_Price is not None else 0.0
            new_price = float(instance.New_Base_Price) if instance.New_Base_Price is not None else 0.0
            change_amount = round(new_price - old_price, 2)
            change_pct = round(((new_price - old_price) / old_price * 100), 2) if old_price > 0 else 0.0

            ret['Previous_Price'] = old_price
            ret['New_Price'] = new_price
            ret['Change_Amount'] = change_amount
            ret['Change_Percentage'] = change_pct
            ret['Reason'] = getattr(instance, 'Reason', None) or 'Regular price adjustment'
            ret['Changed_By_Name'] = instance.Changed_By.username if instance.Changed_By else 'SA (Super Admin)'
            ret['Effective_Date'] = instance.Change_Date.strftime('%d %b %Y') if instance.Change_Date else ''
        except Exception:
            pass
        return ret

class AddonPriceHistorySerializers(serializers.ModelSerializer):

    class Meta:
        model = AddonPriceHistory
        fields = '__all__'
        depth = 1


class LeadsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Leads
        fields = '__all__'

class LeadsSerializers(serializers.ModelSerializer):

    class Meta:
        model = Leads
        fields = '__all__'
        depth = 1


class SafeDateField(serializers.DateField):
    """
    Safely handles both string, date, and datetime instances without raising:
    "Expected a `date`, but got a `datetime`. Refusing to coerce..."
    """
    def to_internal_value(self, value):
        if not value:
            return None
        if isinstance(value, str):
            value = value.split('T')[0].split(' ')[0]
        return super().to_internal_value(value)

    def to_representation(self, value):
        if not value:
            return None
        if hasattr(value, 'date'):
            value = value.date()
        return super().to_representation(value)


class DealSerializer(serializers.ModelSerializer):
    Won_Deal_Date = SafeDateField(required=False, allow_null=True)
    Created_Date = SafeDateField(required=False, allow_null=True)
    Updated_Date = SafeDateField(required=False, allow_null=True)
    Products = serializers.CharField(source='Product_Name', required=False, allow_null=True, allow_blank=True)

    class Meta:
        model = Deal
        fields = '__all__'

class DealSerializers(serializers.ModelSerializer):
    Won_Deal_Date = SafeDateField(required=False, allow_null=True)
    Created_Date = SafeDateField(required=False, allow_null=True)
    Updated_Date = SafeDateField(required=False, allow_null=True)
    Products = serializers.CharField(source='Product_Name', required=False, allow_null=True, allow_blank=True)

    class Meta:
        model = Deal
        fields = '__all__'
        depth = 1


class AccountSerializerpartner(serializers.ModelSerializer):
    Created_Date = SafeDateField(required=False, allow_null=True)
    Updated_Date = SafeDateField(required=False, allow_null=True)
    Date_Of_Birth = SafeDateField(required=False, allow_null=True)

    class Meta:
        model = Account
        fields = '__all__'

    def to_internal_value(self, data):
        data = data.copy() if hasattr(data, 'copy') else dict(data)
        for f in ['Created_Date', 'Updated_Date', 'Date_Of_Birth']:
            if data.get(f):
                val = str(data[f])
                if 'T' in val:
                    data[f] = val.split('T')[0]
                elif ' ' in val:
                    data[f] = val.split(' ')[0]
        return super().to_internal_value(data)

    def to_representation(self, instance):
        from datetime import datetime
        if hasattr(instance, 'Created_Date') and isinstance(instance.Created_Date, datetime):
            instance.Created_Date = instance.Created_Date.date()
        if hasattr(instance, 'Updated_Date') and isinstance(instance.Updated_Date, datetime):
            instance.Updated_Date = instance.Updated_Date.date()
        if hasattr(instance, 'Date_Of_Birth') and isinstance(instance.Date_Of_Birth, datetime):
            instance.Date_Of_Birth = instance.Date_Of_Birth.date()
        return super().to_representation(instance)


class AccountSerializerpartners(serializers.ModelSerializer):
    Created_Date = SafeDateField(required=False, allow_null=True)
    Updated_Date = SafeDateField(required=False, allow_null=True)
    Date_Of_Birth = SafeDateField(required=False, allow_null=True)

    class Meta:
        model = Account
        fields = '__all__'
        depth = 1

    def to_representation(self, instance):
        from datetime import datetime
        if hasattr(instance, 'Created_Date') and isinstance(instance.Created_Date, datetime):
            instance.Created_Date = instance.Created_Date.date()
        if hasattr(instance, 'Updated_Date') and isinstance(instance.Updated_Date, datetime):
            instance.Updated_Date = instance.Updated_Date.date()
        if hasattr(instance, 'Date_Of_Birth') and isinstance(instance.Date_Of_Birth, datetime):
            instance.Date_Of_Birth = instance.Date_Of_Birth.date()
        return super().to_representation(instance)


# ==========================================
# License & Entitlement Management Serializers
# ==========================================

class _LicenseAuditSerializerMixin(serializers.ModelSerializer):
    """Shared display helpers, FK string resolution via icontains, and audit defaults."""

    created_by_name = serializers.SerializerMethodField(read_only=True)
    updated_by_name = serializers.SerializerMethodField(read_only=True)
    organization_name = serializers.SerializerMethodField(read_only=True)

    @staticmethod
    def _normalize_data(data):
        if hasattr(data, 'dict'):
            return data.dict()
        if hasattr(data, 'copy'):
            return data.copy()
        return dict(data)

    @staticmethod
    def _inject_audit_defaults(data, is_partial=False):
        if is_partial:
            return
        if not data.get('Organization_Id'):
            first_org = Userorganizationmaster.objects.first()
            if first_org:
                data['Organization_Id'] = first_org.id
        if not data.get('Created_By'):
            first_user = UserAdmin.objects.first()
            if first_user:
                data['Created_By'] = first_user.id
        if not data.get('Updated_By'):
            data['Updated_By'] = data.get('Created_By')

    @staticmethod
    def _resolve_fk_pk(model_cls, raw_val, *search_fields):
        if raw_val in (None, ''):
            return None
        if hasattr(raw_val, 'id'):
            return raw_val.id
        if isinstance(raw_val, dict):
            raw_val = raw_val.get('id') or raw_val.get('value')
        if isinstance(raw_val, int):
            return raw_val
        text = str(raw_val).strip()
        if text.isdigit():
            return int(text)
        if not text or not search_fields:
            return raw_val
        query = Q()
        for field_name in search_fields:
            query |= Q(**{f"{field_name}__icontains": text})
        obj = model_cls.objects.filter(query).order_by('id').first()
        return obj.id if obj else raw_val

    @staticmethod
    def _format_user_display(user_obj):
        if not user_obj:
            return None
        first = getattr(user_obj, 'First_Name', '') or ''
        last = getattr(user_obj, 'Last_Name', '') or ''
        full = f"{first} {last}".strip()
        return full or getattr(user_obj, 'username', None)

    def get_created_by_name(self, obj):
        return self._format_user_display(getattr(obj, 'Created_By', None))

    def get_updated_by_name(self, obj):
        return self._format_user_display(getattr(obj, 'Updated_By', None))

    def get_organization_name(self, obj):
        org = getattr(obj, 'Organization_Id', None)
        return (getattr(org, 'Organization_Name', None) or str(org)) if org else None


class LicenseEntitlementSerializer(_LicenseAuditSerializerMixin):
    license_key = serializers.SerializerMethodField(read_only=True)
    feature_name = serializers.SerializerMethodField(read_only=True)
    addon_name = serializers.SerializerMethodField(read_only=True)
    module_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = LicenseEntitlement
        fields = '__all__'

    def to_internal_value(self, data):
        data = self._normalize_data(data)
        if 'license_id' in data and 'License_Id' not in data:
            data['License_Id'] = data.pop('license_id')
        if 'License_Id' in data:
            data['License_Id'] = self._resolve_fk_pk(
                LicenseMaster, data.get('License_Id'), 'License_Id', 'License_Key'
            )
        if 'Feature_Id' in data:
            data['Feature_Id'] = self._resolve_fk_pk(
                ProductFeature, data.get('Feature_Id'), 'Feature_Id', 'Feature_Code', 'Feature_Name'
            )
        if 'Addon_Id' in data:
            data['Addon_Id'] = self._resolve_fk_pk(
                AddonMaster, data.get('Addon_Id'), 'Addon_Code', 'Addon_Name'
            )
        if 'Module_Id' in data:
            data['Module_Id'] = self._resolve_fk_pk(
                ModuleMaster, data.get('Module_Id'), 'ModuleMasterId', 'Module_Code', 'Module_name'
            )
        self._inject_audit_defaults(data, is_partial=self.partial)
        return super().to_internal_value(data)

    def get_license_key(self, obj):
        lic = getattr(obj, 'License_Id', None)
        return getattr(lic, 'License_Key', None) if lic else None

    def get_feature_name(self, obj):
        feat = getattr(obj, 'Feature_Id', None)
        return getattr(feat, 'Feature_Name', None) if feat else None

    def get_addon_name(self, obj):
        addon = getattr(obj, 'Addon_Id', None)
        return getattr(addon, 'Addon_Name', None) if addon else None

    def get_module_name(self, obj):
        mod = getattr(obj, 'Module_Id', None)
        return getattr(mod, 'Module_name', None) if mod else None


class LicenseAssignmentSerializer(_LicenseAuditSerializerMixin):
    license_key = serializers.SerializerMethodField(read_only=True)
    customer_name = serializers.SerializerMethodField(read_only=True)
    assigned_user_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = LicenseAssignment
        fields = '__all__'

    def to_internal_value(self, data):
        data = self._normalize_data(data)
        if 'License_Id' in data:
            data['License_Id'] = self._resolve_fk_pk(
                LicenseMaster, data.get('License_Id'), 'License_Id', 'License_Key'
            )
        if 'Customer_Id' in data:
            data['Customer_Id'] = self._resolve_fk_pk(
                Account, data.get('Customer_Id'), 'Account_Id', 'Organization_Name', 'Contact_Name'
            )
        self._inject_audit_defaults(data, is_partial=self.partial)
        return super().to_internal_value(data)

    def get_license_key(self, obj):
        lic = getattr(obj, 'License_Id', None)
        return getattr(lic, 'License_Key', None) if lic else None

    def get_customer_name(self, obj):
        cust = getattr(obj, 'Customer_Id', None)
        if cust:
            return getattr(cust, 'Organization_Name', None) or getattr(cust, 'Contact_Name', None)
        lic = getattr(obj, 'License_Id', None)
        return getattr(lic, 'Customer_Name', None) if lic else None

    def get_assigned_user_name(self, obj):
        return self._format_user_display(getattr(obj, 'Assigned_User_Id', None)) or obj.Assignee_Name


class LicenseRenewalSerializer(_LicenseAuditSerializerMixin):
    license_key = serializers.SerializerMethodField(read_only=True)
    customer_name = serializers.SerializerMethodField(read_only=True)
    product_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = LicenseRenewal
        fields = '__all__'

    def to_internal_value(self, data):
        data = self._normalize_data(data)
        if 'License_Id' in data:
            data['License_Id'] = self._resolve_fk_pk(
                LicenseMaster, data.get('License_Id'), 'License_Id', 'License_Key'
            )
        self._inject_audit_defaults(data, is_partial=self.partial)
        return super().to_internal_value(data)

    def get_license_key(self, obj):
        lic = getattr(obj, 'License_Id', None)
        return getattr(lic, 'License_Key', None) if lic else None

    def get_customer_name(self, obj):
        lic = getattr(obj, 'License_Id', None)
        if not lic:
            return None
        return lic.Customer_Name or (getattr(lic.Customer_Id, 'Organization_Name', None) if lic.Customer_Id else None)

    def get_product_name(self, obj):
        lic = getattr(obj, 'License_Id', None)
        if not lic:
            return None
        return lic.Product_Name or (getattr(lic.Product_Id, 'Product_Name', None) if lic.Product_Id else None)


class LicenseMasterSerializer(_LicenseAuditSerializerMixin):
    Valid_From = SafeDateField(required=False, allow_null=True)
    Valid_To = SafeDateField(required=False, allow_null=True)
    Activated_On = SafeDateField(required=False, allow_null=True)
    customer_name = serializers.SerializerMethodField(read_only=True)
    product_name = serializers.SerializerMethodField(read_only=True)
    product_code = serializers.SerializerMethodField(read_only=True)
    plan_name = serializers.SerializerMethodField(read_only=True)
    edition_name = serializers.SerializerMethodField(read_only=True)
    plan_edition_display = serializers.SerializerMethodField(read_only=True)
    subscription_code = serializers.SerializerMethodField(read_only=True)
    entitlements_count = serializers.SerializerMethodField(read_only=True)
    entitlements = serializers.SerializerMethodField(read_only=True)
    is_expiring_soon = serializers.SerializerMethodField(read_only=True)
    days_to_expiry = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = LicenseMaster
        fields = '__all__'

    def to_internal_value(self, data):
        data = self._normalize_data(data)
        self._initial_entitlements = data.pop('entitlements', None)

        alias_map = {
            'customer_id': 'Customer_Id',
            'tenant_id': 'Customer_Id',
            'product_id': 'Product_Id',
            'plan_id': 'Plan_Id',
            'edition_id': 'ProductEdition_id',
            'product_edition_id': 'ProductEdition_id',
            'subscription_id': 'Subscription_Id',
            'users': 'Entitled_Users',
            'entitled_users': 'Entitled_Users',
            'valid_from': 'Valid_From',
            'valid_to': 'Valid_To',
            'status': 'Status',
            'license_type': 'License_Type',
        }
        for src_key, dst_key in alias_map.items():
            if src_key in data and dst_key not in data:
                data[dst_key] = data.pop(src_key)

        if 'Customer_Id' in data:
            data['Customer_Id'] = self._resolve_fk_pk(
                Account, data.get('Customer_Id'), 'Account_Id', 'Organization_Name', 'Contact_Name'
            )
        if 'Product_Id' in data:
            data['Product_Id'] = self._resolve_fk_pk(
                ProductMaster, data.get('Product_Id'), 'Product_Code', 'Product_Name'
            )
        if 'Plan_Id' in data:
            data['Plan_Id'] = self._resolve_fk_pk(
                Plan, data.get('Plan_Id'), 'Plan_Id', 'Plan_Name'
            )
        if 'ProductEdition_id' in data:
            data['ProductEdition_id'] = self._resolve_fk_pk(
                ProductEdition, data.get('ProductEdition_id'), 'Edition_Id', 'Edition_Code', 'Edition_Name'
            )
        if 'Subscription_Id' in data:
            data['Subscription_Id'] = self._resolve_fk_pk(
                Subscriptions, data.get('Subscription_Id'), 'Subscription_Id', 'Subscription_Name'
            )

        self._inject_audit_defaults(data, is_partial=self.partial)
        return super().to_internal_value(data)

    def validate(self, attrs):
        attrs = super().validate(attrs)
        valid_from = attrs.get('Valid_From', getattr(self.instance, 'Valid_From', None))
        valid_to = attrs.get('Valid_To', getattr(self.instance, 'Valid_To', None))
        if valid_from and valid_to and valid_to < valid_from:
            raise serializers.ValidationError({'Valid_To': 'Valid_To must be on or after Valid_From.'})
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        license_obj = super().create(validated_data)
        self._sync_initial_entitlements(license_obj)
        return license_obj

    def _sync_initial_entitlements(self, license_obj):
        items = getattr(self, '_initial_entitlements', None)
        if not isinstance(items, list):
            return
        for item in items:
            if not isinstance(item, dict):
                continue
            payload = dict(item)
            payload['License_Id'] = license_obj.id
            if not payload.get('Organization_Id') and license_obj.Organization_Id_id:
                payload['Organization_Id'] = license_obj.Organization_Id_id
            if not payload.get('Created_By') and license_obj.Created_By_id:
                payload['Created_By'] = license_obj.Created_By_id
            ent_ser = LicenseEntitlementSerializer(data=payload)
            if ent_ser.is_valid(raise_exception=True):
                ent_ser.save()

    def get_customer_name(self, obj):
        if obj.Customer_Id:
            return getattr(obj.Customer_Id, 'Organization_Name', None) or getattr(obj.Customer_Id, 'Contact_Name', None)
        return obj.Customer_Name

    def get_product_name(self, obj):
        if obj.Product_Id:
            return getattr(obj.Product_Id, 'Product_Name', None)
        return obj.Product_Name

    def get_product_code(self, obj):
        if obj.Product_Id:
            return getattr(obj.Product_Id, 'Product_Code', None)
        return None

    def get_plan_name(self, obj):
        return getattr(obj.Plan_Id, 'Plan_Name', None) if obj.Plan_Id else None

    def get_edition_name(self, obj):
        return getattr(obj.ProductEdition_id, 'Edition_Name', None) if obj.ProductEdition_id else None

    def get_plan_edition_display(self, obj):
        return (
            obj.Plan_Edition_Name
            or self.get_edition_name(obj)
            or self.get_plan_name(obj)
            or ''
        )

    def get_subscription_code(self, obj):
        return getattr(obj.Subscription_Id, 'Subscription_Id', None) if obj.Subscription_Id else None

    def get_entitlements_count(self, obj):
        return obj.entitlements.filter(Is_Deleted=False).count()

    def get_entitlements(self, obj):
        qs = obj.entitlements.filter(Is_Deleted=False).order_by('id')
        return LicenseEntitlementSerializer(qs, many=True).data

    def get_days_to_expiry(self, obj):
        if not obj.Valid_To:
            return None
        return (obj.Valid_To - timezone.localdate()).days

    def get_is_expiring_soon(self, obj):
        days = self.get_days_to_expiry(obj)
        if days is None:
            return False
        status_lower = (obj.Status or '').lower()
        return status_lower == 'expiring' or (0 <= days <= 30 and status_lower in ('active', 'expiring'))


# ==========================================
# Trial Configuration Serializer (Single Table)
# ==========================================

class TrialConfigurationSerializer(_LicenseAuditSerializerMixin):
    product_name = serializers.SerializerMethodField(read_only=True)
    product_code = serializers.SerializerMethodField(read_only=True)
    edition_name = serializers.SerializerMethodField(read_only=True)
    plan_name = serializers.SerializerMethodField(read_only=True)
    category_name = serializers.SerializerMethodField(read_only=True)
    default_converted_plan_name = serializers.SerializerMethodField(read_only=True)
    enabled_features_details = serializers.SerializerMethodField(read_only=True)
    enabled_features_count = serializers.SerializerMethodField(read_only=True)
    duration_label = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = TrialConfiguration
        fields = '__all__'

    def _resolve_features_list(self, raw_features):
        if raw_features in (None, ''):
            return []
        if isinstance(raw_features, str):
            raw_txt = raw_features.strip()
            if raw_txt.startswith('['):
                try:
                    raw_features = json.loads(raw_txt)
                except Exception:
                    raw_features = [x.strip() for x in raw_txt.split(',') if x.strip()]
            else:
                raw_features = [x.strip() for x in raw_txt.split(',') if x.strip()]
        if not isinstance(raw_features, list):
            raw_features = [raw_features]

        resolved_ids = []
        for item in raw_features:
            pk = self._resolve_fk_pk(ProductFeature, item, 'Feature_Id', 'Feature_Code', 'Feature_Name')
            if isinstance(pk, int) and pk not in resolved_ids:
                resolved_ids.append(pk)
        return resolved_ids

    def to_internal_value(self, data):
        data = self._normalize_data(data)

        if 'Trial_Id' in data and not data.get('Trial_Code'):
            data['Trial_Code'] = data['Trial_Id']
        elif 'Trial_Code' in data and not data.get('Trial_Id'):
            data['Trial_Id'] = data['Trial_Code']

        alias_map = {
            'trial_plan_name': 'Trial_Plan_Name',
            'plan_name': 'Trial_Plan_Name',
            'product_id': 'Product_Id',
            'product': 'Product_Id',
            'edition_id': 'Edition_Id',
            'edition': 'Edition_Id',
            'plan_id': 'Plan_Id',
            'category_id': 'Category_Id',
            'trial_duration_days': 'Trial_Duration_Days',
            'trial_duration': 'Trial_Duration_Days',
            'duration': 'Trial_Duration_Days',
            'feature_scope': 'Feature_Scope',
            'features_summary': 'Features_Summary',
            'enabled_features': 'Enabled_Features',
            'allow_conversion_to_paid': 'Allow_Conversion_To_Paid',
            'default_converted_plan_id': 'Default_Converted_Plan_Id',
            'retain_trial_data': 'Retain_Trial_Data',
            'auto_expire_trial': 'Auto_Expire_Trial',
            'user_limit': 'User_Limit',
            'storage_limit_gb': 'Storage_Limit_GB',
            'storage_limit': 'Storage_Limit_GB',
            'trial_rules': 'Trial_Rules',
            'conversion_settings': 'Conversion_Settings',
            'email_notifications': 'Email_Notifications',
            'description': 'Description',
            'status': 'Status',
        }
        for src_key, dst_key in alias_map.items():
            if src_key in data and dst_key not in data:
                data[dst_key] = data.pop(src_key)

        if data.pop('save_as_draft', False):
            data['Status'] = 'Draft'
            data['Is_Active'] = False

        if 'Product_Id' in data:
            data['Product_Id'] = self._resolve_fk_pk(
                ProductMaster, data.get('Product_Id'), 'Product_Code', 'Product_Name'
            )
        if 'Edition_Id' in data:
            data['Edition_Id'] = self._resolve_fk_pk(
                ProductEdition, data.get('Edition_Id'), 'Edition_Id', 'Edition_Code', 'Edition_Name'
            )
        if 'Plan_Id' in data:
            data['Plan_Id'] = self._resolve_fk_pk(
                Plan, data.get('Plan_Id'), 'Plan_Id', 'Plan_Name'
            )
        if 'Default_Converted_Plan_Id' in data:
            data['Default_Converted_Plan_Id'] = self._resolve_fk_pk(
                Plan, data.get('Default_Converted_Plan_Id'), 'Plan_Id', 'Plan_Name'
            )
        if 'Category_Id' in data:
            data['Category_Id'] = self._resolve_fk_pk(
                ProductCategory, data.get('Category_Id'), 'Category_Id', 'Category_Code', 'Category_Name'
            )
        if 'Enabled_Features' in data:
            data['Enabled_Features'] = self._resolve_features_list(data.get('Enabled_Features'))

        if not self.partial and not data.get('Product_Id'):
            first_prod = ProductMaster.objects.first()
            if first_prod:
                data['Product_Id'] = first_prod.id

        self._inject_audit_defaults(data, is_partial=self.partial)
        return super().to_internal_value(data)

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        t_id = getattr(instance, 'Trial_Id', None) or getattr(instance, 'Trial_Code', None)
        ret['Trial_Id'] = t_id
        if not ret.get('Trial_Code'):
            ret['Trial_Code'] = t_id
        return ret

    def get_product_name(self, obj):
        return getattr(obj.Product_Id, 'Product_Name', None) if obj.Product_Id else None

    def get_product_code(self, obj):
        return getattr(obj.Product_Id, 'Product_Code', None) if obj.Product_Id else None

    def get_edition_name(self, obj):
        return getattr(obj.Edition_Id, 'Edition_Name', None) if obj.Edition_Id else None

    def get_plan_name(self, obj):
        return getattr(obj.Plan_Id, 'Plan_Name', None) if obj.Plan_Id else None

    def get_category_name(self, obj):
        return getattr(obj.Category_Id, 'Category_Name', None) if obj.Category_Id else None

    def get_default_converted_plan_name(self, obj):
        return getattr(obj.Default_Converted_Plan_Id, 'Plan_Name', None) if obj.Default_Converted_Plan_Id else None

    def get_enabled_features_details(self, obj):
        return [
            {
                'id': feat.id,
                'Feature_Id': feat.Feature_Id,
                'Feature_Code': feat.Feature_Code,
                'Feature_Name': feat.Feature_Name,
            }
            for feat in obj.Enabled_Features.filter(Is_Deleted=False).order_by('id')
        ]

    def get_enabled_features_count(self, obj):
        return obj.Enabled_Features.filter(Is_Deleted=False).count()

    def get_duration_label(self, obj):
        days = getattr(obj, 'Trial_Duration_Days', None)
        return f"{days} Days" if days is not None else None





