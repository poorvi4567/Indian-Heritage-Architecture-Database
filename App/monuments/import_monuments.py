import csv
from monuments.models import Location, ArchitecturalStyle, Period, Monument

def run():
    with open("monuments.csv", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            location, _ = Location.objects.get_or_create(
                city=row["City"].strip(),
                state=row["State"].strip(),
                defaults={
                    "latitude": float(row["latitude"]) if row["latitude"] else 0,
                    "longitude": float(row["longitude"]) if row["longitude"] else 0,
                    "zone": row["Zone"]
                }
            )

            style, _ = ArchitecturalStyle.objects.get_or_create(
                name=row["architectural_style"]
            )

            period, _ = Period.objects.get_or_create(
                year=row["Establishment Year"]
            )

            Monument.objects.create(
                name=row["Name"],
                monument_type=row["Type"],
                zone=row["Zone"],
                year=row["Establishment Year"],
                location=location,
                style=style,
                period=period
            )
