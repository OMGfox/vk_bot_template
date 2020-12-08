import re
from copy import deepcopy

from flights import Dispatcher
from generate_ticket import generate_ticket

"""
Handler - the function that take text (text of the message) as input and context (dict), and return bool:
True if step is pass, False - if a data input is not correct
"""

CONSONANTS = ('а', 'у', 'о', 'ы', 'и', 'э', 'я', 'ю', 'ё', 'е')


def handler_departure_city(text, context) -> bool:
    result = False
    for city in Dispatcher.get_departure_cities():
        departure_city = deepcopy(city)
        if city[-1] in CONSONANTS:
            city = city[:-1] + r'[а-я]?'
        if re.search(city.lower(), text.lower()):
            context['departure_city'] = departure_city
            result = True
    if not result:
        context['departure_cities'] = Dispatcher.get_departure_cities()
    return result


def handler_destination_city(text, context) -> bool:
    result = False
    for city in Dispatcher.get_destination_cities():
        destination_city = deepcopy(city)
        if city[-1] in CONSONANTS:
            city = city[:-1] + r'[а-я]?'
        if re.search(city.lower(), text.lower()):
            context['destination_city'] = destination_city
            flight_is_exists = Dispatcher.check_flight_exists(context['departure_city'], context['destination_city'])
            if not flight_is_exists:
                context['is_ended'] = True
            result = True
            break
    else:
        context['destination_cities'] = Dispatcher.get_destination_cities()

    return result


def handler_date(text, context) -> bool:
    result = False
    re_date = re.compile(r'\d+-\d+-\d{4}')
    date = re_date.findall(text)
    if date:
        context['date'] = date[0]
        closest_flights = Dispatcher.get_closest_flights(departure_city=context['departure_city'],
                                                         destination_city=context['destination_city'],
                                                         flight_date=context['date'])
        context['closest_flights'] = closest_flights
        flights_variants = ''
        for index, flight in enumerate(closest_flights):
            flights_variants += (f"{index + 1}: {flight['departure_city']} --> "
                                 f"{flight['destination_city']}, "
                                 f"дата: {flight['date']}\n")
        context['flights_variants'] = flights_variants
        if not context['closest_flights']:
            context['is_ended'] = True
        result = True
    return result


def handler_set_flight(text, context) -> bool:
    result = False
    max_element = len(context['closest_flights'])
    if text.isdigit() and int(text) in range(1, max_element + 1):
        index = int(text) - 1
        context['selected_flight'] = context['closest_flights'][index]
        result = True
    return result


def handler_number_of_seats(text, context) -> bool:
    if text.isdigit() and int(text) in range(1, 6):
        context['number_of_seats'] = text
        return True
    return False


def handler_comment(text, context) -> bool:
    context['comment'] = text
    selected_flight = context["selected_flight"]
    checked_data = (f'Откуда: {selected_flight["departure_city"]}\n' 
                    f'Куда: {selected_flight["destination_city"]}\n'
                    f'Дата вылета: {selected_flight["date"]}\n'
                    f'Количество мест: {context["number_of_seats"]}\n'
                    f'Комментарий: {context["comment"]}')
    context['checked_data'] = checked_data
    return True


def handler_check_data(text, context) -> bool:
    if re.search(r'\bда\b', text.lower()):
        return True
    elif re.search(r'\bнет\b', text.lower()):
        context['is_ended'] = True
        return True
    return False


def handler_telephone_number(text, context) -> bool:
    re_telephone_number = re.compile(r"([+]*[(]{0,1}[0-9]{1,4}[)]{0,1}[-\s\./0-9]*)")
    telephone_number = ''.join(re_telephone_number.findall(text))
    if telephone_number:
        context['telephone_number'] = telephone_number
        return True
    return False


def generate_ticket_handler(text, context):
    return generate_ticket(departure_city=context['departure_city'],
                           destination_city=context['destination_city'],
                           date=context['selected_flight']['date'],
                           seats=context['number_of_seats'])

