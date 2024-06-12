from django.shortcuts import render, redirect, get_object_or_404
from store.models import Product, Variation
from . models import Cart, CartItem
from django.http import HttpResponse
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required

#to get the session id from the cookies, add _ or underscore will make it private function
def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    return cart




def add_cart(request, product_id):
    current_user = request.user
    product = Product.objects.get(id=product_id)
    
    if current_user.is_authenticated:
        product_variation_list = []
    
        if request.method == 'POST':
            for item in request.POST:
                key = item
                value = request.POST[key]
                try: 
                    variation = Variation.objects.get(product=product, variation_category__iexact=key,variation_value__iexact=value ) #iexact will ignore the upper case and lower case
                    product_variation_list.append(variation)
                except:
                    pass
        
        product = Product.objects.get(id=product_id)
        
        # ----------------creating a session key--------no need, user is authenticated---------------
        # try:
        #     cart = Cart.objects.get(cart_id=_cart_id(request)) #to get the session key
        # except Cart.DoesNotExist:
        #     cart = Cart.objects.create(cart_id=_cart_id(request))
        #     cart.save()
        # ------------------------------------------------------------- 
        
        is_cart_item_exists = CartItem.objects.filter(product=product,user=current_user).exists()
        
        if is_cart_item_exists:
            cart_item = CartItem.objects.filter(product=product, user=current_user)
            #existing variation  > database
            #current variation  > product_variation
            #item_id > data
            existing_variation_list = []
            id=[]
            for item in cart_item:
                existing_variation = item.variations.all()
                existing_variation_list.append(list(existing_variation))
                id.append(item.id)
        
            
            #increase the count of the specific variation
            if product_variation_list in existing_variation_list:
                index =  existing_variation_list.index(product_variation_list)   
                item_id = id[index]
                item = CartItem.objects.get(product=product, id = item_id)
                item.quantity +=1
                item.save()
                
            else: 
                item = CartItem.objects.create(product=product,user=current_user, quantity = 1) 
                if len(product_variation_list) > 0:
                    item.variations.clear()
                    item.variations.add(*product_variation_list)
                item.save()
        
        else:         #if no cart item exist it will create new item
            item = CartItem.objects.create(product=product,user=current_user, quantity = 1) 
            if len(product_variation_list) > 0:
                # cart_item.variations.clear()
                item.variations.add(*product_variation_list)
            item.save()
        return redirect('cart')
            
    else: 
        product_variation_list = []
        
        if request.method == 'POST':
            for item in request.POST:
                key = item
                value = request.POST[key]
                try: 
                    variation = Variation.objects.get(product=product, variation_category__iexact=key,variation_value__iexact=value ) #iexact will ignore the upper case and lower case
                    product_variation_list.append(variation)
                except:
                    pass
        
        product = Product.objects.get(id=product_id)
        
        # ----------------creating a session key-----------------------
        try:
            cart = Cart.objects.get(cart_id=_cart_id(request)) #to get the session key
        except Cart.DoesNotExist:
            cart = Cart.objects.create(cart_id=_cart_id(request))
            cart.save()
        # ------------------------------------------------------------- 
        
        is_cart_item_exists = CartItem.objects.filter(product=product,cart=cart).exists()
        
        if is_cart_item_exists:
            cart_item = CartItem.objects.filter(product=product, cart=cart)
            #existing variation  > database
            #current variation  > product_variation
            #item_id > data
            existing_variation_list = []
            id=[]
            for item in cart_item:
                existing_variation = item.variations.all()
                existing_variation_list.append(list(existing_variation))
                id.append(item.id)
            print(existing_variation_list)
            
            #increase the count of the specific variation
            if product_variation_list in existing_variation_list:
                index =  existing_variation_list.index(product_variation_list)   
                item_id = id[index]
                item = CartItem.objects.get(product=product, id = item_id)
                item.quantity +=1
                item.save()
                
            else: 
                item = CartItem.objects.create(product=product,cart=cart, quantity = 1) 
                if len(product_variation_list) > 0:
                    item.variations.clear()
                    item.variations.add(*product_variation_list)
                item.save()
        
        else:         #if no cart item exist it will create new item
            item = CartItem.objects.create(product=product,cart=cart, quantity = 1) 
            if len(product_variation_list) > 0:
                # cart_item.variations.clear()
                item.variations.add(*product_variation_list)
            item.save()
        return redirect('cart')

def remove_cart(request, product_id, cart_item_id):
    
    product = get_object_or_404(Product, id = product_id)
    try:
        if request.user.is_authenticated:
            cart_item = CartItem.objects.get(product=product, user = request.user, id = cart_item_id)
        else:
            cart = Cart.objects.get(cart_id = _cart_id(request))
            cart_item = CartItem.objects.get(product=product, cart = cart, id = cart_item_id)
        
        if cart_item.quantity > 1 :
                cart_item.quantity -= 1
                cart_item.save()
        else:
            cart_item.delete()
    except:
        pass

    return redirect('cart')

def remove_cart_item(request, product_id, cart_item_id):
    
    product = get_object_or_404(Product, id = product_id)
    
    if request.user.is_authenticated:
        cart_item  = CartItem.objects.get(product=product, user = request.user, id=cart_item_id)
       
    else:
        cart = Cart.objects.get(cart_id = _cart_id(request))
        cart_item  = CartItem.objects.get(product=product, cart = cart, id=cart_item_id)
       
    cart_item.delete()
    return redirect('cart')



def cart(request, total=0, quantity=0, cart_items=None):
    tax = 0
    grand_total = 0
    try:
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            quantity += cart_item.quantity
        tax = (2 * total)/100
        grand_total = total + tax
    except ObjectDoesNotExist:
        pass #just ignore
       
    tax  = (total * .02)
    grand_total = total + tax
        
    context={
        'cart_items':cart_items,
        'total': total,
        'quantity': quantity,
        'tax':tax,
        'grand_total': grand_total
        
    }
    return render(request, 'store/cart.html', context)

@login_required(login_url='login')
def checkout(request, total=0, quantity=0, cart_items=None):
    tax  = 0
    grand_total = 0
    try: 
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        
        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            quantity += cart_item.quantity
    except ObjectDoesNotExist:
        pass
       
    tax  = (total * .02)
    grand_total = total + tax
        
    context={
        'cart_items':cart_items,
        'total': total,
        'quantity': quantity,
        'tax':tax,
        'grand_total': grand_total
        
    }
    return render(request, 'store/checkout.html', context)