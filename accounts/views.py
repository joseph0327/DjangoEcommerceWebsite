from django.shortcuts import render, redirect
import requests.utils
from .forms import RegistrationForm
from .models import Account
from django.contrib import messages, auth
from django.contrib.auth.decorators import login_required

from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage

from carts.views import _cart_id
from carts.models import Cart, CartItem

import requests

# Create your views here.



def register(request):
    form = RegistrationForm()
    if request.method == "POST":
        form = RegistrationForm(request.POST)  # this contains all the post values from the form
        if form.is_valid(): #valid if all values are inputted in the field
            #to fetch all the date from fom the form
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            phone_number = form.cleaned_data['phone_number']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            username = email.split('@')[0]
            user = Account.objects.create_user(first_name=first_name , last_name=last_name, username=username, email=email, password=password)
            user.phone_number =  phone_number  
            user.save() 
            
            #User Activation
            current_site = get_current_site(request)
            mail_subject = 'Please activate your account'
            message = render_to_string('accounts/account_verification_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user)
            })
            
            #then we need to send the mail
            to_email = email
            send_email = EmailMessage(mail_subject, message, to=[to_email])
            send_email.send()
            
            
            # messages.success(request, 'Thank you for the registering. We have sent email for activation')
            return redirect('/accounts/login/?command=verification&email='+email)
    else:
        form = RegistrationForm()
    
    context = {
        'form': form,
    }
    return render(request, 'accounts/register.html', context)

def login(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        
        user = auth.authenticate(email=email, password=password)
    
        if user is not None:
            try:
                cart = Cart.objects.get(cart_id=_cart_id(request))
                is_cart_item_exists = CartItem.objects.filter(cart=cart).exists()
                if is_cart_item_exists:
                    cart_item = CartItem.objects.filter(cart=cart)   
                    
                    #get the product variation by cart id
                    product_variation = []
                    for item in cart_item:
                        variation = item.variations.all()
                        product_variation.append(list(variation))

                    #getting the cart item of the user to access his product variations
                    cart_items = CartItem.objects.filter(user=user)
                    existing_var_list = []
                    id=[]
                    for item in cart_items:
                        existing_var = item.variations.all()
                        existing_var_list.append(list(existing_var))
                        id.append(item.id)

                    # checking product_variation exist in existing_var_list
                    for pr in product_variation:
                        if pr in existing_var_list:
                            index = existing_var_list.index(pr) #If pr exists, find the index of pr in existing_var_list using 
                            item_id = id[index]
                            item = CartItem.objects.get(id=item_id)
                            item.quantity +=1
                            item.user = user
                            item.save()
                        else:
                            cart_item = CartItem.objects.filter(cart=cart)
                            for item in cart_item:  
                               item.user = user
                               item.save()
            except:
                pass
            
            auth.login(request, user)
            messages.success(request, 'You are logged in !')
            url = request.META.get('HTTP_REFERER')
            try: 
                query = requests.utils.urlparse(url).query
                # next=/cart/checkout/
                params = dict(x.split('=') for x in query.split('&'))
                if 'next' in params:
                    nextPage = params['next']
                    return redirect(nextPage)
            except:
                return redirect('dashboard')
            
        else:
            messages.error(request,'Invalid login credential')  
            return redirect('login')    
        
    return render(request, 'accounts/login.html')

@login_required(login_url='login')
def logout(request):
    auth.logout(request)
    messages.success(request, 'You are logged out !')
    return redirect('login')


def activate(request, uidb64, token):
    try: 
        uid = urlsafe_base64_decode(uidb64).decode() #decoded to get the primary key of the user
        user = Account._default_manager.get(pk = uid) # get the primary key of the user from the Account model
        
    except(TypeError,ValueError, OverflowError, Account.DoesNotExist):
        User = None
        
    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, 'Congratulations! Your account is activated.')
        return redirect('login')
    else:
        messages.error(request, 'Invalid activation link')
        return redirect('register')
    
@login_required(login_url='login')
def dashboard(request):
    return render(request,'accounts/dashboard.html')

def forgotPassword(request):
    if request.method == 'POST':
        email = request.POST['email']
        account = Account.objects.filter(email=email).exists()
        
        if account:
            user = Account.objects.get(email__exact = email)
            
            #reset password email 
            current_site = get_current_site(request)
            mail_subject = 'Account password reset'
            message = render_to_string('accounts/reset_password_email.html', {
                'user': user,
                'domain': current_site,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user)
            })
            
            to_mail = email
            send_email = EmailMessage (mail_subject, message, to=[to_mail])
            send_email.send()
            messages.success(request, f'We have a sent a link to your {email} to reset your password. Please check your email. Thank you!')
        else:
            messages.error(request, 'Account does not exist')
            return redirect('forgotPassword')
        
    return render(request,'accounts/forgotPassword.html')

def resetPassword_validate(request, uidb64, token):
    try: 
        uid = urlsafe_base64_decode(uidb64).decode() #decoded to get the primary key of the user
        user = Account._default_manager.get(pk = uid) # get the primary key of the user from the Account model/ or get the actual user
        
    except(TypeError,ValueError, OverflowError, Account.DoesNotExist):
        User = None
    
    if user is not None and default_token_generator.check_token(user, token):
        request.session['uid'] = uid
        messages.success(request, 'Please reset your password. Enter the new password.')
        return redirect('resetPassword')
    else:
        messages.error(request, "The link is no longer valid")
        return redirect('resetPassword')
       

def resetPassword(request):
    if request.method =='POST':
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']
        
        if password == confirm_password:
            uid = request.session.get('uid')
            user= Account.objects.get(pk = uid)
            user.set_password(password)
            user.save()
            messages.success(request, 'Password successfully saved.')
            return redirect('login')
        else:
            messages.error(request, 'Password doest not match.')
            return redirect('resetPassword')
        
    return render(request, 'accounts/resetPassword.html')
    
