import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id
from vk_api.exceptions import ApiError
from config import comunity_token, access_token
from core import VkTools

import json

from data_store import add_user, check_user

def save_database(database):
    with open('database.json', 'w') as file:
        json.dump(database, file)

def load_database():
    with open('database.json', 'r') as file:
        database = json.load(file)
    return database

class BotInterface():
    def init(self, comunity_token, access_token):
        self.vk = vk_api.VkApi(token=comunity_token)
        self.db = vk_api.VkApi(token=access_token).get_api().database
        self.longpoll = VkLongPoll(self.vk)
        self.vktools = VkTools(access_token)
        self.params = {}
        self.worksheet = []
        self.offset = 0
        self.database = load_database()
        self.sex_request = False
        self.city_request = False
        self.age_request = False
        try:
            self.user_id = self.vktools.api.method('users.get')[0]['id']
        except ApiError as e:
            self.user_id = None
            info = {}
            print(f'error = {e}')

    def messagesend(self, userid, message, attachment=None):
        self.vk.method('messages.send', 
                       {'user_id': userid,
                        'message': message,
                        'attachment': attachment,
                        'random_id': get_random_id()}
                       )

    def event_handler(self):
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                self.response(event)
                    
        save_database(self.database)
        
    def back_to_search(self,event):
        event.text = 'поиск'
        self.response(event)
        
    def response(self, event):
        if event.text.lower() == 'пока':
            self.messagesend(
                event.user_id, 'До новых встреч.')
        elif self.sex_request:
            if event.text.lower() == 'ж':
                self.params['sex'] = 1
            elif event.text.lower() == 'м':
                self.params['sex'] = 2
            else:
                self.messagesend(
                event.user_id, 
                f'Пол введён неверно. Попробуйте снова.')
            self.sex_request = False
            self.back_to_search(event)
            
        elif self.city_request:
            cities = self.db.getCities(
                q = event.text, need_all=1, count=1000)['items']
            find_city = list(filter(
                lambda x: x['title'].lower() == event.text.lower(), cities))
            if find_city != []:
                self.params['city'] = event.text
                self.city_request = False
            else:
                self.messagesend(
                event.user_id, 
                f'Город введён неверно. Попробуйте снова.')
            self.back_to_search(event)
        elif self.age_request:
            if event.text.isdigit():
                age = int(event.text)
                if 0 < age < 200:
                    self.params['age'] = age
                    self.age_request = False
                    self.back_to_search(event)
                else:
                    self.messagesend(
                event.user_id, 
                f'Возраст введён неверно. Попробуйте снова.')
            else:
                self.messagesend(
                event.user_id, 
                f'Возраст введён неверно. Попробуйте снова.')
            
        elif event.text.lower() == 'привет':
                    '''Логика для получения данных о пользователе'''
                    self.params = self.vktools.get_profile_info(event.user_id)
                    self.messagesend(
                        event.user_id, f'Привет, друг, {self.params["name"]}')
        elif event.text.lower() == 'поиск':
            '''Валидация данных пользователя'''
            if self.params['sex'] == 0:
                self.messagesend(
                    event.user_id, f'Укажите ваш пол (м/ж)')
                self.sex_request = True
            elif (self.params['city'] is None or 
                    self.params['city'] == ''):
                self.messagesend(
                    event.user_id, f'Укажите ваш город')
                self.city_request = True
            elif self.params['age'] is None:
                self.messagesend(
                    event.user_id, f'Укажите ваш возраст')
                self.age_request = True
            else:
                '''Логика для поиска анкет'''
                self.messagesend(
                    event.user_id, 'Начинаем поиск')
                if self.worksheet:
                    worksheet = self.worksheets.pop()
                    print('user_id',self.user_id, 'worksheet_id:',worksheet['id'])
                    while check_user(profile_id=self.user_id, worksheet_id=worksheet['id']):
                        worksheet = self.worksheets.pop()
                    photos = self.vktools.get_photos(worksheet['id'])
                    photo_string = ''
                    for photo in photos:
                        photo_string += f'photo{photo["owner_id"]}_{photo["id"]},'
                else:
                    self.worksheets = self.vktools.search_worksheet(
                        self.params,self.offset)
                    worksheet = self.worksheets.pop()
                    print('user_id',self.user_id, 'worksheet_id:',worksheet['id'])
                    while check_user(profile_id=self.user_id, worksheet_id=worksheet['id']):
                        worksheet = self.worksheets.pop()
                    'проверка анкеты в бд в соответствии с event.user_id'
                    photos = self.vktools.get_photos(worksheet['id'])
                    photo_string = ''
                    for photo in photos:
                        photo_string += f'photo{photo["owner_id"]}_{photo["id"]},'
                    self.offset += 10 
                
                self.messagesend(
                    event.user_id, 
                    f'имя: {worksheet["name"]} ссылка: vk.com/{worksheet["id"]}',
                    attachment=photo_string
                    )
                add_user(self.user_id, worksheet['id'])
                'добавить анкету в бд в соответствии с event.user_id'
                self.database[event.user_id] = worksheet
        else:
            self.messagesend(
                event.user_id, 'Неизвестная команда')
                    
                    
if __name__ == '__main__':
    bot_interface = BotInterface()
    bot_interface.init(comunity_token, access_token) 
    bot_interface.event_handler()