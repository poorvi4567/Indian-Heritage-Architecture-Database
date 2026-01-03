from django.shortcuts import render
from .models import Monument

def monument_list(request):
    monuments = Monument.objects.select_related(
        'location', 'style', 'period'
    ).all()

    return render(request, 'monuments.html', {
        'monuments': monuments
    })

def filter_monuments(request):
    state = request.GET.get("state")
    city = request.GET.get("city")
    style = request.GET.get("style")

    monuments = Monument.objects.all()

    if state:
        monuments = monuments.filter(location__state__iexact=state)

    if city:
        monuments = monuments.filter(location__city__iexact=city)

    if style:
        monuments = monuments.filter(style__name__iexact=style)

    return render(request, "monuments/filter.html", {
        "monuments": monuments
    })

def monuments_map(request):
    monuments = Monument.objects.select_related("location")
    return render(request, "map.html", {
        "monuments": monuments
    })