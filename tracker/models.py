# tracker/models.py

from django.db import models
from datetime import datetime
def current_month():
    return datetime.now().month

def current_year():
    return datetime.now().year
class Habit(models.Model):
    name = models.CharField(max_length=100)
    month = models.IntegerField(default=current_month)
    year = models.IntegerField(default=current_year)

    def __str__(self):
        return self.name


class HabitRecord(models.Model):
    habit = models.ForeignKey(Habit, on_delete=models.CASCADE)
    day = models.IntegerField()
    completed = models.BooleanField(default=False)

    # 🔥 ADD THESE
    month = models.IntegerField(default=datetime.now().month)
    year = models.IntegerField(default=datetime.now().year)

    class Meta:
        unique_together = ('habit', 'day', 'month', 'year')