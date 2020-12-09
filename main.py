from bot import VkBot
import settings

try:
    import settings
except ImportError:
    exit('You have to create a settings.py file from the template and set GROUP_ID and TOKEN inside it')


if __name__ == '__main__':
    vk_bot = VkBot(settings=settings, token=settings.TOKEN, group_id=settings.GROUP_ID)
    try:
        vk_bot.run()
    except KeyboardInterrupt:
        exit('Goodbye, boss')
