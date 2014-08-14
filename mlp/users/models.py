from django.db import models
from django.contrib.auth.models import AbstractBaseUser, UserManager
from django.core.urlresolvers import reverse
from django.core.exceptions import PermissionDenied
from mlp.classes.enums import UserRole

class User(AbstractBaseUser):
    """
    Model for a user. Users that have the staff flag raised are
    considered 'super-admins' and have all priviledges.
    Users that want to be admins for their class must set
    that flag in the roster.
    """
    user_id = models.AutoField(primary_key=True)
    email = models.EmailField(max_length=255, unique=True)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    date_joined = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True, blank=True, help_text="Inactive users cannot login")
    is_staff = models.BooleanField(default=False, blank=True)


    USERNAME_FIELD = 'email'

    objects = UserManager()

    class Meta:
        db_table = "user"
        ordering = ['last_name', 'first_name']

    #
    # These methods are required to work with Django's admin
    #
    def get_full_name(self): return self.last_name + ", " + self.first_name
    def get_short_name(self): return self.first_name + " " + self.last_name

    # we don't need granular permissions; all staff will have access to
    # everything
    def has_perm(self, perm, obj=None): return self.is_staff
    def has_module_perms(self, app_label): return self.is_staff

    def __unicode__(self):
        if self.last_name and self.first_name:
            return self.get_full_name()
        else:
            return self.email

    def get_absolute_url(self):
        return reverse("users-detail", args=[self.pk])


    def __str__(self):
        if self.last_name and self.first_name:
            return self.get_full_name()
        else:
            return self.email

    def bind_to_class(self, _class):
        """
        Bind this user to the class and populate their roles based on it.
        """
        roles = set(mlp.classes.models.Roster.objects.filter(user=self, _class=_class).values_list("role", flat=True))
        if not roles:
            # the user doesn't have any roles in this class
            raise PermissionDenied()

        self.roles = roles
        self._class = _class

    def __getattr__(self, attr):
        """
        Instead of creating a bunch of user.is_admin, user.is_uploader,
        user.is_whatever convenience methods, just overload getattr to check
        for user roles when the method name starts with "is_"
        """
        role_names = set(role.lower() for role in UserRole.__dict__.keys())
        # is this a role check?
        if attr.startswith("is_") and attr[len("is_"):] in role_names:
            return getattr(UserRole, attr[len("is_"):].upper()) in self.roles

        raise AttributeError("You tried to access the attribute '%s' on an instance of a User model. That attribute isn't defined" % attr)
