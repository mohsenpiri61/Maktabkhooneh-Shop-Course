from django import template
from shop.models import ProductStatusType, ProductModel, WishlistProductModel, ProductCategoryModel

register = template.Library()


@register.inclusion_tag("includes/latest-products.html",takes_context=True)
def show_latest_products(context):
    request = context.get("request")
    latest_products = ProductModel.objects.filter(
        status=ProductStatusType.publish.value).order_by("-created_date")[:8]
    wishlist_items = WishlistProductModel.objects.filter(user=request.user).values_list("product__id", flat=True) if request.user.is_authenticated else []
    return {"latest_products": latest_products,"request":request,"wishlist_items":wishlist_items}


@register.inclusion_tag("includes/similar-products.html", takes_context=True)
def show_similar_products(context, product):
    request = context.get("request")
    
    # دریافت دسته‌بندی فعلی محصول
    main_category = product.category
    parent_category = main_category.parent if main_category else None
    
    # پیدا کردن دسته‌بندی‌های فرزند از دسته‌بندی والد
    if parent_category:
        product_categories = parent_category.children.all()
    else:
        product_categories = [main_category]  # اگر دسته‌بندی والد ندارد، فقط دسته‌بندی فعلی در نظر گرفته می‌شود.
    
    # فیلتر محصولات مشابه بر اساس دسته‌بندی
    similar_products = ProductModel.objects.filter(
        status=ProductStatusType.publish.value, 
        category__in=product_categories
    ).distinct().exclude(id=product.id).order_by("-created_date")[:4]
    wishlist_items = WishlistProductModel.objects.filter(user=request.user).values_list("product__id", flat=True) if request.user.is_authenticated else []
    
    return {
        "similar_prodcuts": similar_products,
        "request": request,
        "wishlist_items": wishlist_items
    }


@register.inclusion_tag("includes/swiper-products.html",takes_context=True)
def show_swiper_products(context):
    request = context.get("request")
    swiper_products = ProductModel.objects.filter(
        status=ProductStatusType.publish.value).distinct().order_by("-created_date")[:5]
    wishlist_items = WishlistProductModel.objects.filter(user=request.user).values_list("product__id", flat=True) if request.user.is_authenticated else []
    return {"swiper_products": swiper_products,"request":request,"wishlist_items":wishlist_items}



@register.inclusion_tag("includes/most-popular-products.html",takes_context=True)
def most_popular_products(context):
    request = context.get("request")
    popular_products = ProductModel.objects.filter(
        status=ProductStatusType.publish.value).distinct().order_by("-avg_rate")[:4] 
    wishlist_items = WishlistProductModel.objects.filter(user=request.user).values_list("product__id", flat=True) if request.user.is_authenticated else []
    return {"popular_products": popular_products, "request":request, "wishlist_items": wishlist_items}


@register.inclusion_tag("includes/discounted-products.html",takes_context=True)
def show_discounted_products(context):
    request = context.get("request")
    discounted_products = ProductModel.objects.filter(
        status=ProductStatusType.publish.value).distinct().order_by("-discount_percent")[:4]
    wishlist_items = WishlistProductModel.objects.filter(user=request.user).values_list("product__id", flat=True) if request.user.is_authenticated else []
    return {"discounted_products": discounted_products, "request":request, "wishlist_items": wishlist_items}


@register.inclusion_tag('includes/categories-tree.html')
def show_categories_tree():
    categories_parent = ProductCategoryModel.objects.filter(parent=None)
    return {'categories_parent': categories_parent}