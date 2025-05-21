
from django.core.files.storage import Storage
from replit.object_storage import Client
import os

class ReplitObjectStorage(Storage):
    def __init__(self):
        self.client = Client()
        
    def _save(self, name, content):
        self.client.upload_file(name, content)
        return name
        
    def _open(self, name, mode='rb'):
        return self.client.get_file(name)
        
    def url(self, name):
        return self.client.get_url(name)
        
    def exists(self, name):
        try:
            self.client.get_file(name)
            return True
        except:
            return False
        
    def size(self, name):
        return self.client.get_file_size(name)
        
    def delete(self, name):
        self.client.delete_file(name)
