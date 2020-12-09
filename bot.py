import random
from random import randint

import requests
from pony.orm import ObjectNotFound, db_session
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType, VkBotEvent
import vk_api
import handlers
from db.models import *

logging.config.dictConfig(log_config)
stream_logger = logging.getLogger('stream_logger')
file_logger = logging.getLogger('file_logger')


class VkBot:
    """
        vk bot with a mystery functionality
    """

    def __init__(self, token, group_id, settings):
        init(settings.DB_CONFIG)
        self.settings = settings
        self.token = token
        self.group_id = group_id
        self.vk_session = vk_api.VkApi(token=self.token)
        self.vk = self.vk_session.get_api()
        self.long_poll_bot = VkBotLongPoll(vk=self.vk_session, group_id=self.group_id)

    def send_message(self, peer_id, message: str):
        """
        The method to send a message
        @param peer_id: receiver id
        @param message: text of your message
        @return: None
        """
        random_id = randint(2 ** 8, 2 ** 31)
        self.vk.messages.send(random_id=random_id, peer_id=peer_id, message=message)
        stream_logger.info(f'The new message returned to the sender with ID: {peer_id}')
        file_logger.info(f'The new message returned to the sender with ID: {peer_id}')

    def send_image(self, image, user_id):
        upload_url = self.vk.photos.getMessagesUploadServer()['upload_url']
        upload_data = requests.post(upload_url, files={'photo': ('image.png', image, 'image/png')}).json()
        image_data = self.vk.photos.saveMessagesPhoto(**upload_data)
        owner_id = image_data[0]['owner_id']
        media_id = image_data[0]['id']
        attachment_id = f"photo{owner_id}_{media_id}"
        self.vk.messages.send(random_id=random.randint(0, 2 ** 20),
                              peer_id=user_id,
                              attachment=attachment_id)

    def send_step(self, step, user_id, text, context):
        if "text" in step:
            self.send_message(peer_id=user_id, message=text)
        if "image" in step:
            handler = getattr(handlers, step['image'])
            image = handler(text, context)
            self.send_image(image, user_id)

    def run(self):
        """
        Running of the bot
        @return: None
        """
        for event in self.long_poll_bot.listen():
            file_logger.debug(msg=f'The new event received')
            try:
                self.on_event(event)
            except Exception:
                stream_logger.exception(msg='Exception while event processing')
                file_logger.exception(msg='Exception while event processing')

    @db_session
    def on_event(self, event: VkBotEvent):
        """
        The method to handle events
        @param event: VkBotEventType.MESSAGE_NEW
        @return: None
        """
        if event.type == VkBotEventType.MESSAGE_NEW:
            peer_id = event.obj.from_id
            text = event.obj.text
            stream_logger.info(msg=f'MESSAGE_NEW from: {peer_id} with text: "{text}"')
            file_logger.info(msg=f'MESSAGE_NEW from: {peer_id} with text: "{text}"')

            for intent in self.settings.INTENTS:
                if any(token in text for token in intent['tokens']):
                    if intent['answer']:
                        self.send_message(peer_id=peer_id, message=intent['answer'])
                    else:
                        self._start_scenario(intent, peer_id)
                    break
            else:
                try:
                    self._scenario_steps_handling(peer_id, text)
                except ObjectNotFound:
                    self.send_message(peer_id=peer_id, message=self.settings.DEFAULT_ANSWER)
        else:
            file_logger.debug(msg=f"New event with type: {event.type} ignored")

    def _start_scenario(self, intent, peer_id):
        """
        The method to start scenario and to send the first step answer to user
        @param intent: is dict with a scenario name, tokens or an answer
        @param peer_id: user id
        @return: None
        """
        scenario_name = intent['scenario']
        stream_logger.info(msg=f'new scenario started for user {peer_id}, name {scenario_name}"')
        file_logger.info(msg=f'new scenario started for user {peer_id}, name {scenario_name}"')
        first_step = self.settings.SCENARIOS[scenario_name]['first_step']
        try:
            state = UserState[peer_id]
            state.set(scenario_name=scenario_name, step_name=first_step, context=dict())
        except ObjectNotFound:
            UserState(user_id=peer_id, scenario_name=scenario_name, step_name=first_step, context=dict())
        answer = self.settings.SCENARIOS[scenario_name]['steps'][first_step]['text']
        step = self.settings.SCENARIOS[scenario_name]['steps'][first_step]
        self.send_step(step=step, user_id=peer_id, text=answer, context={})

    def _scenario_steps_handling(self, peer_id, text):
        """
        The method to handling the started scenario
        @param peer_id: user id
        @param text: a message of the user
        @return: None
        """
        state = UserState[peer_id]
        scenario_name = state.scenario_name
        step_name = state.step_name
        handler_name = self.settings.SCENARIOS[scenario_name]['steps'][step_name]['handler']
        handler = getattr(handlers, handler_name)
        if handler(text=text, context=state.context):
            next_step = self.settings.SCENARIOS[scenario_name]['steps'][step_name]['next_step']
            if self._is_current_user_session_ended(state.context):
                self.send_message(peer_id=peer_id,
                                  message="По вашему запросу не найдено ни одного рейса. Либо сценарий завершен "
                                          "пользователем")
                state.delete()
                return
            answer = self.settings.SCENARIOS[scenario_name]['steps'][next_step]['text']
            state.step_name = next_step
            step = self.settings.SCENARIOS[scenario_name]['steps'][next_step]
            self.send_step(step=step, user_id=peer_id, text=answer.format(**state.context), context=state.context)

            if self._is_last_scenario_step(scenario_name, next_step):
                TicketOrder(user_id=peer_id,
                            departure_city=state.context["departure_city"],
                            destination_city=state.context["destination_city"],
                            date=state.context["selected_flight"]["date"],
                            seats=state.context["number_of_seats"],
                            comment=state.context["comment"],
                            telephone_number=state.context["telephone_number"])
                state.delete()
        else:
            answer = self.settings.SCENARIOS[scenario_name]['steps'][step_name]['failure_text']
            if answer:
                self.send_message(peer_id, answer.format(**state.context))

    def _is_last_scenario_step(self, scenario_name, next_step):
        """
        The method to check if the last scenario step exists
        @param scenario_name: str
        @param next_step: str
        @return: bool
        """
        has_next_step = bool(self.settings.SCENARIOS[scenario_name]['steps'][next_step]['next_step'])
        has_failure_text = bool(self.settings.SCENARIOS[scenario_name]['steps'][next_step]['failure_text'])
        if not has_next_step and not has_failure_text:
            return True
        return False

    def _is_current_user_session_ended(self, context):
        """
        The method to check if the current user scenario is ended
        @param context:
        @return: None
        """
        return context.get('is_ended', False)
