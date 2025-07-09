# roles.py

from rolepermissions.roles import AbstractUserRole

class Pastor(AbstractUserRole):
    available_permissions = {
        'manage_all_members': True,
        'create_education': True,
        'view_prayers': True,
    }

class Elder(AbstractUserRole):
    available_permissions = {
        'manage_group_members': True,
        'record_carelog': True,
    }

class Teacher(AbstractUserRole):
    available_permissions = {
        'record_student_attendance': True,
    }

class Member(AbstractUserRole):
    available_permissions = {
        'view_bulletin': True,
        'apply_for_volunteer': True,
    }
