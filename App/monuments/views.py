from django.shortcuts import render, get_object_or_404
from django.conf import settings
from .models import Monument
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import google.generativeai as genai
from django.db import connection

def home(request):
    """Home page with project description and navigation"""
    return render(request, 'home.html')

def monument_list(request):
    monuments = Monument.objects.select_related('location', 'style', 'period').all()
    return render(request, 'monuments.html', {'monuments': monuments})

def filter_monuments(request):
    monuments = Monument.objects.select_related('location', 'style', 'period').all()
    
    state = request.GET.get('state', '').strip()
    city = request.GET.get('city', '').strip()
    style = request.GET.get('style', '').strip()
    
    if state:
        monuments = monuments.filter(location__state__iexact=state)
    if city:
        monuments = monuments.filter(location__city__iexact=city)
    if style:
        monuments = monuments.filter(style__name__iexact=style)
    
    return render(request, 'filter.html', {'monuments': monuments})

def monuments_map(request):
    monuments = Monument.objects.select_related('location').all()
    return render(request, 'map.html', {'monuments': monuments})

def monument_detail(request, monument_id):
    """Detail page showing data from both SQLite and MongoDB Atlas"""
    # Get monument from SQLite
    monument = get_object_or_404(
        Monument.objects.select_related('location', 'style', 'period'),
        monument_id=monument_id
    )
    
    # Try to fetch additional data from MongoDB Atlas
    mongo_data = None
    mongo_error = False
    
    try:
        # Connect to MongoDB Atlas
        client = MongoClient(
            settings.MONGODB_URI,
            serverSelectionTimeoutMS=5000  # 5 second timeout
        )
        
        # Test connection
        client.admin.command('ping')
        
        # Get database and collection
        db = client[settings.MONGODB_DB_NAME]
        collection = db[settings.MONGODB_COLLECTION]
        
        # Fetch monument details
        mongo_data = collection.find_one({'monument_id': monument_id})
        
        client.close()
        
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        mongo_error = True
        print(f"MongoDB Atlas connection error: {e}")
    except Exception as e:
        mongo_error = True
        print(f"Error fetching MongoDB data: {e}")
    
    # Placeholder image URL
    placeholder_image = "https://via.placeholder.com/800x400/FF9933/FFFFFF?text=No+Image+Available"
    
    context = {
        'monument': monument,
        'mongo_data': mongo_data,
        'mongo_error': mongo_error,
        'placeholder_image': placeholder_image,
    }
    
    return render(request, 'monument_detail.html', context)

def nlp_search(request):
    results = None
    columns = None
    query = ""
    error = None
    sql_query = ""

    if request.method == 'POST':
        query = request.POST.get('query', '').strip()
        if query:
            try:
                # Configure Gemini
                if not settings.GEMINI_API_KEY:
                    raise ValueError("GEMINI_API_KEY not found in settings.")
                
                genai.configure(api_key=settings.GEMINI_API_KEY)
                model = genai.GenerativeModel('gemini-2.5-flash')

                # Schema context for the LLM
                schema = """
                Table: location
                Columns: location_id (pk), city, state, latitude, longitude, zone

                Table: architectural_style
                Columns: style_id (pk), name, monument_type

                Table: period
                Columns: period_id (pk), year

                Table: monument
                Columns: monument_id (pk), name, monument_type, zone, year, location_id (fk), style_id (fk), period_id (fk)
                """

                prompt = f"""
                You are an SQL expert. Convert the following natural language query into a valid SQL query for a SQLite database.
                
                Database Schema:
                {schema}

                Rules:
                1. Only generate SELECT statements.
                2. Do not use markdown formatting (no ```sql ... ```).
                3. Return ONLY the raw SQL string.
                4. Use LIKE for partial matches.
                5. If the user asks for a count, return a count.
                6. Join tables as necessary using the foreign keys.
                
                7. When selecting monuments, ALWAYS include the 'monument_id' column.
                8. Use 'LOWER(column) LIKE LOWER('%value%')' for case-insensitive string matching.
                
                Query: "{query}"
                """

                response = model.generate_content(prompt)
                generated_sql = response.text.strip()
                
                # Clean up if the model decides to add backticks despite instructions
                generated_sql = generated_sql.replace('```sql', '').replace('```', '').strip()
                
                if not generated_sql.lower().startswith('select'):
                    raise ValueError("Generated query is not a SELECT statement.")
                
                sql_query = generated_sql

                with connection.cursor() as cursor:
                    cursor.execute(sql_query)
                    if cursor.description:
                        columns = [col[0] for col in cursor.description]
                        raw_results = cursor.fetchall()
                        
                        # Process results to add links
                        results = []
                        monument_id_idx = -1
                        name_idx = -1
                        
                        # Find indices safely
                        for i, col in enumerate(columns):
                            if col.lower() == 'monument_id':
                                monument_id_idx = i
                            elif col.lower() == 'name':
                                name_idx = i
                        
                        for row in raw_results:
                            processed_row = []
                            monument_id = row[monument_id_idx] if monument_id_idx != -1 else None
                            
                            for i, cell in enumerate(row):
                                cell_data = {'value': cell, 'url': None}
                                # If this is the name column and we have a valid monument_id, make it a link
                                if i == name_idx and monument_id:
                                    cell_data['url'] = f"/monument/{monument_id}/"
                                processed_row.append(cell_data)
                            results.append(processed_row)
                            
                    else:
                        results = []
                        columns = []

            except Exception as e:
                error = str(e)

    return render(request, 'nlp_search.html', {
        'results': results,
        'columns': columns,
        'query': query,
        'error': error,
        'sql_query': sql_query
    })