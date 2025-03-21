import os
import requests
from urllib.parse import urlsplit
from dotenv import load_dotenv

VK_API_URL = "https://api.vk.com/method"
VK_API_VERSION = "5.131"


def get_comic():
    url = "https://xkcd.com/info.0.json"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()


def download_picture(picture_url, folder="Files"):
    file_name = os.path.basename(urlsplit(picture_url).path)
    response = requests.get(picture_url)
    response.raise_for_status()
    file_path = os.path.join(folder, file_name)
    with open(file_path, "wb") as file:
        file.write(response.content)
    return file_name


def get_upload_url(access_token, group_id):
    params = {"access_token": access_token, "v": VK_API_VERSION, "group_id": group_id}
    response = requests.get(f"{VK_API_URL}/photos.getWallUploadServer", params=params)
    response.raise_for_status()
    return response.json()["response"]["upload_url"]


def upload_picture(file_name, upload_url, folder="Files"):
    file_path = os.path.join(folder, file_name)
    with open(file_path, "rb") as file:
        files = {"photo": file}
        response = requests.post(upload_url, files=files)
    response.raise_for_status()
    return response.json()


def save_picture_on_vk(server, photo_hash, photo, access_token, group_id):
    params = {
        "access_token": access_token,
        "v": VK_API_VERSION,
        "group_id": group_id,
        "server": server,
        "hash": photo_hash,
        "photo": photo,
    }
    response = requests.post(f"{VK_API_URL}/photos.saveWallPhoto", params=params)
    response.raise_for_status()
    saved_photo = response.json()["response"][0]
    return saved_photo["owner_id"], saved_photo["id"]


def publish_picture_on_wall(owner_id, attachment_id, message, access_token, group_id):
    params = {
        "access_token": access_token,
        "v": VK_API_VERSION,
        "owner_id": f"-{group_id}",
        "from_group": 1,
        "message": message,
        "attachments": f"photo{owner_id}_{attachment_id}",
    }
    response = requests.post(f"{VK_API_URL}/wall.post", params=params)
    response.raise_for_status()


def main():
    load_dotenv()
    try:
        vk_access_token = os.environ["VK_ACCESS_TOKEN"]
        vk_client_id = os.environ["VK_CLIENT_ID"]
    except KeyError as e:
        print(f"Ошибка: обязательная переменная окружения {str(e)} не установлена.")
        return

    os.makedirs("Files", exist_ok=True)
    file_name = None
    try:
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
            vk_client_id,
        )
        print("Публикация изображения на стене группы...")
        publish_picture_on_wall(
            owner_id, attachment_id, comic_alt_text, vk_access_token, vk_client_id
        )
        print("Публикация завершена успешно!")
    except requests.RequestException as error:
        print(f"Ошибка при обработке данных: {error}")
    except Exception as error:
        print(f"Неизвестная ошибка: {error}")
    finally:
        if file_name:
            try:
                os.remove(os.path.join("Files", file_name))
            except OSError as e:
                print(f"Ошибка удаления файла: {e}")


if __name__ == "__main__":
    main()
