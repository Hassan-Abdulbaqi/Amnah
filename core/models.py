from django.db import models


class Partner(models.Model):
    name = models.CharField(max_length=255, unique=True)
    joined_amount = models.BigIntegerField()
    percentage = models.DecimalField(max_digits=5, decimal_places=2, help_text="Percentage of profit share (0-100)")

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.percentage}%)"


class Order(models.Model):
    INGOING = "IN"
    OUTGOING = "OUT"
    TYPE_CHOICES = [
        (INGOING, "Ingoing"),
        (OUTGOING, "Outgoing"),
    ]

    name = models.CharField(max_length=255)
    order_type = models.CharField(max_length=3, choices=TYPE_CHOICES, null=True, blank=True)
    price = models.BigIntegerField()
    date = models.DateField()
    description = models.TextField(blank=True)
    customer_name = models.CharField(max_length=255, blank=True)
    customer_address = models.TextField(blank=True)

    class Meta:
        ordering = ["-date", "name"]

    def __str__(self) -> str:
        direction = dict(self.TYPE_CHOICES).get(self.order_type, self.order_type)
        return f"{self.name} - {direction} - {self.price} on {self.date}"

    @property
    def signed_amount(self) -> float:
        """Return price as positive for INGOING, negative for OUTGOING, and 0 for null/empty."""
        if self.order_type == self.INGOING:
            return self.price
        elif self.order_type == self.OUTGOING:
            return -self.price
        else:
            return 0


class ActivityLog(models.Model):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    ACTION_CHOICES = [
        (CREATE, "Create"),
        (UPDATE, "Update"),
        (DELETE, "Delete"),
    ]

    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey("auth.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="activity_logs")
    action = models.CharField(max_length=12, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=100)
    object_id = models.BigIntegerField()
    object_repr = models.TextField()
    details = models.TextField(blank=True)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self) -> str:
        who = self.user.username if self.user else "system"
        return f"{self.timestamp} {who} {self.action} {self.model_name}#{self.object_id}"