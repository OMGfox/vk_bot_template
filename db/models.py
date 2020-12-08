from pony.orm import Database, Required, PrimaryKey, Json, db_session
from settings import DB_CONFIG

db = Database()


class UserState(db.Entity):
    """
    user state in scenario
    """
    user_id = PrimaryKey(int)
    scenario_name = Required(str)
    step_name = Required(str)
    context = Required(Json)


class TicketOrder(db.Entity):
    """
    completed orders
    """
    user_id = Required(int)
    departure_city = Required(str)
    destination_city = Required(str)
    date = Required(str)
    seats = Required(int)
    comment = Required(str)
    telephone_number = Required(str)


db.bind(**DB_CONFIG)
db.generate_mapping(create_tables=True)
