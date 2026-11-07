from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def wiki_placeholder(request):
    """Временная заглушка до этапа чтения (models/views/wiki)."""
    return render(request, 'wiki/placeholder.html')
