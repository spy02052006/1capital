from django.shortcuts import render, redirect

def root_redirect(request):
    """Redirect to website landing page if not authenticated, else dashboard"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    return redirect('website')

def website_view(request):
    """Render the One Capital website landing page"""
    context = {
        'title': 'One Capital | Premier Equity Advisory & Wealth Management',
    }
    return render(request, 'website.html', context)

def about_us_view(request):
    """Render the About Us page"""
    context = {
        'title': 'About Us | One Capital',
    }
    return render(request, 'about_us.html', context)

def mf_advisor_view(request):
    """Render the Mutual Fund Advisor recommendation form"""
    context = {
        'title': 'Mutual Fund Advisor | One Capital',
    }
    return render(request, '1capital_mf.html', context)
