import requests

# First step: sending dummy data to a dummy address (Carol will provide the real address later)
# Second step: sending detected plate data and the spot in which it was detected
ADDRESS = "https://easy-park-iw.herokuapp.com/user/linkUserToSpot"


if __name__ == "__main__":
    response = requests.post(
        ADDRESS,
        json={
            "plate": "DEF1234y",
            "spot": "V1",
        },
    )
    print(response.status_code)
