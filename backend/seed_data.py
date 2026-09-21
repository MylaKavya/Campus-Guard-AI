# seed_data.py – Run once to pre-populate sample data for demos
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from app import app, db, ItemReport, run_matching

SAMPLES = [
    dict(report_type="lost", item_name="Black iPhone 14 Pro",
         category="phone", description="Black iPhone 14 Pro with a cracked back glass, blue case. Phone has a SpongeBob sticker.",
         location="Main Library, 2nd Floor", date_time="2024-11-20T14:30", contact="alice@campus.edu"),

    dict(report_type="found", item_name="iPhone found near library",
         category="phone", description="Found a black iPhone with a cracked back near the library entrance. Has a cartoon sticker.",
         location="Main Library, Ground Floor", date_time="2024-11-20T15:00", contact="bob@campus.edu"),

    dict(report_type="lost", item_name="Silver MacBook Pro 13\"",
         category="laptop", description="Silver MacBook Pro 2022 with a terminal sticker on the lid. Charger also missing.",
         location="Computer Science Block, Lab 3", date_time="2024-11-21T10:00", contact="charlie@campus.edu"),

    dict(report_type="found", item_name="Laptop bag with MacBook",
         category="laptop", description="Found a silver MacBook Pro with stickers in CS block. Handed in to reception.",
         location="CS Block Reception", date_time="2024-11-21T11:30"),

    dict(report_type="lost", item_name="Blue Jansport Backpack",
         category="bag", description="Medium blue Jansport backpack containing textbooks, a red pencil case, and a calculator.",
         location="Cafeteria, Table near window", date_time="2024-11-22T13:15", contact="diana@campus.edu"),

    dict(report_type="found", item_name="Keys with a car remote",
         category="keys", description="Found a set of car keys with a Honda remote and a university lanyard attached.",
         location="Parking Lot B", date_time="2024-11-22T16:00", contact="security@campus.edu"),

    dict(report_type="lost", item_name="Student ID Card",
         category="id card", description="University student ID card for Emma Wilson, student number 20210456.",
         location="Sports Complex, Gym", date_time="2024-11-23T09:45", contact="emma@campus.edu"),

    dict(report_type="found", item_name="Prescription Glasses",
         category="glasses", description="Found round black-framed prescription glasses in a grey soft case.",
         location="Science Block, Lecture Hall 2", date_time="2024-11-23T14:00"),
]

with app.app_context():
    db.create_all()
    for s in SAMPLES:
        item = ItemReport(**s)
        db.session.add(item)
    db.session.commit()
    # Run matching for all items
    for item in ItemReport.query.all():
        run_matching(item)
    print(f"✅ Seeded {len(SAMPLES)} items. Check /api/matches to see AI pairs!")
