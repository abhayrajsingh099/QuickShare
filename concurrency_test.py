from concurrent.futures import ThreadPoolExecutor
from urllib.request import Request, urlopen
from urllib.error import HTTPError

URL = (
    "http://localhost:8080/api/transfers/"
    "21a7a797-7e50-433a-b6f7-6a01e25560b4/"
    "files/dd75a911-3645-45e6-b472-b7e46665f23a/download/"
)


def send_request(number):
    request = Request(URL, method="POST")

    try:
        with urlopen(request, timeout=30) as response:
            return number, response.status

    except HTTPError as error:
        return number, error.code


with ThreadPoolExecutor(max_workers=10) as executor:
    results = list(executor.map(send_request, range(1, 11)))

for number, status in results:
    print(f"Request {number}: HTTP {status}")

print("\nSummary:")
print("Successful:", sum(status == 200 for _, status in results))
print("Rejected:", sum(status == 403 for _, status in results))