from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from .models import Stock, Portfolio, Transaction
from django.db.models import Sum
from .forms import CustomUserCreationForm
import os

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            email = form.cleaned_data.get('email')
            subject = 'Welcome to Stockbroker'
            message = f'Hi {username},\n\nThank you for registering with Stockbroker! Your email {email} has been recorded. Start trading now.\n\nBest,\nStockbroker Team'
            from_email = settings.EMAIL_HOST_USER
            recipient_list = [email]
            send_mail(subject, message, from_email, recipient_list, fail_silently=False)
            messages.success(request, f'Account created for {username}! A welcome email has been sent to {email}.')
            return redirect('login')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomUserCreationForm()
    return render(request, 'register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            next_url = request.POST.get('next', request.GET.get('next'))
            if next_url and not next_url.startswith('/'):
                next_url = 'dashboard'
            return redirect(next_url or 'dashboard')
        else:
            messages.error(request, 'Invalid username or password')
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def dashboard(request):
    stocks = Stock.objects.all()
    return render(request, 'dashboard.html', {'stocks': stocks})

@login_required
def portfolio(request):
    portfolio_items = Portfolio.objects.filter(user=request.user)
    total_value = sum(item.stock.price * item.quantity for item in portfolio_items)
    return render(request, 'portfolio.html', {
        'portfolio_items': portfolio_items,
        'total_value': total_value
    })

@login_required
def buy_stock(request):
    if request.method == 'POST':
        stock_id = request.POST['stock_id']
        quantity = int(request.POST['quantity'])
        stock = Stock.objects.get(id=stock_id)
        
        
        total_cost = stock.price * quantity
        
       
        portfolio_item, created = Portfolio.objects.get_or_create(
            user=request.user,
            stock=stock,
            defaults={'quantity': quantity, 'purchase_price': stock.price}
        )
        if not created:
            portfolio_item.quantity += quantity
            portfolio_item.save()
        
       
        transaction = Transaction.objects.create(
            user=request.user,
            stock=stock,
            quantity=quantity,
            price=stock.price,
            transaction_type='BUY'
        )
        
       
        subject = f'Stock Purchase Confirmation'
        message = f'Hi {request.user.username},\n\nYou have successfully bought {quantity} shares of {stock.symbol} at ${stock.price} each. Total cost: ${total_cost}.\n\nTransaction ID: {transaction.id}\n\nBest,\nStockbroker Team'
        from_email = settings.EMAIL_HOST_USER
        recipient_list = [request.user.email]
        send_mail(subject, message, from_email, recipient_list, fail_silently=False)
        
        messages.success(request, f'Successfully bought {quantity} shares of {stock.symbol}')
        return redirect('dashboard')
    return redirect('dashboard')

@login_required
def sell_stock(request):
    if request.method == 'POST':
        stock_id = request.POST['stock_id']
        quantity = int(request.POST['quantity'])
        stock = Stock.objects.get(id=stock_id)
        
        portfolio_item = Portfolio.objects.get(user=request.user, stock=stock)
        if portfolio_item.quantity >= quantity:
            portfolio_item.quantity -= quantity
            if portfolio_item.quantity == 0:
                portfolio_item.delete()
            else:
                portfolio_item.save()
                
          
            transaction = Transaction.objects.create(
                user=request.user,
                stock=stock,
                quantity=quantity,
                price=stock.price,
                transaction_type='SELL'
            )
            
          
            total_proceeds = stock.price * quantity
            subject = f'Stock Sale Confirmation'
            message = f'Hi {request.user.username},\n\nYou have successfully sold {quantity} shares of {stock.symbol} at ${stock.price} each. Total proceeds: ${total_proceeds}.\n\nTransaction ID: {transaction.id}\n\nBest,\nStockbroker Team'
            from_email = settings.EMAIL_HOST_USER
            recipient_list = [request.user.email]
            send_mail(subject, message, from_email, recipient_list, fail_silently=False)
            
            messages.success(request, f'Successfully sold {quantity} shares of {stock.symbol}')
        else:
            messages.error(request, 'Not enough shares to sell')
        return redirect('portfolio')
    return redirect('portfolio')

def custom_404(request, exception):
    return render(request, '404.html', status=404)