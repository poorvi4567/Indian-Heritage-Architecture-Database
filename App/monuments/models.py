from django.db import models


class Location(models.Model):
    location_id = models.AutoField(primary_key=True)
    city = models.TextField()
    state = models.TextField()
    latitude = models.FloatField()
    longitude = models.FloatField()
    zone = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "location"
        unique_together = ("city", "state")

    def __str__(self):
        return f"{self.city}, {self.state}"


class ArchitecturalStyle(models.Model):
    style_id = models.AutoField(primary_key=True)
    name = models.TextField(unique=True)
    monument_type = models.TextField(null=True, blank=True)
    
    class Meta:
        db_table = "architectural_style"

    def __str__(self):
        return self.name


class Period(models.Model):
    period_id = models.AutoField(primary_key=True)
    year = models.TextField(unique=True)

    class Meta:
        db_table = "period"

    def __str__(self):
        return str(self.year)


class Monument(models.Model):
    monument_id = models.AutoField(primary_key=True)
    name = models.TextField()
    monument_type = models.TextField(null=True, blank=True)
    zone = models.TextField(null=True, blank=True)
    # 'Year' column in CSV can be ranges or negative values, keep as text
    year = models.TextField(null=True, blank=True)
    # 'Establishment Year' is often numeric but can be missing or textual; store as integer when possible
    # NOTE: The attributes below are intentionally excluded from the relational Django model
    # and will be stored in a MongoDB collection (e.g. 'monument_details'). They remain
    # commented here for reference and to document the mapping used when importing the CSV.
    # establishment_year = models.IntegerField(null=True, blank=True)
    # time_to_visit_hours = models.FloatField(null=True, blank=True)
    # google_review_rating = models.FloatField(null=True, blank=True)
    # num_google_reviews_lakhs = models.FloatField(null=True, blank=True)
    # entrance_fee_inr = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    # airport_within_50km = models.BooleanField(null=True)
    # weekly_off = models.TextField(null=True, blank=True)
    # significance = models.TextField(null=True, blank=True)
    # dslr_allowed = models.BooleanField(null=True)
    # best_time_to_visit = models.TextField(null=True, blank=True)
    # image_url = models.URLField(null=True, blank=True)

    location = models.ForeignKey(
        Location,
        on_delete=models.CASCADE,
        related_name="monuments",
        null=True,
        blank = True
    )

    style = models.ForeignKey(
        ArchitecturalStyle,
        on_delete=models.SET_NULL,
        null=True,
        related_name="monuments"
    )

    period = models.ForeignKey(
        Period,
        on_delete=models.SET_NULL,
        null=True,
        related_name="monuments"
    )

    class Meta:
        db_table = "monument"

    def __str__(self):
        if self.location:
            return f"{self.name} ({self.location})"
        return self.name
