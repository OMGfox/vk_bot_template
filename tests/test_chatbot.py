import unittest
from copy import deepcopy
from unittest.mock import patch, Mock, ANY
from datetime import time, datetime
import logging
from pony.orm import rollback
from vk_api.bot_longpoll import VkBotMessageEvent
from bot import VkBot, db_session
from flights import Dispatcher
import flights
from chatbot import handlers

logging.disable()


def isolate_db(test_func):
    def wrapper(*args, **kwargs):
        with db_session:
            test_func(*args, **kwargs)
            rollback()

    return wrapper


class BotTestCase(unittest.TestCase):
    RAW_EVENT = {'type': 'message_new',
                 'object': {'date': 1604225746, 'from_id': 620723211, 'id': 57, 'out': 0, 'peer_id': 620723211,
                            'text': '/help', 'conversation_message_id': 44, 'fwd_messages': [], 'important': False,
                            'random_id': 0, 'attachments': [], 'is_hidden': False},
                 'group_id': 199740511, 'event_id': 'ecb5f633e170b5093d53afcbf993526818c20903'}

    SETTINGS = Mock()
    SETTINGS.INTENTS = [
        {
            "name": "Help",
            "tokens": ("/help",),
            "scenario": None,
            "answer": "Отправьте боту сообщение:\n/ticket - чтобы оформить билет\n/help - для вывода этого сообщения."
        },
        {
            "name": "Booking a ticket",
            "tokens": ("/ticket",),
            "scenario": "booking_a_ticket",
            "answer": None
        }
    ]
    SETTINGS.SCENARIOS = {
        "booking_a_ticket": {
            "first_step": "step_1",
            "steps": {
                "step_1": {
                    "text": "Введите город отправления",
                    "failure_text": "Введенный вами город не найден. возможно вам подойдет один из следующего списка:"
                                    " {departure_cities}",
                    "handler": "handler_departure_city",
                    "next_step": "step_2"
                },
            }
        }
    }

    SETTINGS.DEFAULT_ANSWER = ("Отправьте боту сообщение:\n/ticket - чтобы оформить билет"
                               "\n/help - для вывода этого сообщения.")

    SETTINGS.DB_CONFIG = {
        "provider": 'sqlite',
        "filename": ':memory:'
    }

    def test_run(self):
        count = 5
        obj = {}
        events = [obj] * 5  # [obj, obj ...]
        long_poll_mock = Mock(return_value=events)
        long_poll_listen_mock = Mock()
        long_poll_listen_mock.listen = long_poll_mock

        with patch('bot.VkBot'):
            with patch('bot.VkBotLongPoll', return_value=long_poll_listen_mock):
                vk_bot = VkBot(' ', ' ', self.SETTINGS)
                vk_bot.on_event = Mock()
                vk_bot.run()
                vk_bot.on_event.assert_any_call(obj)
                self.assertEqual(count, vk_bot.on_event.call_count)

    def test_on_event_help(self):
        event = VkBotMessageEvent(raw=self.RAW_EVENT)
        with patch('bot.vk_api.VkApi'):
            with patch('bot.VkBotLongPoll'):
                bot = VkBot(' ', ' ', self.SETTINGS)
                bot.send_message = Mock()
                bot.on_event(event)
                text = 'Отправьте боту сообщение:\n/ticket - чтобы оформить билет\n/help - для вывода этого сообщения.'
                bot.send_message.assert_called_once_with(
                    peer_id=620723211,
                    message=text
                )

    @isolate_db
    def test_on_event_ticket(self):
        raw_event = deepcopy(self.RAW_EVENT)
        raw_event['object']['text'] = '/ticket'
        event = VkBotMessageEvent(raw=raw_event)
        with patch('bot.vk_api.VkApi'):
            with patch('bot.VkBotLongPoll'):
                bot = VkBot(' ', ' ', self.SETTINGS)
                bot.send_message = Mock()
                bot.on_event(event)
                text = 'Введите город отправления'
                bot.send_message.assert_called_once_with(
                    peer_id=620723211,
                    message=text
                )

    def test_on_event_ticket_start_scenario(self):
        raw_event = deepcopy(self.RAW_EVENT)
        raw_event['object']['text'] = '/ticket'
        event = VkBotMessageEvent(raw=raw_event)
        intent = {
            "name": "Booking a ticket",
            "tokens": ("/ticket",),
            "scenario": "booking_a_ticket",
            "answer": None
        }
        with patch('bot.vk_api.VkApi'):
            with patch('bot.VkBotLongPoll'):
                bot = VkBot(' ', ' ', self.SETTINGS)
                bot.send_message = Mock()
                bot._start_scenario = Mock()
                bot.on_event(event)
                bot._start_scenario.assert_called_once_with(intent, 620723211)

    def test_on_event_ticket_scenario_steps_handling(self):
        raw_event = deepcopy(self.RAW_EVENT)
        raw_event['object']['text'] = 'test'
        event = VkBotMessageEvent(raw=raw_event)
        with patch('bot.vk_api.VkApi'):
            with patch('bot.VkBotLongPoll'):
                bot = VkBot(' ', ' ', self.SETTINGS)
                bot.send_message = Mock()
                bot._scenario_steps_handling = Mock()
                bot.on_event(event)
                bot._scenario_steps_handling.assert_called_once_with(620723211, 'test')

    def test_send_message(self):
        send_mock = Mock()

        with patch('bot.vk_api.VkApi'):
            with patch('bot.VkBotLongPoll'):
                bot = VkBot(' ', ' ', self.SETTINGS)
                bot.vk = Mock()
                bot.vk.messages.send = send_mock

                text = self.RAW_EVENT['object']['text']
                peer_id = 620723211
                message = f'Я ЭхоБот, вот ваше сообщение: "{text}"'
                bot.send_message(peer_id=peer_id, message=message)

                send_mock.assert_called_once_with(
                    random_id=ANY,
                    peer_id=peer_id,
                    message=message
                )


class DispatcherTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.flights_db = [
            {
                "departure_city": "Москва",
                "destination_city": "Лондон",
                "weekly": (2, 4),
                "monthly": None,
                "date": None,
                "time": time(hour=18, minute=0)
            },
            {
                "departure_city": "Лондон",
                "destination_city": "Берлин",
                "weekly": None,
                "monthly": (5, 10, 20),
                "date": None,
                "time": time(hour=12, minute=10)
            },
            {
                "departure_city": "Стамбул",
                "destination_city": "Мадрид",
                "weekly": None,
                "monthly": None,
                "date": datetime(year=2020, month=11, day=20, hour=22, minute=30),
                "time": None
            },
        ]
        flights.flights_db = self.flights_db

    def test_get_departure_cities(self):
        result = sorted(Dispatcher.get_departure_cities())
        checker = ['Лондон', 'Москва', 'Стамбул']
        self.assertEqual(checker, result)

    def test_get_destination_cities(self):
        result = sorted(Dispatcher.get_destination_cities())
        checker = ['Берлин', 'Лондон', 'Мадрид']
        self.assertEqual(checker, result)

    def test_check_flight_exists_true(self):
        self.assertTrue(Dispatcher.check_flight_exists(departure_city='Москва', destination_city='Лондон'))

    def test_check_flight_exists_false(self):
        self.assertFalse(Dispatcher.check_flight_exists(departure_city='Москва', destination_city='Стамбул'))

    def test_get_closest_flights_date_number(self):
        checker = 1
        result = len(Dispatcher.get_closest_flights(departure_city='Стамбул',
                                                    destination_city='Мадрид',
                                                    flight_date='20-11-2020'))
        self.assertEqual(checker, result)

    def test_get_closest_flights_date_number_1(self):
        checker = 0
        result = len(Dispatcher.get_closest_flights(departure_city='Стамбул',
                                                    destination_city='Ливерпуль',
                                                    flight_date='20-11-2020'))
        self.assertEqual(checker, result)

    def test_get_closest_flights_date_results(self):
        checker = {
            "departure_city": "Стамбул",
            "destination_city": "Мадрид",
            "weekly": None,
            "monthly": None,
            'date': '20-11-2020 22:30',
            "time": None
        }
        result = Dispatcher.get_closest_flights(departure_city='Стамбул',
                                                destination_city='Мадрид',
                                                flight_date='20-11-2020')[0]
        self.assertEqual(checker, result)

    def test_get_closest_flights_weekly_number(self):
        checker = 2
        result = len(Dispatcher.get_closest_flights(departure_city='Москва',
                                                    destination_city='Лондон',
                                                    flight_date='18-11-2020'))
        self.assertEqual(checker, result)

    def test_get_closest_flights_weekly_results(self):
        checker = [
            {
                "departure_city": "Москва",
                "destination_city": "Лондон",
                "weekly": None,
                "monthly": None,
                'date': '18-11-2020 18:00',
                "time": None
            },
            {
                "departure_city": "Москва",
                "destination_city": "Лондон",
                "weekly": None,
                "monthly": None,
                'date': '20-11-2020 18:00',
                "time": None
            }]
        result = Dispatcher.get_closest_flights(departure_city='Москва',
                                                destination_city='Лондон',
                                                flight_date='18-11-2020')
        self.assertEqual(checker, result)

    def test_get_closest_flights_monthly_number(self):
        checker = 2
        result = len(Dispatcher.get_closest_flights(departure_city='Лондон',
                                                    destination_city='Берлин',
                                                    flight_date='05-11-2020'))
        self.assertEqual(checker, result)

    def test_get_closest_flights_monthly_number_1(self):
        checker = 1
        result = len(Dispatcher.get_closest_flights(departure_city='Лондон',
                                                    destination_city='Берлин',
                                                    flight_date='19-11-2020'))
        self.assertEqual(checker, result)

    def test_get_closest_flights_monthly_number_2(self):
        checker = 0
        result = len(Dispatcher.get_closest_flights(departure_city='Лондон',
                                                    destination_city='Берлин',
                                                    flight_date='21-11-2020'))
        self.assertEqual(checker, result)

    def test_get_closest_flights_monthly_result(self):
        checker = [
            {
                "departure_city": "Лондон",
                "destination_city": "Берлин",
                "weekly": None,
                "monthly": None,
                'date': '05-11-2020 12:10',
                "time": None
            },
            {
                "departure_city": "Лондон",
                "destination_city": "Берлин",
                "weekly": None,
                "monthly": None,
                'date': '10-11-2020 12:10',
                "time": None
            }
        ]
        result = Dispatcher.get_closest_flights(departure_city='Лондон',
                                                destination_city='Берлин',
                                                flight_date='05-11-2020')
        self.assertEqual(checker, result)


class HandlersTestCase(unittest.TestCase):
    def test_handler_departure_city_true(self):
        context = dict()
        text = "Лондон"
        available_cities = ['Лондон', 'Москва', 'Стамбул']
        Dispatcher.get_departure_cities = Mock(return_value=available_cities)
        result = handlers.handler_departure_city(text=text, context=context)
        self.assertEqual(text, context['departure_city'])
        self.assertTrue(result)

    def test_handler_departure_city_false(self):
        context = dict()
        text = "Париж"
        available_cities = ['Лондон', 'Москва', 'Стамбул']
        Dispatcher.get_departure_cities = Mock(return_value=['Лондон', 'Москва', 'Стамбул'])
        result = handlers.handler_departure_city(text=text, context=context)
        self.assertEqual(available_cities, context['departure_cities'])
        self.assertFalse(result)

    def test_handler_destination_city_true_exists(self):
        context = dict()
        context['departure_city'] = ''
        text = "Лондон"
        available_cities = ['Лондон', 'Москва', 'Стамбул']
        Dispatcher.get_destination_cities = Mock(return_value=available_cities)
        Dispatcher.check_flight_exists = Mock(return_value=True)
        result = handlers.handler_destination_city(text=text, context=context)
        self.assertEqual(text, context['destination_city'])
        self.assertTrue(result)

    def test_handler_destination_city_true_no_exists(self):
        context = dict()
        context['departure_city'] = ''
        text = "Лондон"
        available_cities = ['Лондон', 'Москва', 'Стамбул']
        Dispatcher.get_destination_cities = Mock(return_value=available_cities)
        Dispatcher.check_flight_exists = Mock(return_value=False)
        result = handlers.handler_destination_city(text=text, context=context)
        self.assertTrue(context['is_ended'])
        self.assertTrue(result)

    def test_handler_destination_city_false(self):
        context = dict()
        text = "Париж"
        available_cities = ['Лондон', 'Москва', 'Стамбул']
        Dispatcher.get_destination_cities = Mock(return_value=['Лондон', 'Москва', 'Стамбул'])
        result = handlers.handler_destination_city(text=text, context=context)
        self.assertEqual(available_cities, context['destination_cities'])
        self.assertFalse(result)

    def test_handler_date_true(self):
        context = dict()
        context['departure_city'] = ''
        context['destination_city'] = ''
        Dispatcher.get_closest_flights = Mock(return_value=[])
        text = '01-12-2020'
        result = handlers.handler_date(text=text, context=context)
        self.assertTrue(result)

    def test_handler_date_true_1(self):
        context = dict()
        context['departure_city'] = ''
        context['destination_city'] = ''
        Dispatcher.get_closest_flights = Mock(return_value=[])
        text = 'Дата:01-12-2020'
        result = handlers.handler_date(text=text, context=context)
        self.assertTrue(result)

    def test_handler_date_false(self):
        context = dict()
        context['departure_city'] = ''
        context['destination_city'] = ''
        Dispatcher.get_closest_flights = Mock(return_value=[])
        checker = '01-12-20'
        result = handlers.handler_date(text=checker, context=context)
        self.assertFalse(result)

    def test_handler_set_flight_true(self):
        context = dict()
        context['closest_flights'] = [
            {
                "departure_city": "Лондон",
                "destination_city": "Берлин",
                "weekly": None,
                "monthly": None,
                "date": datetime(year=2020, month=11, day=5, hour=12, minute=10),
                "time": None
            },
            {
                "departure_city": "Лондон",
                "destination_city": "Берлин",
                "weekly": None,
                "monthly": None,
                "date": datetime(year=2020, month=11, day=10, hour=12, minute=10),
                "time": None
            }
        ]
        checker = '1'
        result = handlers.handler_set_flight(text=checker, context=context)
        self.assertTrue(result)
        self.assertEqual(context['closest_flights'][0], context['selected_flight'])

    def test_handler_set_flight_true_1(self):
        context = dict()
        context['closest_flights'] = [
            {
                "departure_city": "Лондон",
                "destination_city": "Берлин",
                "weekly": None,
                "monthly": None,
                "date": datetime(year=2020, month=11, day=5, hour=12, minute=10),
                "time": None
            },
            {
                "departure_city": "Лондон",
                "destination_city": "Берлин",
                "weekly": None,
                "monthly": None,
                "date": datetime(year=2020, month=11, day=10, hour=12, minute=10),
                "time": None
            }
        ]
        checker = '2'
        result = handlers.handler_set_flight(text=checker, context=context)
        self.assertTrue(result)
        self.assertEqual(context['closest_flights'][1], context['selected_flight'])

    def test_handler_set_flight_false(self):
        context = dict()
        context['closest_flights'] = [
            {
                "departure_city": "Лондон",
                "destination_city": "Берлин",
                "weekly": None,
                "monthly": None,
                "date": datetime(year=2020, month=11, day=5, hour=12, minute=10),
                "time": None
            },
            {
                "departure_city": "Лондон",
                "destination_city": "Берлин",
                "weekly": None,
                "monthly": None,
                "date": datetime(year=2020, month=11, day=10, hour=12, minute=10),
                "time": None
            }
        ]
        checker = '0'
        result = handlers.handler_set_flight(text=checker, context=context)
        self.assertFalse(result)

    def test_handler_set_flight_false_1(self):
        context = dict()
        context['closest_flights'] = [
            {
                "departure_city": "Лондон",
                "destination_city": "Берлин",
                "weekly": None,
                "monthly": None,
                "date": datetime(year=2020, month=11, day=5, hour=12, minute=10),
                "time": None
            },
            {
                "departure_city": "Лондон",
                "destination_city": "Берлин",
                "weekly": None,
                "monthly": None,
                "date": datetime(year=2020, month=11, day=10, hour=12, minute=10),
                "time": None
            }
        ]
        checker = '3'
        result = handlers.handler_set_flight(text=checker, context=context)
        self.assertFalse(result)

    def test_handler_number_of_seats_true(self):
        context = dict()
        checker = [True, True, True, True, True]
        result = []
        for i in range(1, 6):
            result.append(handlers.handler_number_of_seats(text=str(i), context=context))
        self.assertEqual(checker, result)

    def test_handler_number_of_seats_false(self):
        context = dict()
        checker = [False, False, False]
        result = []
        for i in (0, 6, 7):
            result.append(handlers.handler_number_of_seats(text=str(i), context=context))
        self.assertEqual(checker, result)

    def test_handler_comment(self):
        context = dict()
        context["number_of_seats"] = 1
        context['selected_flight'] = {
            "departure_city": "Лондон",
            "destination_city": "Берлин",
            "weekly": None,
            "monthly": None,
            "date": datetime(year=2020, month=11, day=10, hour=12, minute=10),
            "time": None
        }
        text = 'something'
        selected_flight = context['selected_flight']
        checker = (f'Откуда: {selected_flight["departure_city"]}\n'
                   f'Куда: {selected_flight["destination_city"]}\n'
                   f'Дата вылета: {selected_flight["date"]}\n'
                   f'Количество мест: {context["number_of_seats"]}\n'
                   f'Комментарий: {text}')
        result = handlers.handler_comment(text=text, context=context)
        self.assertTrue(result)
        self.assertTrue(context['comment'])
        self.assertEqual(checker, context['checked_data'])

    def test_handler_check_data_true_yes(self):
        checker = 'да'
        result = handlers.handler_check_data(checker, '')
        self.assertTrue(result)

    def test_handler_check_data_true_no(self):
        context = dict()
        checker = 'нет'
        result = handlers.handler_check_data(checker, context)
        self.assertTrue(result)
        self.assertTrue(context['is_ended'])

    def test_handler_check_data_false(self):
        context = dict()
        checker = 'something_wrong'
        result = handlers.handler_check_data(checker, context)
        self.assertFalse(result)

    def test_handler_telephone_number_true(self):
        context = dict()
        checker = '+7(911)123-45-67'
        result = handlers.handler_telephone_number(text=checker, context=context)
        self.assertTrue(result)
        self.assertEqual(checker, context['telephone_number'])

    def test_handler_telephone_number_true_1(self):
        context = dict()
        checker = '+7 911 123-45-67'
        result = handlers.handler_telephone_number(text=checker, context=context)
        self.assertTrue(result)
        self.assertEqual(checker, context['telephone_number'])

    def test_handler_telephone_number_true_2(self):
        context = dict()
        checker = '(911) 123-45-67'
        result = handlers.handler_telephone_number(text=checker, context=context)
        self.assertTrue(result)
        self.assertEqual(checker, context['telephone_number'])

    def test_handler_telephone_number_true_3(self):
        context = dict()
        checker = '123-45-67'
        result = handlers.handler_telephone_number(text=checker, context=context)
        self.assertTrue(result)
        self.assertEqual(checker, context['telephone_number'])

    def test_handler_telephone_number_true_4(self):
        context = dict()
        checker = '1234567'
        result = handlers.handler_telephone_number(text=checker, context=context)
        self.assertTrue(result)
        self.assertEqual(checker, context['telephone_number'])

    def test_handler_telephone_number_true_5(self):
        context = dict()
        checker = '123 45 67'
        result = handlers.handler_telephone_number(text=checker, context=context)
        self.assertTrue(result)
        self.assertEqual(checker, context['telephone_number'])

    def test_handler_telephone_number_false(self):
        context = dict()
        checker = 'asdfasd'
        result = handlers.handler_telephone_number(text=checker, context=context)
        self.assertFalse(result)
