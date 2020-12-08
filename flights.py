"""
weekly = (tuple of days_of_week, where days_of_week are numbers from 0 to 6)
monthly = (tuple of days_of_month, where days_of_month are numbers from 1 to 31)
date = (if weekly and monthly are None then date is using, date type is datetime.date)
time = time of flight. The type is datetime.time
"""
from copy import deepcopy
from datetime import time, datetime, timedelta


class Dispatcher:
    """
    class to emulate the air traffic controller api
    """
    @staticmethod
    def get_departure_cities():
        """
        return the set of the available departure cities
        @return: list
        """
        return list(set(flight['departure_city'] for flight in flights_db))

    @staticmethod
    def get_destination_cities():
        """
        return the set of the available destination cities
        @return: list
        """
        return list(set(flight['destination_city'] for flight in flights_db))

    @staticmethod
    def check_flight_exists(departure_city: str, destination_city: str) -> bool:
        """
        check if flight from the departure city to the destination city
        @param departure_city: name of departure city, type is str
        @param destination_city: name of the destination city, type is str
        @return: bool
        """
        is_exists = False
        for flight in flights_db:
            is_exists = all([flight['departure_city'] == departure_city,
                             flight['destination_city'] == destination_city])
            if is_exists:
                break
        return is_exists

    @staticmethod
    def get_closest_flights(departure_city: str, destination_city: str, flight_date: str) -> list:
        """
        The method to find and return the list of the available closest flights
        @param departure_city:
        @param destination_city:
        @param flight_date: date
        @return: list of flights
        """
        for_number_days = 5  # на ближайшие 5 дней
        closest_flights = list()
        for flight in flights_db:
            flights = Dispatcher._fit_flight(flight, flight_date, for_number_days)
            is_fit = all((flight['departure_city'] == departure_city,
                          flight['destination_city'] == destination_city,
                          flights))
            if is_fit:
                closest_flights.extend(flights)
        return closest_flights

    @staticmethod
    def _fit_flight(flight: dict, flight_date: str, for_number_days: int) -> list:
        """
        extends method get_closest_flights
        @param flight:
        @param flight_date:
        @param for_number_days:
        @return:
        """
        closest_flights = list()
        flight_date = datetime.strptime(flight_date, format('%d-%m-%Y'))
        range_sequence = range(0, for_number_days + 1)
        if flight['weekly']:
            for i in range_sequence:
                tested_date = flight_date + timedelta(days=i)
                if tested_date.weekday() in flight['weekly']:
                    fit_flight = deepcopy(flight)
                    fit_flight['weekly'] = None
                    flight_time = fit_flight['time']
                    fit_flight['date'] = tested_date.replace(hour=flight_time.hour, minute=flight_time.minute)
                    fit_flight['time'] = None
                    fit_flight['date'] = fit_flight['date'].strftime('%d-%m-%Y %H:%M')
                    closest_flights.append(fit_flight)
        if flight['monthly']:
            for i in range_sequence:
                tested_date = flight_date + timedelta(days=i)
                if tested_date.day in flight['monthly']:
                    fit_flight = deepcopy(flight)
                    fit_flight['monthly'] = None
                    flight_time = fit_flight['time']
                    fit_flight['date'] = tested_date.replace(hour=flight_time.hour, minute=flight_time.minute)
                    fit_flight['time'] = None
                    fit_flight['date'] = fit_flight['date'].strftime('%d-%m-%Y %H:%M')
                    closest_flights.append(fit_flight)

        if flight['date']:
            for i in range_sequence:
                tested_date = flight_date + timedelta(days=i)
                if tested_date.strftime('%d-%m-%Y') == flight['date'].strftime('%d-%m-%Y'):
                    fit_flight = deepcopy(flight)
                    fit_flight['date'] = fit_flight['date'].strftime('%d-%m-%Y %H:%M')
                    closest_flights.append(fit_flight)
                    break
        return closest_flights


flights_db = [
    {
        "departure_city": "Москва",
        "destination_city": "Лондон",
        "weekly": (2, 4),
        "monthly": None,
        "date": None,
        "time": time(hour=18, minute=0)
    },
    {
        "departure_city": "Москва",
        "destination_city": "Стамбул",
        "weekly": None,
        "monthly": (10, 20),
        "date": None,
        "time": time(hour=22, minute=30)

    },
    {
        "departure_city": "Москва",
        "destination_city": "Берлин",
        "weekly": (1, 3),
        "monthly": None,
        "date": None,
        "time": time(hour=13, minute=30)
    },
    {
        "departure_city": "Лондон",
        "destination_city": "Москва",
        "weekly": (3, 5),
        "monthly": None,
        "date": None,
        "time": time(hour=6, minute=00)
    },
    {
        "departure_city": "Лондон",
        "destination_city": "Берлин",
        "weekly": (2, 5),
        "monthly": None,
        "date": None,
        "time": time(hour=12, minute=10)
    },
    {
        "departure_city": "Лондон",
        "destination_city": "Киев",
        "weekly": None,
        "monthly": None,
        "date": datetime(year=2020, month=11, day=19, hour=10, minute=0),
        "time": None
    },
    {
        "departure_city": "Стамбул",
        "destination_city": "Берлин",
        "weekly": None,
        "monthly": (5, 10, 15, 20),
        "date": None,
        "time": time(hour=22, minute=0)
    },
    {
        "departure_city": "Стамбул",
        "destination_city": "Мадрид",
        "weekly": (0, 2, 4, 6),
        "monthly": None,
        "date": None,
        "time": time(hour=23, minute=50)
    },
    {
        "departure_city": "Стамбул",
        "destination_city": "Рим",
        "weekly": (2, 4, 6),
        "monthly": None,
        "date": None,
        "time": time(hour=22, minute=10)
    },
    {
        "departure_city": "Берлин",
        "destination_city": "Москва",
        "weekly": (2, 4),
        "monthly": None,
        "date": None,
        "time": time(hour=12, minute=10)
    },
    {
        "departure_city": "Берлин",
        "destination_city": "Лондон",
        "weekly": (3, 6),
        "monthly": None,
        "date": None,
        "time": time(hour=12, minute=10)
    },
    {
        "departure_city": "Берлин",
        "destination_city": "Стамбул",
        "weekly": None,
        "monthly": (7, 12, 17, 22),
        "date": None,
        "time": time(hour=22, minute=10)
    },
    {
        "departure_city": "Мадрид",
        "destination_city": "Киев",
        "weekly": None,
        "monthly": None,
        "date": datetime(year=2020, month=11, day=25, hour=22, minute=30),
        "time": None
    },
    {
        "departure_city": "Мадрид",
        "destination_city": "Стамбул",
        "weekly": (2, 4, 6),
        "monthly": None,
        "date": None,
        "time": time(hour=20, minute=45)
    },
    {
        "departure_city": "Мадрид",
        "destination_city": "Минск",
        "weekly": None,
        "monthly": (5, 25),
        "date": None,
        "time": time(hour=21, minute=30)
    },
    {
        "departure_city": "Киев",
        "destination_city": "Минск",
        "weekly": (0, 2, 4, 6),
        "monthly": None,
        "date": None,
        "time": time(hour=22, minute=30)
    },
    {
        "departure_city": "Киев",
        "destination_city": "Лондон",
        "weekly": None,
        "monthly": (3, 5),
        "date": None,
        "time": time(hour=9, minute=30)
    },
    {
        "departure_city": "Киев",
        "destination_city": "Рим",
        "weekly": None,
        "monthly": (10,),
        "date": None,
        "time": time(hour=20, minute=00)
    },
    {
        "departure_city": "Рим",
        "destination_city": "Стамбул",
        "weekly": (3,),
        "monthly": None,
        "date": None,
        "time": time(hour=23, minute=30)
    },
    {
        "departure_city": "Рим",
        "destination_city": "Киев",
        "weekly": None,
        "monthly": (15,),
        "date": None,
        "time": time(hour=12, minute=30)
    },
    {
        "departure_city": "Рим",
        "destination_city": "Минск",
        "weekly": None,
        "monthly": (5, 10, 20),
        "date": None,
        "time": time(hour=21, minute=30)
    },
]

if __name__ == '__main__':
    print(Dispatcher.get_departure_cities())
    print(Dispatcher.get_destination_cities())
