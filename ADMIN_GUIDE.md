# Admin Dashboard Guide



---


## Overview

The Admin page provides all permissions required to manage the application completely.

---


## Default Admin Login

After running `migrate_database.py`, an admin user is created:

- **Email:** `admin@admin.com`
- **Password:** [Set by admin]
- **Role:** `admin`

⚠️ Change the password after the first login!

---


## How to Access

### 1. Login as Admin:
1. Open: http://127.0.0.1:8000/login
2. Enter:
   - Email: `admin@admin.com`
   - Password: [Set by admin]
3. After login, Admin links will appear

### 2. Direct Access:
- http://127.0.0.1:8000/admin

---

## 📊 الميزات المتاحة

### 1. Dashboard Statistics
- **Total users:** Number of all users
- **Active users:** Number of active users
- **Total analyses:** Number of all analyses
- **Today's analyses:** Number of analyses today

### 2. Users Management

#### View all users:
- List of all users with details
- Shows: ID, Username, Email, Role, Status, Number of analyses

#### Permissions:
- ✅ **View user details**
- ✅ **Change Role** (user ↔ admin)
- ✅ **Activate/Deactivate user**
- ✅ **Delete user** (with all analyses)

### 3. Analyses Management

#### View all analyses:
- List of all analyses from all users
- Shows: ID, Text, Sentiment, Confidence, User, Date

#### Permissions:
- ✅ **Delete analysis**
- ✅ **View full analysis details**

### 4. Sentiment Statistics

#### Sentiment distribution:
- Shows the count of each sentiment in the system
- Visual chart with Emojis
- Accurate statistics

---

## Permissions System

### Admin Role:
- ✅ Access Admin page
- ✅ View all users
- ✅ Edit user permissions
- ✅ Activate/Deactivate users
- ✅ Delete users
- ✅ View all analyses
- ✅ Delete any analysis
- ✅ View statistics

### User Role (regular):
- ❌ Cannot access Admin page
- ✅ Can only use regular features

---

## 🛠️ Admin API Endpoints

### Statistics:
- `GET /admin/stats` - Get all statistics

### User Management:
- `GET /admin/users` - قائمة جميع المستخدمين
- `GET /admin/users/{user_id}` - تفاصيل مستخدم
- `PUT /admin/users/{user_id}/role?role={role}` - تحديث role
- `PUT /admin/users/{user_id}/status?status={status}` - تحديث status
- `DELETE /admin/users/{user_id}` - حذف مستخدم

### Analysis Management:
- `GET /admin/analyses` - قائمة جميع التحليلات
- `DELETE /admin/analyses/{analysis_id}` - حذف تحليل
- `DELETE /admin/analyses/user/{user_id}` - حذف جميع تحليلات مستخدم

---

## ⚠️ ملاحظات أمنية

1. **تغيير كلمة المرور:**
   - قم بتغيير كلمة مرور admin فوراً بعد أول تسجيل دخول
   - استخدم كلمة مرور قوية

2. **حماية الصفحة:**
   - الصفحة محمية بـ Admin-only access
   - يتم التحقق من صلاحيات admin في كل request

3. **القيود:**
   - Admin لا يمكنه حذف نفسه
   - Admin لا يمكنه تغيير role نفسه
   - Admin لا يمكنه تعطيل نفسه

---

## 🎨 التصميم

- ✅ تصميم عصري مع Glass Morphism
- ✅ Tabs للتنقل بين الأقسام
- ✅ Tables منظمة وواضحة
- ✅ Action buttons لكل عنصر
- ✅ Loading states
- ✅ Empty states جميلة
- ✅ Responsive design

---

## 📝 استخدامات عملية

### سيناريو 1: تعيين مستخدم كـ Admin
1. افتح صفحة Admin
2. اذهب لـ "Users Management"
3. اضغط على زر "Toggle Role" بجانب المستخدم
4. تأكيد التغيير

### سيناريو 2: تعطيل مستخدم
1. اذهب لـ "Users Management"
2. اضغط على زر "Deactivate" بجانب المستخدم
3. المستخدم لن يتمكن من تسجيل الدخول

### سيناريو 3: حذف مستخدم
1. اذهب لـ "Users Management"
2. اضغط على زر "Delete" بجانب المستخدم
3. ⚠️ سيتم حذف جميع تحليلاته أيضاً

### سيناريو 4: حذف تحليل غير مناسب
1. اذهب لـ "All Analyses"
2. ابحث عن التحليل
3. اضغط على زر "Delete"

---

## ✅ الخلاصة

**صفحة Admin جاهزة بالكامل مع جميع الصلاحيات!**

- ✅ نظام صلاحيات كامل
- ✅ إدارة المستخدمين
- ✅ إدارة التحليلات
- ✅ إحصائيات شاملة
- ✅ تصميم احترافي
- ✅ أمان محسن

**الوصول:** http://127.0.0.1:8000/admin

---

**تم الإنشاء:** 2025-01-27

