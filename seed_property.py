#!/usr/bin/env python3
"""
Seed the default Sheraton Laval property for backward compatibility.

Run this script once to initialize the properties table with the default
Sheraton Laval property. Existing multi-property data will reference this ID.

Usage:
    python seed_property.py
"""

from main import create_app
from database.models import db, Property

app = create_app()

with app.app_context():
    # Check if default property already exists
    existing = Property.query.filter_by(code='SHRLVL').first()

    if existing:
        print(f"✓ Default property already exists: {existing.name} (ID: {existing.id})")
    else:
        # Create the default Sheraton Laval property
        prop = Property(
            code='SHRLVL',
            name='Sheraton Laval',
            brand='Marriott',
            total_rooms=252,
            address='2440 Autoroute des Laurentides',
            city='Laval',
            province='Québec',
            country='Canada',
            timezone='America/Montreal',
            currency='CAD',
            pms_type='Galaxy Lightspeed',
            pms_property_id='',
            is_active=True,
        )
        db.session.add(prop)
        db.session.commit()

        print(f"✓ Created default property: {prop.name}")
        print(f"  - ID: {prop.id}")
        print(f"  - Code: {prop.code}")
        print(f"  - Rooms: {prop.total_rooms}")
        print(f"  - Location: {prop.city}, {prop.province}")

print("\nSeed complete. Multi-property support is enabled.")
