from django.shortcuts import render
from .models import Tag
# Create your views here

def tag_view(request):
    words = Tag.objects.all()  # Fetch words from the database
    context = {'words': words}
    return render(request, 'tags/tag_to_sentence.html', context)

