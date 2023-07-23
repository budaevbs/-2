from pprint import pprint
from datetime import datetime

import vk_api
from vk_api.exceptions import ApiError
from config import access_token


class VkTools:
    def __init__(self, access_token):
        self.api = vk_api.VkApi(token=access_token)

    def _bdate_toyear(self, bdate):
        user_years = bdate.split('.')[2]
        now = datetime.now().year
        return now - int(user_years) if bdate else None
    
    def get_profile_info(self, user_id):
        try:
            info, = self.api.method('users.get', {
                'user_id': user_id,
                'fields': 'city, bdate, sex, relation'
            })
        except ApiError as e:
            info = {}
            print(f'error = {e}')

        result = {'name': info['first_name'] + ' ' + info['last_name'] if
                  'first_name' in info and 'last_name' in info else None,
                  'sex': info.get('sex'),
                  'city': info.get('city')['title'] if info.get('city') is not None else None,
                  'age': self._bdate_toyear(info.get('bdate'))
                  }
        return result

    def search_users(self, params, city_id, sex):
        sex = 1 if params['sex'] == 2 else 2
        params = self.get_profile_info(789657038)
        city = params.get('city')
        city_id = city['id'] if city and 'id' in city else None
        city_id = params['city_id']

        current_year = datetime.now().year
        user_year = int(params['bdate'].split('.')[2])
        age = current_year - user_year
        age_from = age - 5
        age_to = age + 5

        users = self.api.method('users.search', {
            'count': 10,
            'offset': 0,
            'age_from': age_from,
            'age_to': age_to,
            'sex': sex,
            'city': city_id,
            'status': 6,
            'is_closed': False
        })

        try:
            users = users['items']
        except KeyError:
            return []

        res = []
        for user in users:
            if not user['is_closed']:
                res.append({'id': user['id'], 'name': user['first_name'] + ' ' + user['last_name']})

        return res

    def get_photos(self, user_id):
        photos = self.api.method('photos.get', {
            'user_id': user_id,
            'album_id': 'profile',
            'extended': 1
        })

        try:
            photos = photos['items']
        except KeyError:
            return []

        result = []
        for photo in photos:
            result.append({
                'owner_id': photo['owner_id'],
                'id': photo['id'],
                'likes': photo['likes']['count'],
                'comments': photo['comments']['count']
            })

        result.sort(key=lambda x: x['likes'] + x['comments'] * 10, reverse=True)
        return result
    
    def search_worksheet(self, params, offset):
        try:
            users = self.api.method('users.search',
                                      {
                                       'count': 20,
                                       'offset': offset,
                                       'hometown': params['city'],
                                       'sex': 1 if params['sex'] == 2 else 2,
                                       'has photo': True,
                                       'age_from': params['age'] - 3,
                                        'age_to': params['age'] + 3
                                      }
                                      )
        except ApiError as e:
            users = []
            print(f'error = (e)')
            
        result = [{'name': item['first_name'] + item['last_name'],
                    'id': item['id']        
                    } for item in users['items'] if item['is_closed'] is False
                  ]
        return result
    
    def get_photos(self, user_id):
            photos = self.api.method('photos.get', {
                'user_id': user_id,
                'album_id': 'profile',
                'extended': 1
            })

            try:
                photos = photos['items']
            except KeyError:
                return []

            result = []
            for photo in photos:
                likes_count = photo['likes']['count'] if 'likes' in photo else 0
                comments_count = photo['comments']['count'] if 'comments' in photo else 0
                
                result.append({
                    'owner_id': photo['owner_id'],
                    'id': photo['id'],
                    'likes': likes_count,
                    'comments': comments_count
                })

            result.sort(key=lambda x: x['likes'] + x['comments'] * 10, reverse=True)
            '''сортировка по лайкам и комментам'''
            
            return result[:3]


if __name__ == '__main__':
    user_id = 789657038
    tools = VkTools(access_token)
    params = tools.get_profile_info(user_id)
    worksheets = tools.search_worksheet(params, 10)
    worksheet = worksheets.pop()
    photos = tools.get_photos(worksheet['id'])
    
    pprint(worksheets)