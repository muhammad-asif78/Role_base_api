# app/models/enums.py
from enum import Enum

class UserRole(str, Enum):
    CEO = "CEO"
    CTO = "CTO"
    ProjectLead = "ProjectLead"
    Engineer = "Engineer"
    Developer = "Developer"