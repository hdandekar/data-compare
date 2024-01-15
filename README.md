# Data-Match

Data Match is a Django App to compare data between 2 different data sources, it helps in identifying the differences between 2 datasets.

License: MIT


## Development

### Type checks

Running type checks with mypy:

    $ mypy data_compare

## Deployment

The following details how to deploy this application.

1. Clone the github Repo
2. Run ```pip install -r requirements\production.txt```
3. Configure database(postgres for production usage) and add details in ```config/settings/production.py```
4. Run ```python manage.py migrate```
5. Create a superuser using ```python manage.py createsuperuser```
6. Launch the app using ```python manage.py runserver```
