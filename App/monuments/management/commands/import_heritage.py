import csv
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from monuments.models import Location, ArchitecturalStyle, Period, Monument

try:
	from pymongo import MongoClient
except Exception:
	MongoClient = None


def _bool_from_yes_no(val):
	if val is None:
		return None
	v = val.strip().lower()
	if v in ("yes", "y", "true", "1"):
		return True
	if v in ("no", "n", "false", "0"):
		return False
	return None


class Command(BaseCommand):
	help = "Import monuments CSV into Django models and store extra fields in MongoDB"

	def add_arguments(self, parser):
		parser.add_argument('csv_path', help='Path to CSV file')
		parser.add_argument('--mongo-uri', help='MongoDB URI (optional)', default='mongodb://localhost:27017')
		parser.add_argument('--mongo-db', help='MongoDB database name', default='heritage')

	def handle(self, *args, **options):
		csv_path = options['csv_path']
		mongo_uri = options['mongo_uri']
		mongo_db = options['mongo_db']

		use_mongo = MongoClient is not None
		if not use_mongo:
			self.stdout.write(self.style.WARNING('pymongo not installed — MongoDB writes will be skipped.'))

		mongo_client = None
		mongo_col = None
		if use_mongo:
			mongo_client = MongoClient(mongo_uri)
			mongo_col = mongo_client[mongo_db]['monument_details']

		try:
			with open(csv_path, newline='', encoding='utf-8') as fh:
				reader = csv.DictReader(fh)
				created = 0
				updated = 0
				for row in reader:
					name = row.get('Name') or row.get('name')
					if not name:
						continue

					city = row.get('City') or row.get('city')
					state = row.get('State') or row.get('state')
					style_name = (row.get('architectural_style') or row.get('Architectural Style') or '').strip()
					period_year = (row.get('Establishment Year') or row.get('year') or '').strip()
					monument_type = (row.get('Type') or row.get('type') or '').strip()
					zone = (row.get('Zone') or row.get('zone') or '').strip()

					latitude = row.get('latitude') or row.get('Latitude')
					longitude = row.get('longitude') or row.get('Longitude')

					with transaction.atomic():
						# Location
						location = None
						if city and state:
							location, _ = Location.objects.get_or_create(city=city.strip(), state=state.strip(), defaults={
								'latitude': float(latitude) if latitude else 0.0,
								'longitude': float(longitude) if longitude else 0.0,
							})

						# Style
						style = None
						if style_name:
							style, _ = ArchitecturalStyle.objects.get_or_create(name=style_name)

						# Period
						period = None
						if period_year:
							period, _ = Period.objects.get_or_create(year=period_year)

						# Monument
						monument_values = {
							'monument_type': monument_type or None,
							'zone': zone or None,
							'year': period_year or None,
							'location': location,
							'style': style,
							'period': period,
						}

						monument_obj, created_flag = Monument.objects.update_or_create(
							name=name.strip(),
							defaults=monument_values
						)
						if created_flag:
							created += 1
						else:
							updated += 1

						# Prepare extra document for MongoDB
						if use_mongo and mongo_col is not None:
							extra = {
								'name': name.strip(),
								'establishment_year': row.get('Establishment Year') or row.get('establishment_year'),
								'time_to_visit_hours': row.get('time needed to visit in hrs'),
								'google_review_rating': row.get('Google review rating'),
								'entrance_fee_inr': row.get('Entrance Fee in INR'),
								'airport_within_50km': _bool_from_yes_no(row.get('Airport with 50km Radius')),
								'weekly_off': row.get('Weekly Off'),
								'significance': row.get('Significance'),
								'dslr_allowed': _bool_from_yes_no(row.get('DSLR Allowed')),
								'num_google_reviews_lakhs': row.get('Number of google review in lakhs'),
								'best_time_to_visit': row.get('Best Time to visit'),
								'image_url': row.get('Image URL') or row.get('Image URL'),
								'source_row': row,
								'monument_id': monument_obj.monument_id,
							}
							# upsert by monument_id
							mongo_col.update_one({'monument_id': extra['monument_id']}, {'$set': extra}, upsert=True)

				self.stdout.write(self.style.SUCCESS(f'Imported: {created}, Updated: {updated}'))

		except FileNotFoundError as e:
			raise CommandError(f'File not found: {csv_path}')
		finally:
			if mongo_client:
				mongo_client.close()

