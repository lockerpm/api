import ast
import uuid

from django.db import models

from cystack_models.models.teams.teams import Team
from cystack_models.models.users.users import User


class Cipher(models.Model):
    id = models.CharField(primary_key=True, max_length=128, default=uuid.uuid4)
    creation_date = models.FloatField()
    revision_date = models.FloatField()
    deleted_date = models.FloatField(null=True)
    reprompt = models.IntegerField(default=0)

    score = models.FloatField(default=0)
    type = models.IntegerField()
    data = models.TextField(blank=True, null=True)
    favorites = models.TextField(blank=True, null=True)
    folders = models.TextField(blank=True, null=True, default="")
    view_password = models.BooleanField(default=True)

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="ciphers", null=True)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="ciphers", null=True)

    class Meta:
        db_table = 'cs_ciphers'

    def get_data(self):
        if not self.data:
            return {}
        return ast.literal_eval(str(self.data))

    def get_favorites(self):
        if not self.favorites:
            return {}
        return ast.literal_eval(str(self.favorites))

    def set_favorite(self, user_id, is_favorite=False):
        favorites = self.get_favorites()
        favorites[user_id] = is_favorite
        self.favorites = favorites
        self.save()

    def get_folders(self):
        if not self.folders:
            return {}
        return ast.literal_eval(str(self.folders))

    def set_folder(self, user_id, folder_id=None):
        folders = self.get_folders()
        folders[user_id] = folder_id
        self.folders = folders
        self.save()
