# About the project

This project extracts data from the website **https://www.nordstrom.com/** and sends it by email.

When the process starts I receive a message on Telegram, and when the process is finished I also receive a message.

This process runs once a week.

# The problem

The site blocks every X requests

# Solution
When the site is blocked I run a browser where I reload all the cookies, get new cookies and send them to process to continue without a browser.

For this solution I implemented a Docker image with a GUI where I can open a real browser.

This process doesn't work with Selenium so I created an extension to get all the data I need.


# How to run

* Configure keys in `app/.env`
  ![image](https://github.com/cleber-silva-web-scraping/python-docker-extension-nordstrom/assets/6031795/62513662-48bc-44b8-8c72-97264fb5e20b)


# Build a docker image
* docker build . -t local/vncubuntu:0.0.1

# Run docker or add in cron job
* docker run -d -p 6901:6901 -p 5901:5901  -v /dev/shm:/dev/shm -v ./out:/home/rpa/out   local/vncubuntu:0.0.1


The result will be stored in the `out` folder and sent by email.

![image](https://github.com/cleber-silva-web-scraping/python-docker-extension-nordstrom/assets/6031795/7b27c59f-a719-4833-bd54-1b0d2169c48d)



