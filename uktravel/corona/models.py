from django.db import models
from django.urls import reverse  # Used to generate URLs by reversing the URL patternss

# Create your models here.

class Country(models.Model):
    """Model representing a country and corresponding information."""
    name = models.CharField(max_length=200)
    corona = models.TextField(max_length=10000, help_text='Enter coronavirus restriction information.')
    quarantine = models.TextField(max_length=10000, help_text='Enter quarantine restriction information')
    date_of_information = models.DateField(null=True, blank=True)

    def __str__(self):
        """String for representing the Model object."""
        return self.name

    def get_absolute_url(self):
        """Returns the url to access a detail record for this book."""
        return reverse('country-detail', args=[str(self.id)])