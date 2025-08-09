import errno
import os
from gzip import open as gzip_open
from urllib.parse import urljoin


class HashFileCache:
    def __init__(self, root, url, gzip=False):
        self.root = root
        self.url = url
        self.gzip = gzip

    def create(self, file_hash):
        try:
            os.makedirs(os.path.join(self.root, file_hash))
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

    def has_file(self, file_hash, file):
        return os.path.isfile(self.get_path(file_hash, file))

    def get_path(self, file_hash, file):
        return os.path.join(self.root, file_hash, file)

    def get_url(self, file_hash, file):
        return urljoin(self.url, f"{file_hash}/{file}")

    def read_file(self, file_hash, file):
        return open(self.get_path(file_hash, file), "rb")

    def read_data(self, file_hash, file):
        with self.read_file(file_hash, file) as f:
            return f.read()

    def cache_data(self, file_hash, file, data, url=True, gzip=True):
        if gzip and self.gzip:
            with gzip_open(self.get_path(file_hash, file + ".gz"), "wb") as f:
                f.write(data)

        with open(self.get_path(file_hash, file), "wb") as f:
            f.write(data)

        if url:
            return self.get_url(file_hash, file)
        return None
