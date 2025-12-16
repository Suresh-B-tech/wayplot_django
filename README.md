
# Setup Instructions

## Prerequisites

- python 3.10+ (install if not present)
- pip (install if not present)

## Installation

1. clone this repo or download the code
2. open a terminal in the project root directory
3. install dependencies:
	```sh
	pip install -r requirements.txt
	```
4. create a `.env` file in the project root with the following content, refer to .env.sample for guidance:
    ```
    CLOUDINARY_CLOUD_NAME="dXXXXXX"
    CLOUDINARY_API_KEY="XXXXXXXXXXXXXX"
    CLOUDINARY_API_SECRET="XXXX-XXXXXXXXXXXXXXX"
    ```

## Database Setup

run migrations:
```sh
python manage.py migrate
```

## Running the Server

start the development server:
```sh
python manage.py runserver
```
open your browser at [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

## Additional Info

- gpx parsing: see `routing/utils/gpx_parser.py`
- path algorithms: see `routing/algorithms/`

## Admin

create a superuser for the admin interface:
```sh
python manage.py createsuperuser
```
