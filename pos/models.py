from django.db import models
from django.forms import model_to_dict

class RoomType(models.Model):
    STATUS_CHOICES = (
        ("ACTIVE", "Active"),
        ("INACTIVE", "Inactive")
    )

    name = models.CharField(max_length=256)
    description = models.TextField(max_length=256)
    status = models.CharField(
        choices=STATUS_CHOICES,
        max_length=100,
        verbose_name="Status of the room type",
    )

    class Meta:
        db_table = "RoomType"
        verbose_name_plural = "Room Types"

    def __str__(self):
        return self.name

class Room(models.Model):
    STATUS_CHOICES = (
        ("ACTIVE", "Active"),
        ("INACTIVE", "Inactive")
    )

    name = models.CharField(max_length=256)
    description = models.TextField(max_length=256)
    status = models.CharField(
        choices=STATUS_CHOICES,
        max_length=100,
        verbose_name="Status of the room",
    )
    room_type = models.ForeignKey(
        RoomType, related_name="room_type", on_delete=models.CASCADE, db_column='room_type')
    price = models.FloatField(default=0)

    class Meta:
        db_table = "Room"

    def __str__(self):
        return self.name

    def to_json(self):
        item = model_to_dict(self)
        item['id'] = self.id
        item['text'] = self.name
        item['room_type'] = self.room_type.name
        item['total_room'] = 0
        return item
