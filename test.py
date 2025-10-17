import requests
from rich import print


def extract_text_from_image(image_path):
    url = "http://localhost:6969/extract-text"
    with open(image_path, "rb") as image_file:
        # sending with filename and MIME type
        files = {
            "image": (
                image_path.split("/")[-1],
                image_file,
                f"image/{image_path.split('.')[-1]}",
            )
        }
        print(files)
        response = requests.post(url, files=files)
        return response.json()


if __name__ == "__main__":
    test_image_path = "/home/muntasirfahim/personal/flexbone_task/images/meme.jpeg"
    result = extract_text_from_image(test_image_path)
    print(f"Response from server: {result}")
