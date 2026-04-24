from django.contrib import admin

from .models import AdminAction, Genre, Hall, Movie, MovieGenre, RecommendationHistory, Seat, Showtime, UserRating

admin.site.register(Genre)
admin.site.register(Movie)
admin.site.register(MovieGenre)
admin.site.register(Hall)
admin.site.register(Seat)
admin.site.register(Showtime)
admin.site.register(UserRating)
admin.site.register(RecommendationHistory)
admin.site.register(AdminAction)
