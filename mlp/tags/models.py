import random
import string
from django.db import models

class TaggableManager(models.Manager):
    def retag(self, tags, user, taggable_object):
        """
        This provides a nice interface to retag an object that has a
        manytomany relationship with the tags table (FileTag, UserTag, etc)

        The many2many table this manager is attached to assumes there is a
        field with the same name as the name of the taggable_object's
        classname
        """
        # we assume the many2many table has a field with this particular name
        field_name = taggable_object.__class__.__name__.lower()
        tags = set(tags or [])
        queryset = self.filter(**{
            field_name: taggable_object,
        })
        existing_tags = set(obj_tag.tag.name for obj_tag in queryset.select_related("tag"))
        to_remove = existing_tags - tags
        queryset.filter(tag__name__in=to_remove).delete()

        to_add = tags - existing_tags
        instances = []
        for tag in to_add:
            try:
                tag = Tag.objects.get(name=tag)
            except Tag.DoesNotExist as e:
                tag = Tag(name=tag, created_by=user)
                tag.save()
            instances.append(self.model(tag=tag, tagged_by=user, **{field_name: taggable_object}))

        self.bulk_create(instances)


class Tag(models.Model):
    BLUE = '#428bca'
    WHITE = '#ffffff'
    BLACK = '#000000'
    GREEN = '#7bd148'
    BOLD_BLUE = '#5484ed'        
    LIGHT_BLUE = '#a4bdfc'
    TURQUOISE = '#46d6db'
    LIGHT_GREEN = '#7ae7bf'
    BOLD_GREEN = '#51b749'
    YELLOW = '#fbd75b'
    ORANGE = '#ffb878'
    RED = '#ff887c'
    BOLD_RED = '#dc2127'
    PURPLE = '#dbadff'
    GREY = '#e1e1e1'    

    DEFAULT_BACKGROUND_COLOR = BLUE
    DEFAULT_COLOR = WHITE

    COLORS = (
        (BLUE, 'Blue'),
        (WHITE, 'White'),
        (BLACK, 'Black'),
        (GREEN, 'Green'),
        (BOLD_BLUE, 'Bold blue'),
        (LIGHT_BLUE, 'Light Blue'),
        (TURQUOISE, 'Turquoise'),
        (LIGHT_GREEN, 'Light green'),
        (BOLD_GREEN, 'Bold green'),
        (YELLOW, 'Yellow'),
        (ORANGE, 'Orange'),
        (RED, 'Red'),
        (BOLD_RED, 'Bold red'),
        (PURPLE, 'Purple'),
        (GREY, 'Grey'),
    )
    

    tag_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    # tags can be styled with a text color and a bgcolor
    color = models.CharField(max_length=16, choices=COLORS, verbose_name="Text Color")
    background_color = models.CharField(max_length=16, choices=COLORS)

    created_by = models.ForeignKey('users.User', null=True, on_delete=models.SET_NULL)

    class Meta:
        db_table = "tag"

    def __str__(self):
        return self.name

    def to_css_class(self):
        """
        This encodes a tag name as a valid CSS identifier. It mirrors the
        encodeTag function in our JavaScript
        """
        simple_chars = set(string.ascii_letters + string.digits)

        # the encoded tag is prefixed with "tag-"
        encoded_tag = ["tag-"]
        for c in self.name:
            if c == "-":
                # dash characters are escaped with another dash
                encoded_tag.append("--")
            elif c in simple_chars:
                # simple characters don't need to be escaped
                encoded_tag.append(c)
            else:
                # non simple characters are escaped with -ASCII_VALUE-
                encoded_tag.append("-" + str(ord(c)) + "-")

        return "".join(encoded_tag)

    @staticmethod
    def get_random_tag_colors():
        '''
        returns a random (good) COLOR and a BACKGROUND COLOR, in that order
        '''

        COLOR_COMBINATIONS = (
            (Tag.WHITE, Tag.BLUE),
            (Tag.WHITE, Tag.GREEN),
            (Tag.WHITE, Tag.BLACK),
            (Tag.WHITE, Tag.BOLD_BLUE),
            (Tag.WHITE, Tag.TURQUOISE),
            (Tag.WHITE, Tag.BOLD_GREEN),
            (Tag.WHITE, Tag.RED),
            (Tag.WHITE, Tag.BOLD_RED),
            (Tag.YELLOW, Tag.BLUE),
            (Tag.YELLOW, Tag.BLACK),
            (Tag.BOLD_RED, Tag.BLACK),
            (Tag.YELLOW, Tag.BOLD_BLUE),
            (Tag.YELLOW, Tag.BOLD_GREEN),
            (Tag.YELLOW, Tag.BOLD_RED),
            (Tag.GREEN, Tag.BLACK),
            (Tag.GREEN, Tag.BOLD_BLUE),
            (Tag.BOLD_BLUE, Tag.YELLOW),
            (Tag.BOLD_BLUE, Tag.GREY),
            (Tag.BOLD_BLUE, Tag.BOLD_BLUE),
            (Tag.BOLD_BLUE, Tag.BOLD_GREEN),
            (Tag.BOLD_BLUE, Tag.ORANGE),
            (Tag.BLACK, Tag.GREY),
            (Tag.BLACK, Tag.LIGHT_GREEN),
            (Tag.BLACK, Tag.PURPLE),
            (Tag.BLACK, Tag.RED),
            (Tag.BLACK, Tag.ORANGE),
            (Tag.BLACK, Tag.YELLOW),
            (Tag.BLACK, Tag.LIGHT_GREEN),
            (Tag.BLACK, Tag.BLUE),
            (Tag.ORANGE, Tag.BLUE),
        )

        return random.choice(COLOR_COMBINATIONS)
