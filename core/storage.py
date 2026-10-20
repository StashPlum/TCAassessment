"""Private document boundary used by Django FileField.

The local backend stores under MEDIA_ROOT; no public URL route is installed.
The download view checks site and classification before opening a file.
A corporate backend can implement Django's Storage contract later.
"""
from django.core.files.storage import FileSystemStorage
from django.conf import settings

class PrivateLocalStorage(FileSystemStorage):
    def __init__(self):
        super().__init__(location=settings.MEDIA_ROOT,base_url=None)

    def url(self, name):
        raise ValueError('Private evidence has no public URL. Use the authorized download view.')


def open_or_404(field):
    """Open a private file; a file that no longer exists (temporary demo storage) is a clean 404."""
    from django.http import Http404
    try: return field.open('rb')
    except (FileNotFoundError,OSError,ValueError): raise Http404('This file is no longer available. Uploads are temporary in the hosted demo.')
