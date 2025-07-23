from django.apps import AppConfig



class CustomersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'customers'


    def ready(self):
        import customers.signals
        """
        This method is called when the Django app is fully loaded.

        We use it to import and register signal handlers, like post_save for Vendor,
        so that they are connected when the app starts.

        Without this, the signal receivers (in signals.py) would not be registered
        because simply importing the file in the project does not trigger them.

        Example:
            - post_save signal on Vendor to create a PaystackCustomer

        """
       
       