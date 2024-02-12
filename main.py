import requests
import json
from tqdm import tqdm


class ParsingFromVKToYaDisk:
    API_URL_VK = 'https://api.vk.com/method/photos.get'
    API_URL_YA = 'https://cloud-api.yandex.net/v1/disk/resources/upload'

    def __init__(self, user_id_vk, token_ya, token_vk, count_photo=5):
        self.user_id_vk = user_id_vk
        self.token_ya = token_ya
        self.token_vk = token_vk
        self.count_photo = count_photo

    def get_photos_data(self):
        question = input('По умолчанию загрузится 5 фотографий. Хотите изменить количество фотографий? (да/нет): ')
        if question.lower() == 'да':
            self.count_photo = int(input('Введите количество фотографий: '))

        album = input(
            'Выберете альбом VK из которого нужно сохранить фотографии '
            '(wall - фотографии со стены, profile — фотографии профиля, saved — сохраненные фотографии): ')
        while album not in ['wall', 'profile', 'saved']:
            album = input('Введено некорректное значение. Попробуйте ещё раз: ')

        params = {
            'owner_id': self.user_id_vk,
            'album_id': album,
            'extended': 1,
            'count': self.count_photo,
            'photo_sizes': 1,
            'access_token': self.token_vk,
            'v': '5.199'
        }

        response = requests.get(self.API_URL_VK, params=params)
        photos_list_info = response.json().get('response', {}).get('items')

        return photos_list_info

    def create_folder_on_yad(self):
        name_folder = input('Введите название папки на Яндекс Диске, в которую загрузить фотографии: ')
        url_folder = f'https://cloud-api.yandex.net/v1/disk/resources'
        headers = {
            'Authorization': f'OAuth {self.token_ya}'
        }
        params = {
            'path': name_folder
        }

        requests.put(url_folder, headers=headers, params=params)

        return name_folder

    def _save_info_in_json(self, data, count_photo):
        with open('data_file.json', 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
        print(f'Данные о {count_photo} загруженных фото сохранены в "data_file.json".')

    def uploadind_fotos_to_yad(self, photo_list):
        if len(photo_list) == 0:
            print('В этом альбоме нет фотографий!')
            self._save_info_in_json(photo_list, 0)
            return

        photo_list_info_for_json = []
        folder_name = self.create_folder_on_yad()
        list_names = []

        for i, photo in tqdm(enumerate(photo_list), total=len(photo_list)):
            photo_name = f"{photo.get('likes', {}).get('count')}.jpg"
            if photo_name in list_names:
                photo_name = f"{photo.get('likes', {}).get('count')}_{photo.get('id')}.jpg"
            list_names.append(photo_name)

            url = self.API_URL_YA
            headers = {
                'Authorization': f'OAuth {self.token_ya}'
            }
            params = {
                'path': f'{folder_name}/{photo_name}',
            }

            response = requests.get(url, params=params, headers=headers)
            url_upload = response.json().get('href')

            url_max_size = ''
            size = ''
            max_size = 0

            for elem in photo.get('sizes'):
                if int(elem.get('height')) * int(elem.get('width')) > max_size:
                    url_max_size = elem.get('url')
                    size = elem.get('type')
                    max_size = int(elem.get('height')) * int(elem.get('width'))

            response = requests.get(url_max_size)
            requests.put(url_upload, files={'file': response.content})

            photo_list_info_for_json.append({
                'file_name': photo_name,
                'size': size
            })

        self._save_info_in_json(photo_list_info_for_json, len(photo_list_info_for_json))

user_id_vk_ = input('Введите id пользователя VK: ')
token_vk_ = input('Введите токен VK: ')
token_ya_ = input('Введите токен полигона Яндекс.Диск: ')

if __name__ == '__main__':
    new_object = ParsingFromVKToYaDisk(user_id_vk_, token_ya_, token_vk_)
    photo_info = new_object.get_photos_data()
    new_object.uploadind_fotos_to_yad(photo_info)
