from flask import Blueprint
dashboard_bp = Blueprint('dashboard', __name__)

from .routesDashboard import dashboard
