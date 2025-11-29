from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
import requests
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from .models import Payment, Profile



# --- تنظیمات زرین‌پال ---
MERCHANT = "00000000-0000-0000-0000-000000000000" # برای سندباکس نیازی به مرچنت واقعی نیست اما فرمت باید رعایت شود
ZP_API_REQUEST = "https://sandbox.zarinpal.com/pg/v4/payment/request.json"
ZP_API_VERIFY = "https://sandbox.zarinpal.com/pg/v4/payment/verify.json"
ZP_API_STARTPAY = "https://sandbox.zarinpal.com/pg/StartPay/{authority}"
CALLBACK_URL = "http://127.0.0.1:8000/users/verify/" # آدرس برگشت پس از پرداخت

# قیمت هر سکه (مثلاً ۱۰۰۰ تومان)
COIN_PRICE = 1000



def signup_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'users/signup.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            if 'next' in request.POST:
                return redirect(request.POST.get('next'))
            else:
                return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'users/login.html', {'form': form})



@login_required
def home_view(request):
    return render(request, 'Video/../templates/home.html')


@login_required
def purchase_coins_view(request):
    """صفحه‌ای برای انتخاب تعداد سکه"""
    if request.method == 'POST':
        coins_to_buy = int(request.POST.get('coins', 10))  # پیش‌فرض ۱۰ سکه
        amount = coins_to_buy * COIN_PRICE  # محاسبه قیمت کل
        description = f"خرید {coins_to_buy} سکه برای کاربر {request.user.username}"

        # 1. ارسال درخواست به زرین‌پال
        data = {
            "merchant_id": MERCHANT,
            "amount": amount,
            "callback_url": CALLBACK_URL,
            "description": description,
        }
        headers = {'content-type': 'application/json'}

        try:
            response = requests.post(ZP_API_REQUEST, data=json.dumps(data), headers=headers)
            res_data = response.json()

            if res_data['data']['code'] == 100:
                authority = res_data['data']['authority']

                # 2. ذخیره اطلاعات پرداخت در دیتابیس قبل از رفتن به درگاه
                Payment.objects.create(
                    user=request.user,
                    amount=amount,
                    coins_amount=coins_to_buy,
                    authority=authority
                )

                # 3. هدایت کاربر به درگاه
                return redirect(ZP_API_STARTPAY.format(authority=authority))
            else:
                return HttpResponse(f"Error connecting to gateway: {res_data['errors']}")
        except Exception as e:
            return HttpResponse(f"Error: {str(e)}")

    return render(request, 'users/purchase.html')


@login_required
def verify_payment_view(request):
    """بررسی نتیجه پرداخت پس از بازگشت از بانک"""
    authority = request.GET.get('Authority')
    status = request.GET.get('Status')

    if status == 'NOK':
        return HttpResponse("پرداخت ناموفق بود یا توسط کاربر لغو شد.")

    # پیدا کردن رکورد پرداخت
    payment = get_object_or_404(Payment, authority=authority)

    data = {
        "merchant_id": MERCHANT,
        "amount": payment.amount,
        "authority": authority,
    }
    headers = {'content-type': 'application/json'}

    try:
        response = requests.post(ZP_API_VERIFY, data=json.dumps(data), headers=headers)
        res_data = response.json()

        if res_data['data']['code'] == 100:  # کد ۱۰۰ یعنی پرداخت موفق
            if not payment.is_paid:
                # 1. آپدیت وضعیت پرداخت
                payment.is_paid = True
                payment.save()

                # 2. اضافه کردن سکه به پروفایل کاربر
                profile = Profile.objects.get(user=payment.user)
                profile.coins += payment.coins_amount
                profile.save()

                return HttpResponse(
                    f"پرداخت موفق! {payment.coins_amount} سکه به حساب شما افزوده شد. کد رهگیری: {res_data['data']['ref_id']}")
            else:
                return HttpResponse("این تراکنش قبلاً محاسبه شده است.")
        else:
            return HttpResponse(f"تراکنش ناموفق. کد خطا: {res_data['data']['code']}")

    except Exception as e:
        return HttpResponse(f"Error verifying payment: {str(e)}")



def logout_view(request):
    if request.method == 'POST':
        logout(request)
        return redirect('login')
    return redirect('home')
