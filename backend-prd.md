

# 🧩 **Product Requirements Document (PRD)**

## Tavonga Support System – **Backend API (Django REST Framework)**

---

### **Project Overview**

The backend for the Tavonga Support System will be developed using **Django REST Framework (DRF)**. It will expose secure RESTful APIs that power two frontend applications:

* A **Flutter-based Carer Mobile App**
* A **Next.js + Tailwind Admin Web Dashboard**

The backend will manage authentication, behavior tracking, activity planning, goal management, shift tracking, reporting, and media uploads.

---

### **Level**

Advanced

---

### **Type of Project**

Backend API Development, RESTful Services, Media Handling, Auth + Role Management

---

### **Technology Stack**

* **Language:** Python 3.10+
* **Framework:** Django 4.x, Django REST Framework
* **Auth:** JWT Authentication with Role-based Access Control
* **Database:** PostgreSQL
* **Media:** Cloudinary / AWS S3 for image/video storage
* **Docs:** Swagger or DRF YASG for API documentation
* **Testing:** Pytest or Django's built-in test suite

---

### **Core API Modules & Endpoints**

#### 1. **Authentication & Users**

* `/api/auth/register/` – Register carer (admin approval required)
* `/api/auth/login/` – Login and return JWT
* `/api/auth/profile/` – Get/update user profile
* `/api/users/` – Admin: view/update/disable carers
* `/api/users/{id}/approve/` – Admin: approve carer signup

---

#### 2. **Behavior Tracking**

* `/api/behaviors/` – Submit new behavior log
* `/api/behaviors/{id}/` – View/update/delete log (admin only)
* `/api/behaviors/history/?date=&severity=&type=` – Filter behavior logs
* Fields: location, activity\_before, behavior\_list, warning\_signs, duration, severity, harm\_to\_self/others, intervention, media

---

#### 3. **Daily Activities**

* `/api/activities/` – CRUD for activity templates (admin only)
* `/api/activities/logs/` – Carer logs daily activities
* `/api/activities/schedule/` – Admin assigns daily activities
* Fields: goal tag, location, instructions, prerequisites, completed, notes, media

---

#### 4. **Goals**

* `/api/goals/` – Admin creates/edit goals
* `/api/goals/{id}/track/` – Carer logs progress toward a goal
* `/api/goals/progress/` – Admin views goal performance by date or carer

---

#### 5. **Shifts**

* `/api/shifts/` – Admin assigns shifts
* `/api/shifts/{carer_id}/` – Carer views assigned shifts
* `/api/shifts/{id}/clock-in/` – Carer clocks in (POST)
* `/api/shifts/{id}/clock-out/` – Carer clocks out (PATCH)
* Fields: date, start\_time, end\_time, clock\_in, clock\_out, location, status

---

#### 6. **Reports**

* `/api/reports/behaviors/` – Filter/export logs by carer/date/goal
* `/api/reports/activities/` – Filter/export activity logs
* `/api/reports/shifts/` – Shift attendance summary

---

#### 7. **Media Uploads**

* `/api/media/upload/` – Upload photos/videos with metadata
* Accepts: base64/image file (secured & validated)

---

### **Security & Access Control**

* JWT-based authentication
* Role-based permissions:

  * **Admin**: Full access to all endpoints
  * **Carer**: Limited to personal logs and assigned data
* Rate-limiting and throttling for abusive requests
* Validation for shift clock-ins (e.g., must be within shift window)

---

### **Database Models (Simplified)**

```python
class User(AbstractUser):
    is_admin = models.BooleanField(default=False)
    approved = models.BooleanField(default=False)

class BehaviorLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    location = models.CharField()
    behaviors = ArrayField(models.CharField())
    severity = models.CharField()
    intervention = models.TextField()
    media = models.URLField(blank=True)

class Activity(models.Model):
    name = models.CharField()
    goal = models.ForeignKey('Goal', on_delete=models.SET_NULL, null=True)

class ActivityLog(models.Model):
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    completed = models.BooleanField()
    notes = models.TextField(blank=True)

class Goal(models.Model):
    name = models.CharField()
    description = models.TextField()

class Shift(models.Model):
    carer = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    clock_in = models.DateTimeField(null=True, blank=True)
    clock_out = models.DateTimeField(null=True, blank=True)
```

---

### **Technical Requirements**

* Django REST Framework serializers and viewsets
* Filtering with `django-filter`
* Pagination and sorting on all list endpoints
* Async support where relevant (clock-in/out)
* Swagger/OpenAPI auto-generated documentation
* Admin panel for manual override (Django Admin)

---

### **Deliverables**

* Full Django REST API project with:

  * Models, serializers, viewsets
  * Role-based permissions and JWT Auth
  * Swagger docs + Postman collection
  * Seeded database with example data
* Deployed version (optional: Render, Railway, or DigitalOcean)

---

