"""
Property context utilities for multi-property support.

Provides helpers to manage the active property in the user session
and apply property filters to database queries.
"""

from flask import session
from database.models import Property, db


def get_current_property_id():
    """
    Get the active property_id from the Flask session.

    Returns:
        int: Property ID from session, or 1 (Sheraton Laval default) if not set.
    """
    return session.get('property_id', 1)


def get_current_property():
    """
    Get the active Property object.

    Returns:
        Property: The Property model instance, or None if not found.
    """
    pid = get_current_property_id()
    return Property.query.get(pid)


def set_current_property(property_id):
    """
    Set the active property in the Flask session.

    Args:
        property_id (int): The property ID to activate.
    """
    prop = Property.query.get(property_id)
    if prop and prop.is_active:
        session['property_id'] = property_id
        session['property_name'] = prop.name
        session['property_code'] = prop.code
        session['total_rooms'] = prop.total_rooms
        return True
    return False


def apply_property_filter(query, model):
    """
    Apply a property filter to a query if the model supports it.

    Filters records to show:
    - Records for the current property, OR
    - Records with NULL property_id (legacy single-property data)

    This ensures backward compatibility with existing data that has no property_id.

    Args:
        query: SQLAlchemy query object.
        model: The model class being queried.

    Returns:
        SQLAlchemy query object with property filter applied (if applicable).
    """
    if not hasattr(model, 'property_id'):
        return query

    try:
        pid = get_current_property_id()
        # Include records for current property OR records with NULL property_id (legacy)
        return query.filter(
            db.or_(
                model.property_id == pid,
                model.property_id.is_(None)
            )
        )
    except Exception:
        # If no session context, return unfiltered query
        return query


def get_property_total_rooms():
    """
    Get the total_rooms for the current property.

    Returns:
        int: Total rooms, or 252 (Sheraton Laval default) if not found.
    """
    return session.get('total_rooms', 252)
