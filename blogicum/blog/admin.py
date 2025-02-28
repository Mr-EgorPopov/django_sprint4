from django.contrib import admin

from blog.models import Category, Comment, Location, Post, PostAdmin

admin.site.register(Post, PostAdmin)
admin.site.register(Category)
admin.site.register(Location)
admin.site.register(Comment)
