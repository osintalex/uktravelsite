from django.db import models
from django.urls import reverse  # Used to generate URLs by reversing the URL patterns


# Create your models here.


class Country(models.Model):
    """Model representing a country and corresponding information."""

    name = models.CharField(max_length=200, help_text="Enter the country name.")
    corona = models.TextField(
        max_length=10000, help_text="Enter coronavirus restriction information."
    )
    quarantine = models.TextField(
        max_length=10000, help_text="Enter quarantine restriction information"
    )
    date_of_information = models.DateField(
        help_text="Enter the date information was acquired.",
        blank=True,
        null=True,
    )
    sentiment = models.FloatField(
        help_text="Sentiment classification score",
        blank=True,
        null=True,
    )

    def __str__(self):
        """String for representing the Model object."""
        return self.name

    def get_absolute_url(self):
        """Returns the url to access a detail record for this book."""
        return reverse("country-detail", args=[str(self.id)])
