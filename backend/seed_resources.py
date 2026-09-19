from database.mongodb import db
resources = [
    {
        "_id": "BC1",
        "name": "Badminton Court 1",
        "type": "badminton",
        "capacity": 4,
        "hourly_rate": 300,
        "open_time": "06:00",
        "close_time": "22:00",
        "active": True
    },

    {
        "_id": "BC2",
        "name": "Badminton Court 2",
        "type": "badminton",
        "capacity": 4,
        "hourly_rate": 300,
        "open_time": "06:00",
        "close_time": "22:00",
        "active": True
    },

    {
        "_id": "FT1",
        "name": "Football Turf 1",
        "type": "football",
        "capacity": 14,
        "hourly_rate": 1200,
        "open_time": "06:00",
        "close_time": "22:00",
        "active": True
    },

    {
        "_id": "TC1",
        "name": "Tennis Court 1",
        "type": "tennis",
        "capacity": 4,
        "hourly_rate": 500,
        "open_time": "06:00",
        "close_time": "22:00",
        "active": True
    },

    {
        "_id": "MR1",
        "name": "Multipurpose Room 1",
        "type": "multipurpose",
        "capacity": 20,
        "hourly_rate": 800,
        "open_time": "06:00",
        "close_time": "22:00",
        "active": True
    }
]


db.resources.insert_many(resources)

print("All resources inserted successfully")