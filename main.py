import requests
import json
import configparser
from tqdm import tqdm
from datetime import datetime

# Чтение конфигурационного файла
config = configparser.ConfigParser()
config.read('settings.ini')

# Получение токенов из конфигурационного файла
VKtoken = config["VK"]["token"]
YAtoken = config["Yandex"]["token"]
VK_id = config["VK"]["id_vk"]

class VK:
    def __init__(self, token, version, count_photo=5):
        self.token = token
        self.version = version
        self.count_photo = count_photo

    def get_owner_id(self):
        # Получение ID пользователя VK
        owner_input = input('Введите ID или screen_name целевого профиля VK: ')
        try:
            owner_id = int(owner_input)
        except ValueError:
            # Если введен screen_name, получаем его id через API VK
            response = requests.get('https://api.vk.com/method/utils.resolveScreenName', params={
                'screen_name': owner_input,
                'access_token': self.token,
                'v': self.version
            }).json()
            owner_id = response['response']['object_id']
        return owner_id

    def get_photo(self):
        # Получение фотографий из VK API
        owner_id = self.get_owner_id()

        url = 'https://api.vk.com/method/photos.get'

        question = input('По умолчанию загрузится 5 фотографий. Хотите изменить количество фотографий? (да/нет): ')
        if question.lower() == 'да':
            self.count_photo = int(input('Введите количество фотографий: '))

        album = input(
            'Выберете альбом VK из которого нужно сохранить фотографии '
            '(wall - фотографии со стены, profile — фотографии профиля, saved — сохраненные фотографии): ')
        while album not in ['wall', 'profile', 'saved']:
            album = input('Введено некорректное значение. Попробуйте ещё раз: ')

        params = {
            'owner_id': owner_id,
            'access_token': self.token,
            'v': self.version,
            'extended': '1',
            'album_id': album,
            'photo_sizes': '1',
            'sort': '1',
            'offset': '0',
            'count': self.count_photo
        }

        response = requests.get(url, params=params).json()

        dict_photo = {}
        if 'response' in response and 'items' in response['response']:
            for item in response['response']['items']:
                likes = item.get('likes', {}).get('count', 0)
                sizes = item.get('sizes', [])
                for size in sizes:
                    if size.get('type') == 'z':
                        dict_photo[likes] = size.get('url', '')
        return dict_photo


class YandexDisk:
    def __init__(self, token):
        self.token = token

    def get_headers(self):
        # Получение заголовков для запросов к API Яндекс.Диска
        return {
            'Content-Type': 'application/json',
            'Authorization': 'OAuth {}'.format(self.token)
        }

    def create_folder_on_yadisk(self, disk_folder_path):
        # Создание папки на Яндекс.Диске
        upload_url = "https://cloud-api.yandex.net/v1/disk/resources"
        headers = self.get_headers()
        response = requests.put(f'{upload_url}?path={disk_folder_path}', headers=headers)
        if response.status_code == 201:
            print(f'Создана папка {disk_folder_path} на Яндекс.Диске')

    def get_upload_link(self, disk_file_path):
        # Получение ссылки для загрузки файла на Яндекс.Диск
        upload_url = "https://cloud-api.yandex.net/v1/disk/resources/upload"
        headers = self.get_headers()
        params = {"path": disk_file_path, "overwrite": "true"}
        response = requests.get(upload_url, headers=headers, params=params)
        return response.json()

    def upload_file_to_disk(self, disk_file_path, content):
        # Загрузка файла на Яндекс.Диск
        href = self.get_upload_link(disk_file_path=disk_file_path).get("href", "")
        response = requests.put(href, data=content)
        response.raise_for_status()


def write_data_to_json(photo_dict):
    # Запись данных о фотографиях в JSON файл
    data = []
    for likes, url in photo_dict.items():
        data.append({"likes": likes, "url": url})

    with open("data_files.json", "w") as json_file:
        json.dump(data, json_file, indent=4)
    print("Информация о загруженных фотографиях записана в файл data_files.json")


def download_and_save_photos(photo_dict):
    # Загрузка и сохранение фотографий на Яндекс.Диск
    ya = YandexDisk(token=YAtoken)
    path = input(f'Введите название папки на Яндекс.Диске: ')
    ya.create_folder_on_yadisk(path)

    for likes, url in tqdm(photo_dict.items(), desc="Загрузка фотографий"):
        content = requests.get(url).content
        current_date = datetime.now().strftime("%d-%m-%Y")
        ya.upload_file_to_disk(f"{path}/{likes}_likes_{current_date}.jpg", content)

    write_data_to_json(photo_dict)


def main():
    # Основная функция
    vk = VK(VKtoken, '5.199')
    photo_dict = vk.get_photo()
    download_and_save_photos(photo_dict)


if __name__ == "__main__":
    main()
