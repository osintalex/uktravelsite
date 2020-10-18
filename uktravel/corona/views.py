from django.shortcuts import render
from . import plots


# Create your views here.

def index(request):
    """View function for home page of site."""

    return render(request, 'index.html')

def inbound(request):
    """View function for inbound page of site."""

    plot_div = plots.plot_inbound()

    return render(request, 'inbound.html', context={'plot_div': plot_div})

def about(request):
    """View function for about page of site."""

    return render(request, 'about.html')

def outbound(request):
    """View function for outbound page of the site."""

    plot_div = plots.plot_outbound()

    return render(request, 'outbound.html', context={'plot_div': plot_div})

def search(request):
    """View function for home page of site."""

    return render(request, 'search.html')



