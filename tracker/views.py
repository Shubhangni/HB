from django.shortcuts import render, redirect
from .models import Habit, HabitRecord
import math
import calendar
from datetime import datetime
from django.http import JsonResponse
from django.templatetags.static import static



# -------------------------
# Analytics (Top 5)
# -------------------------
def analytics(request):
    year = int(request.GET.get("year", datetime.today().year))
    month = int(request.GET.get("month", datetime.today().month))

    habits = Habit.objects.filter(month=month, year=year)

    total_completed = HabitRecord.objects.filter(
        completed=True,
        month=month,
        year=year
    ).count()

    data = []

    for habit in habits:
        count = HabitRecord.objects.filter(
            habit=habit,
            completed=True,
            month=month,
            year=year
        ).count()

        percent = int((count / total_completed) * 100) if total_completed else 0

        data.append({
            "name": habit.name,
            "count": count,
            "percent": percent
        })

    data = sorted(data, key=lambda x: x["count"], reverse=True)[:5]

    return JsonResponse(data, safe=False)


# -------------------------
# Common Stats
# -------------------------
def calculate_stats(year, month):
    total_days = calendar.monthrange(year, month)[1]

    habits = list(Habit.objects.filter(month=month, year=year))
    total_habits = len(habits)

    records = HabitRecord.objects.filter(
        month=month,
        year=year,
        completed=True
    )

    day_map = {}
    habit_map = {}

    for r in records:
        day_map[r.day] = day_map.get(r.day, 0) + 1
        habit_map.setdefault(r.habit_id, []).append(r.day)

    return total_days, habits, total_habits, records, day_map, habit_map


# -------------------------
# Toggle Habit (FIXED)
# -------------------------
def toggle(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid"}, status=400)

    habit_id = int(request.POST.get("habit"))
    day = int(request.POST.get("day"))

    # 🔥 FIX: use selected month/year
    month = int(request.POST.get("month") or datetime.today().month)
    year = int(request.POST.get("year") or datetime.today().year)

    obj, _ = HabitRecord.objects.get_or_create(
        habit_id=habit_id,
        day=day,
        month=month,
        year=year
    )

    obj.completed = not obj.completed
    obj.save()

    # stats
    total_days, habits, total_habits, records, day_map, habit_map = calculate_stats(year, month)

    # DAY %
    completed_today = day_map.get(day, 0)
    day_percent = int((completed_today / total_habits) * 100) if total_habits else 0
    day_rounded = max(10, (day_percent // 10) * 10) if day_percent > 0 else 0

    # HABIT %
    habit_completed = len(habit_map.get(habit_id, []))
    habit_percent = int((habit_completed / total_days) * 100)

    # TOTAL %
    total_completed = len(records)
    total_possible = total_habits * total_days
    total_percent = min(100, int((total_completed / total_possible) * 100)) if total_possible else 0

    total_rounded = max(10, (total_percent // 10) * 10) if total_percent > 0 else 0

    # AVG %
    avg_percent = int(sum(
        int((len(habit_map.get(h.id, [])) / total_days) * 100)
        for h in habits
    ) / total_habits) if total_habits else 0

    return JsonResponse({
        "day_percent": day_percent,
        "image": static(f"plants/plant_{day_rounded}.png"),
        "habit_percent": habit_percent,
        "habit_count": habit_completed,
        "total_percent": total_percent,
        "avg_percent": avg_percent,
        "final_image": static(
            f"plants/plant_{total_rounded}.png" if total_rounded > 0 else "plants/plant_0.png"
        )
    })


# -------------------------
# Home Page
# -------------------------
def home(request):
    year = int(request.GET.get("year", datetime.today().year))
    month = int(request.GET.get("month", datetime.today().month))

    total_days, habits, total_habits, records, day_map, habit_map = calculate_stats(year, month)

    days = list(range(1, total_days + 1))

    start_day_index = calendar.monthrange(year, month)[0]
    weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    day_names = [
        weekdays[(start_day_index + i) % 7] for i in range(total_days)
    ]

    # HABIT ROWS
    habit_rows = []
    for habit in habits:
        completed_days = habit_map.get(habit.id, [])
        count = len(completed_days)
        percent = int((count / total_days) * 100) if total_days else 0

        habit_rows.append({
            "id": habit.id,
            "name": habit.name,
            "days": completed_days,
            "count": count,
            "percent": percent
        })

    # DAY PROGRESS
    day_progress_list = []
    for day in days:
        completed = day_map.get(day, 0)
        percent = int((completed / total_habits) * 100) if total_habits else 0
        rounded = int(math.ceil(percent / 10) * 10) if percent > 0 else 0

        day_progress_list.append({
            "day": day,
            "percent": percent,
            "image": f"plants/plant_{rounded}.png"
        })

    # TOTAL
    total_completed = len(records)
    total_possible = total_habits * total_days if total_habits else 1

    total_percent = min(100, int((total_completed / total_possible) * 100))

    avg_percent = int(sum(h["percent"] for h in habit_rows) / len(habit_rows)) if habit_rows else 0

    final_rounded = int(math.ceil(total_percent / 10) * 10) if total_percent > 0 else 0
    final_image = "plants/plant_0.png" if total_percent == 0 else f"plants/plant_{final_rounded}.png"

    # navigation
    prev_month = 12 if month == 1 else month - 1
    prev_year = year - 1 if month == 1 else year

    next_month = 1 if month == 12 else month + 1
    next_year = year + 1 if month == 12 else year
    
    return render(request, "tracker/home.html", {
        "habit_rows": habit_rows,
        "days": days,
        "day_names": day_names,
        "day_progress_list": day_progress_list,
        "total_percent": total_percent,
        "avg_percent": avg_percent,
        "final_image": final_image,
        "month_name": calendar.month_name[month],
        "year": year,
        "month": month,
        "prev_month": prev_month,
        "prev_year": prev_year,
        "next_month": next_month,
        "next_year": next_year,
    })


# -------------------------
# Add Habit
# -------------------------
def add_habit(request):
    if request.method == "POST":
        name = request.POST.get("name")
        month = int(request.POST.get("month") or datetime.today().month)
        year = int(request.POST.get("year") or datetime.today().year)

        if name:
            Habit.objects.create(name=name, month=month, year=year)

    return redirect(f"/?month={month}&year={year}")


# -------------------------
# Reset Month
# -------------------------
def reset(request):
    if request.method == "POST":
        month = int(request.POST.get("month") or datetime.today().month)
        year = int(request.POST.get("year") or datetime.today().year)

        HabitRecord.objects.filter(month=month, year=year).delete()
        Habit.objects.filter(month=month, year=year).delete()

    return redirect(f"/?month={month}&year={year}")


# -------------------------
# Delete Habit
# -------------------------
def delete_habit(request, habit_id):
    if request.method == "POST":
        month = int(request.POST.get("month") or datetime.today().month)
        year = int(request.POST.get("year") or datetime.today().year)

        HabitRecord.objects.filter(
            habit_id=habit_id,
            month=month,
            year=year
        ).delete()

        Habit.objects.filter(
            id=habit_id,
            month=month,
            year=year
        ).delete()

    return redirect(f"/?month={month}&year={year}")

def copy_previous_month(request):
    if request.method == "POST":

        # 🔥 SAFE INPUT
        month = request.POST.get("month")
        year = request.POST.get("year")

        if not month or not year:
            today = datetime.today()
            month = today.month
            year = today.year
        else:
            month = int(month)
            year = int(year)

        # 🔁 PREVIOUS MONTH
        prev_month = 12 if month == 1 else month - 1
        prev_year = year - 1 if month == 1 else year
        
        prev_habits = Habit.objects.filter(
            month=prev_month,
            year=prev_year
        )

        # 🚫 IF NO DATA → DO NOTHING
        if not prev_habits.exists():
            return redirect(f"/?month={month}&year={year}")

        # 🧠 EXISTING HABITS
        existing_names = set(
            Habit.objects.filter(month=month, year=year)
            .values_list("name", flat=True)
        )

        # 📋 COPY ONLY NEW
        for habit in prev_habits:
            if habit.name not in existing_names:
                Habit.objects.create(
                    name=habit.name,
                    month=month,
                    year=year
                )

    return redirect(f"/?month={month}&year={year}")