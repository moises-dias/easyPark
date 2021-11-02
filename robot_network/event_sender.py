import requests

# First step: sending dummy data to a dummy address (Carol will provide the real address later)
# Second step: sending detected plate data and the spot in which it was detected
ADDRESS = "https://httpbin.org/post"


if __name__ == "__main__":
    response = requests.post(ADDRESS, json={"V0": "ABC1234"})
