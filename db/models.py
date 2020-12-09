from pony.orm import Database, Required, PrimaryKey, Json, BindingError
import logging.config
from logs.logging_config import log_config

logging.config.dictConfig(log_config)
stream_logger = logging.getLogger('stream_logger')
file_logger = logging.getLogger('file_logger')

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


def init(db_config):
    try:
        db.bind(**db_config)
        db.generate_mapping(create_tables=True)
    except BindingError:
        stream_logger.exception("Exception while binding of database.")
        file_logger.exception("Exception while binding of database.")
