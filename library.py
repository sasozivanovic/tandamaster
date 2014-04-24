from IPython import embed

import taglib

def _strip(tags):
    """Pulls single list items out of lists."""
    return dict((t,v[0] if isinstance(v,list) and len(v)==1 else v) for t,v in tags.items())

class Librarian:

    _cache = {}

    def _cache_file(self, filename):
        if filename not in self._cache:
            try:
                audiofile = taglib.File(filename)
                tags = audiofile.tags
                self._cache[filename] = _strip(tags)
            except OSError:
                self._cache[filename] = None

    def tags_by_id(self, Id):
        return None # todo

    def tag_by_id(self, key, Id):
        return None # todo

    def tags_by_filename(self, filename):
        self._cache_file(filename)
        return self._cache[filename]

    def tag_by_filename(self, key, filename):
        self._cache_file(filename)
        try:
            return self._cache[filename][key]
        except KeyError:
            return None
        
