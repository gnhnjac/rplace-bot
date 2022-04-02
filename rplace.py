
import requests
import requests.auth
import pyppeteer
import asyncio
import urllib
import json
from PIL import Image
import time

dst_image = Image.open('dest.png').convert('RGB')

# Params
RED = (255, 69, 0)
BLACK = (0, 0, 0)
STARTX = 755
STARTY = 274
SHOW_PUPPETEER = True
USERNAME = ""
PASSWORD = ""
OAUTH_NAME = ""
OAUTH_SECRET = ""
CHROMEPATH = 'C:\Program Files\Google\Chrome\Application\chrome.exe'

headers = {"User-Agent": "api/0.1 by gnhnjac"}
cauth = requests.auth.HTTPBasicAuth(OAUTH_NAME, OAUTH_SECRET)
re = requests.post("https://www.reddit.com/api/v1/access_token", auth=cauth, data={'grant_type': 'password', 'username': USERNAME, 'password': PASSWORD}, headers=headers)
token = json.loads(re.content)["access_token"]

found = None
found2 = None

def eval_request(req):
  global found
  if "canvas-images" in req.url and found is None:
    found2 = req.url
  if "canvas-images" in req.url and found is not None:
    found = req.url

async def act(x, y):

  placed = False

  global found, STARTX, STARTY
  browser = await pyppeteer.launch(headless=not SHOW_PUPPETEER, executablePath=CHROMEPATH, args=['--disable-dev-shm-usage'])
  page = await browser.newPage()
  await page.goto("https://www.reddit.com/r/place/")

  # fetch page requests
  await page.setRequestInterception(True)
  page.on('request', eval_request)
  await page.screenshot({'path': 'reddit.png'})
  await page.mouse.click(0,0)

  while found is None or found2 is None:
    continue
    
  print("Fetched image")

  urllib.request.urlretrieve(found, "backgroundp1.jpg")
  urllib.request.urlretrieve(found2, "backgroundp2.jpg")

  imgp1 = Image.open("backgroundp1.jpg").convert('RGB')
  imgp2 = Image.open("backgroundp2.jpg").convert('RGB')
  img = Image.new('RGB', (2000, 1000), (255,255,255))
  img.paste(imgp1, (0,0))
  img.paste(imgp2, (1000,0))
  color = dst_image.getpixel((x, y))
  if img.getpixel((STARTX + x, STARTY + y)) != color:
    if place_pix(STARTX + x, STARTY + y, color):
        placed = True
        print("Placed pixel at " + str(STARTX + x) + ", " + str(STARTY + y) + " with color " + str(color))
  else:
    placed = None
    print("Pixel already placed at " + str(STARTX + x) + ", " + str(STARTY + y) + " with color " + str(color))

  await browser.close()

  return placed

def place_pix(x, y, color):

  if color == BLACK:
     color_ind = 27
  elif color == RED:
      color_ind = 2
    

  res = requests.post("https://gql-realtime-2.reddit.com/query", headers={    "accept": "*/*",
      "accept-language": "en,en-US;q=0.9,he;q=0.8",
      "apollographql-client-name": "mona-lisa",
      "apollographql-client-version": "0.0.1",
      "authorization": "Bearer " + token,
      "content-type": "application/json",
      "sec-ch-ua": "\" Not A;Brand\";v=\"99\", \"Chromium\";v=\"100\", \"Google Chrome\";v=\"100\"",
      "sec-ch-ua-mobile": "?0",
      "sec-ch-ua-platform": "\"Windows\"",
      "sec-fetch-dest": "empty",
      "sec-fetch-mode": "cors",
      "sec-fetch-site": "same-site"}, data="{\"operationName\":\"setPixel\",\"variables\":{\"input\":{\"actionName\":\"r/replace:set_pixel\",\"PixelMessageData\":{\"coordinate\":{\"x\":" + str(x) + ",\"y\":" + str(y) + "},\"colorIndex\":" + str(color_ind) +",\"canvasIndex\":0}}},\"query\":\"mutation setPixel($input: ActInput!) {\\n  act(input: $input) {\\n    data {\\n      ... on BasicMessage {\\n        id\\n        data {\\n          ... on GetUserCooldownResponseMessageData {\\n            nextAvailablePixelTimestamp\\n            __typename\\n          }\\n          ... on SetPixelResponseMessageData {\\n            timestamp\\n            __typename\\n          }\\n          __typename\\n        }\\n        __typename\\n      }\\n      __typename\\n    }\\n    __typename\\n  }\\n}\\n\"}"
      )

  if b"Ratelimited" in res.content:
    print("Rate limited")
    time.sleep(10)
    return False
    
  if res.status_code != 200:
    print("Error placing pixel: " + str(res.status_code))
    return False
  return True


async def main():
  x = 0
  y = 0
  while True:
      placed = await act(x, y)
      if placed is None:
        x += 1
        if x >= dst_image.size[0]:
          x = 0
          y += 1
          if y >= dst_image.size[1]:
            y = 0
        continue
      if placed:
        # sleep 5 minutes
        x += 1
        if x >= dst_image.size[0]:
          x = 0
          y += 1
          if y >= dst_image.size[1]:
            y = 0
        print("Sleeping for 5 minutes...")
        time.sleep(300)

asyncio.get_event_loop().run_until_complete(main())