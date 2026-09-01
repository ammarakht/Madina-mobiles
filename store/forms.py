from django import forms
from .models import Product, Category, Banner


class ProductForm(forms.ModelForm):
    category = forms.ChoiceField(choices=[], required=True)

    class Meta:
        model = Product
        fields = ['name', 'sku', 'category', 'original_price', 'sale_price',
                  'rating', 'review_count', 'in_stock', 'is_flash_sale',
                  'is_featured', 'image_url', 'image2_url']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. iPhone 15 Pro Max'}),
            'sku': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. APL-IP15PM-256'}),
            'original_price': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': 'e.g. 450000'}),
            'sale_price': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': 'e.g. 419999'}),
            'rating': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.1', 'min': '0', 'max': '5', 'placeholder': '4.8'}),
            'review_count': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': 'e.g. 142'}),
            'image_url': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'https:// or uploaded file path', 'id': 'id_image_url'}),
            'image2_url': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'https:// or uploaded file path (optional hover image)', 'id': 'id_image2_url'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['image_url'].required = False
        self.fields['image2_url'].required = False
        db_categories = Category.objects.all().order_by('order')
        choices = [(cat.slug, cat.name) for cat in db_categories]
        if not choices:
            choices = Product.CATEGORY_CHOICES
        self.fields['category'].choices = choices
        self.fields['category'].widget.attrs['class'] = 'form-input'


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'slug', 'icon', 'image_url', 'subtitle', 'order']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Smartphones'}),
            'slug': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. smartphones'}),
            'icon': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. 📱 or fa-mobile'}),
            'image_url': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'https:// or uploaded image URL', 'id': 'id_category_image_url'}),
            'subtitle': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. NEW COLLECTION (optional)'}),
            'order': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': '0'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['image_url'].required = False
        self.fields['subtitle'].required = False
        self.fields['icon'].required = False


class BannerForm(forms.ModelForm):
    class Meta:
        model = Banner
        fields = ['title', 'subtitle', 'cta_text', 'cta_link', 'image_url', 'order', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. New smartphones Arrival'}),
            'subtitle': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Tagline or subtitle text'}),
            'cta_text': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Shop Now'}),
            'cta_link': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. /category/smartphones/'}),
            'image_url': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'https:// or uploaded file path', 'id': 'id_banner_image_url'}),
            'order': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': '0'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['image_url'].required = False
