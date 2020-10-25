from django.shortcuts import render
from django.views.generic import ListView
from django.db.models import Q
from . import plots
from .models import Country


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
    """View function for search page of site."""

    return render(request, 'search.html')

class SearchResultsView(ListView):
    """View class for search page of the site."""

    model = Country
    template_name = 'search_results.html'

    def get_queryset(self):
        """View method to retrieve the query information."""
        query = self.request.GET.get('q')

        # Verify the string isn't malicious

        if (len(query) > 3) and (len(query) < 30) and all(char.isalpha() or char == ' ' for char in query):
            object_list = Country.objects.filter(
                Q(name__icontains=query)
            ).values()
            if object_list:
                for x in object_list:
                    x['name'] = x['name'].capitalize()
                    x['corona'] = x['corona'].replace('\n', '')
                    x['corona'] = x['corona'].replace('  ', ' ')
                    x['corona'] = x['corona'].strip()
                    x['corona'] = x['corona'].replace(' .', '')
                    if x['corona'] == 'MISSING DATA':
                        x['corona'] = 'No data avaiable.'
                    x['quarantine'] = x['quarantine'].replace('\n', '')
                    x['quarantine'] = x['quarantine'].replace('  ', ' ')
                    x['quarantine'] = x['quarantine'].strip()
                    x['quarantine'] = x['quarantine'].replace(' .', '')
                    if x['quarantine'] == 'MISSING DATA':
                        x['quarantine'] = 'No data avaiable.'

            return object_list
