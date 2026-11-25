import json
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



class AddonPriceTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AddonPriceTemplate
        fields = '__all__'

class AddonPriceTemplateSerializers(serializers.ModelSerializer):

    class Meta:
        model = AddonPriceTemplate
        fields = '__all__'
        depth = 1



class AddonPricingSerializer(serializers.ModelSerializer):
    class Meta:
        model = AddonPricing
        fields = '__all__'

class AddonPricingSerializers(serializers.ModelSerializer):

    class Meta:
        model = AddonPricing
        fields = '__all__'
        depth = 1



class AddonTieredPricingSerializer(serializers.ModelSerializer):
    class Meta:
        model = AddonTieredPricing
        fields = '__all__'

class AddonTieredPricingSerializers(serializers.ModelSerializer):

    class Meta:
        model = AddonTieredPricing
        fields = '__all__'
        depth = 1



class AddonDiscountCouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = AddonDiscountCoupon
        fields = '__all__'

class AddonDiscountCouponSerializers(serializers.ModelSerializer):

    class Meta:
        model = AddonDiscountCoupon
        fields = '__all__'
        depth = 1




class AddonPriceHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = AddonPriceHistory
        fields = '__all__'

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



