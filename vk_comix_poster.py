import os
import random
import requests
from urllib.parse import urlsplit
from dotenv import load_dotenv

VK_API_URL = "https://api.vk.com/method"
VK_API_VERSION = "5.131"


def create_folder(folder="Files"):
    """Создает папку, если она не существует."""
    os.makedirs(folder, exist_ok=True)


def get_comic():
    """Получает случайный комикс с сайта xkcd."""
    url = "https://xkcd.com/info.0.json"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()


def check_vk_errors(response):
    """Проверяет наличие ошибок в ответе VK API."""
    if "error" in response:
        raise Exception(f"VK API Error: {response['error']['error_msg']}")
    return response


def download_picture(picture_url, folder="Files"):
    """Скачивает изображение по заданному URL."""
    file_name = os.path.basename(urlsplit(picture_url).path)
    response = requests.get(picture_url)
    response.raise_for_status()
    file_path = os.path.join(folder, file_name)
    with open(file_path, "wb") as file:
        file.write(response.content)
    return file_name


def get_upload_url(access_token, group_id):
    """Получает URL для загрузки изображения на сервер VK."""
    params = {
        "access_token": access_token,
        "v": VK_API_VERSION,
        "group_id": group_id
    }
    response = requests.get(f"{VK_API_URL}/photos.getWallUploadServer", params=params)
    response.raise_for_status()
    return check_vk_errors(response.json())["response"]["upload_url"]


def upload_picture(file_name, upload_url, folder="Files"):
    """Загружает изображение на сервер VK."""
    file_path = os.path.join(folder, file_name)
    with open(file_path, "rb") as file:
        files = {"photo": file}
        response = requests.post(upload_url, files=files)
    response.raise_for_status()
    return response.json()


def save_picture_on_vk(server, photo_hash, photo, access_token, group_id):
    """Сохраняет изображение на сервере VK."""
    params = {
        "access_token": access_token,
        "v": VK_API_VERSION,
        "group_id": group_id,
        "server": server,
        "hash": photo_hash,
        "photo": photo
    }
    response = requests.post(f"{VK_API_URL}/photos.saveWallPhoto", params=params)
    response.raise_for_status()
    vk_response = check_vk_errors(response.json())
    saved_photo = vk_response["response"][0]
    return saved_photo["owner_id"], saved_photo["id"]


def publish_picture_on_wall(owner_id, attachment_id, message, access_token, group_id):
    """Публикует изображение на стене группы VK."""
    params = {
        "access_token": access_token,
        "v": VK_API_VERSION,
        "owner_id": f"-{group_id}",
        "from_group": 1,
        "message": message,
        "attachments": f"photo{owner_id}_{attachment_id}"
    }
    response = requests.post(f"{VK_API_URL}/wall.post", params=params)
    response.raise_for_status()
    check_vk_errors(response.json())


def remove_temp_file(file_name, folder="Files"):
    """Удаляет временный файл."""
    file_path = os.path.join(folder, file_name)
    if os.path.exists(file_path):
        os.remove(file_path)


def main():
    load_dotenv()

    try:
        vk_access_token = os.getenv("VK_ACCESS_TOKEN")
        vk_client_id = os.getenv("VK_CLIENT_ID")
        if not vk_access_token or not vk_client_id:
            raise EnvironmentError("Переменные окружения не установлены.")
    except EnvironmentError as e:
        print(f"Ошибка: {e}")
        return

    file_name = None

    try:
        create_folder()

        comic = get_comic()
        comic_img_url = comic["img"]
        comic_alt_text = comic["alt"]

        print("Скачивание изображения...")
        file_name = download_picture(comic_img_url)

        print("Получение URL для загрузки на сервер ВКонтакте...")
        upload_url = get_upload_url(vk_access_token, vk_client_id)

        print("Загрузка изображения на сервер...")
        upload_response = upload_picture(file_name, upload_url)

        print("Сохранение изображения на сервере VK...")
        owner_id, attachment_id = save_picture_on_vk(
            upload_response["server"],
            upload_response["hash"],
            upload_response["photo"],
            vk_access_token,
            vk_client_id
        )

        print("Публикация изображения на стене группы...")
        publish_picture_on_wall(owner_id, attachment_id, comic_alt_text, vk_access_token, vk_client_id)

        print("Публикация завершена успешно!")

    except requests.RequestException as error:
        print(f"Ошибка при обработке данных: {error}")
    except Exception as error:
        print(f"Неизвестная ошибка: {error}")
    finally:
        if file_name:
            remove_temp_file(file_name)


if __name__ == "__main__":
    main()
