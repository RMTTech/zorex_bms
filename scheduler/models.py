from datetime import datetime
from django.db import models
from django.urls import reverse
from customer.models import Customer
from account.models import Account


class EventAbstract(models.Model):
    """ Event abstract model """
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class EventManager(models.Manager):
    """ Event manager """
    def get_all_events(self, user):
        events = Event.objects.filter(
            event_account=user, is_active=True, is_deleted=False
        )
        return events

    def get_running_events(self, user):
        running_events = Event.objects.filter(
            event_account=user, is_active=True, is_deleted=False,
            end__gte=datetime.now().date()
        ).order_by('start')
        return running_events


class Event(EventAbstract):
    """ Event model """
    id = models.BigAutoField(primary_key=True)
    event_account   = models.ForeignKey(Account, on_delete=models.deletion.CASCADE, related_name='jobs')
    event_parent    = models.ForeignKey(Account, on_delete=models.deletion.CASCADE, related_name='tasks', null=True, blank=True)
    event_customer  = models.ForeignKey(Customer, on_delete=models.deletion.CASCADE, related_name='appointments')
    onapproachsms   = models.BooleanField(default=False)
    completed       = models.BooleanField(default=False)
    completed_time  = models.DateTimeField(null=True, blank=True)
    onsite         = models.BooleanField(default=False)
    onsite_time    = models.DateTimeField(null=True, blank=True)
    description     = models.TextField()
    start           = models.DateTimeField()
    end             = models.DateTimeField()

    objects = EventManager()

    def __str__(self):
        return f'{self.event_account.name}'

    def get_absolute_url(self):
        return reverse('event_list', args=(self.id,))

    @property
    def get_html_url(self):
        url = reverse('event_list', args=(self.id,))
        return f'<a href="{url}"> {self.event_account.name} </a>'

class EventMember(EventAbstract):
    """ Event member model """
    event = models.ForeignKey(
        Event, on_delete=models.deletion.CASCADE, related_name='events'
    )
    event_customer = models.ForeignKey(
        Customer, on_delete=models.deletion.CASCADE, related_name='event_members'
    )

    class Meta:
        unique_together = ['event', 'event_customer']

    def __str__(self):
        return f'{self.event_account.name}'

