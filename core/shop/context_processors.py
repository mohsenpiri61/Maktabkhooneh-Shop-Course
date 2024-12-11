from .models import ProductCategoryModel

def categories_context(request):
    """
    ارسال دسته‌بندی‌ها به تمام صفحات
    """
    categories_parent = ProductCategoryModel.objects.filter(parent=None).prefetch_related("children")
    return {"categories_parent": categories_parent}
