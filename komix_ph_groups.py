import os
import random
import requests
from urllib.parse import urlsplit
from dotenv import load_dotenv

VK_API_URL = "https://api.vk.com/method"
VK_API_VERSION = "5.131"

def main():
    load_dotenv()
    try:
        VK_ACCESS_TOKEN = os.environ["VK_ACCESS_TOKEN"]
        VK_CLIENT_ID = os.environ["VK_CLIENT_ID"]
    except KeyError as e:
        print(f"Ошибка: переменная окружения {str(e)} не установлена.")
        return

    def get_comic():
        try:
            url = "https://xkcd.com/info.0.json"
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Ошибка при получении комикса: {e}")
            raise
        except ValueError as e:
            print(f"Ошибка при парсинге JSON: {e}")
            raise

    def check_vk_errors(response):
        if "error" in response:
            raise Exception(f"VK API Error: {response['error']['error_msg']}")
        return response

    def download_picture(picture_url, folder="Files"):
        try:
            file_name = os.path.basename(urlsplit(picture_url).path)
            os.makedirs(folder, exist_ok=True)
            response = requests.get(picture_url)
            response.raise_for_status()
            file_path = os.path.join(folder, file_name)
            with open(file_path, "wb") as file:
                file.write(response.content)
            return file_name
        except requests.RequestException as e:
            print(f"Ошибка при скачивании изображения: {e}")
            raise

    def get_upload_url(access_token, group_id):
        try:
            params = {
                "access_token": access_token,
                "v": VK_API_VERSION,
                "group_id": group_id
            }
            response = requests.get(f"{VK_API_URL}/photos.getWallUploadServer", params=params)
            response.raise_for_status()
            return check_vk_errors(response.json())["response"]["upload_url"]
        except requests.RequestException as e:
            print(f"Ошибка при получении URL для загрузки: {e}")
            raise
        except Exception as e:
            print(f"Ошибка при получении URL для загрузки на сервер ВКонтакте: {e}")
            raise

    def upload_picture(file_name, upload_url, folder="Files"):
        file_path = os.path.join(folder, file_name)
        try:
            with open(file_path, "rb") as file:
                files = {"photo": file}
                response = requests.post(upload_url, files=files)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Ошибка при загрузке изображения: {e}")
            raise

    def save_picture_on_vk(server, _hash, photo, access_token, group_id):
        try:
            params = {
                "access_token": access_token,
                "v": VK_API_VERSION,
                "group_id": group_id,
                "server": server,
                "hash": _hash,
                "photo": photo
            }
            response = requests.post(f"{VK_API_URL}/photos.saveWallPhoto", params=params)
            response.raise_for_status()
            vk_response = check_vk_errors(response.json())
            saved_photo = vk_response["response"][0]
            return saved_photo["owner_id"], saved_photo["id"]
        except requests.RequestException as e:
            print(f"Ошибка при сохранении изображения: {e}")
            raise
        except Exception as e:
            print(f"Ошибка при сохранении изображения на сервере ВКонтакте: {e}")
            raise

    def publish_picture_on_wall(owner_id, attachment_id, message, access_token, group_id):
        try:
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
        except requests.RequestException as e:
            print(f"Ошибка при публикации на стене: {e}")
            raise
        except Exception as e:
            print(f"Ошибка при публикации изображения на стене группы: {e}")
            raise

    try:
        comic = get_comic()
        comic_img_url = comic["img"]
        comic_alt_text = comic["alt"]

        print("Скачивание изображения...")
        file_name = download_picture(comic_img_url)

        print("Получение URL для загрузки на сервер ВКонтакте...")
        upload_url = get_upload_url(VK_ACCESS_TOKEN, VK_CLIENT_ID)

        print("Загрузка изображения на сервер...")
        upload_response = upload_picture(file_name, upload_url)

        os.remove(os.path.join("Files", file_name))

        print("Сохранение изображения...")
        owner_id, attachment_id = save_picture_on_vk(
            upload_response["server"],
            upload_response["hash"],
            upload_response["photo"],
            VK_ACCESS_TOKEN,
            VK_CLIENT_ID
        )

        print("Публикация изображения на стене группы...")
        publish_picture_on_wall(owner_id, attachment_id, comic_alt_text, VK_ACCESS_TOKEN, VK_CLIENT_ID)

        print("Публикация завершена успешно!")

    except (requests.RequestException, ValueError) as error:
        print(f"Ошибка при обработке данных: {error}")
        if os.path.exists(os.path.join("Files", file_name)):
            os.remove(os.path.join("Files", file_name))
    except Exception as error:
        print(f"Неизвестная ошибка: {error}")

if __name__ == "__main__":
    main()
