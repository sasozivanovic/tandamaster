from IPython import embed

import taglib

def _strip(tags):
    """Pulls single list items out of lists."""
    print()
    return dict((t,v[0] if isinstance(v,list) and len(v)==1 else v) for t,v in tags.items())

class Librarian:

    _cache = {}

    def _cache_file(self, filename):
        if filename not in self._cache:
            #try:
                audiofile = taglib.File(filename)
                self._cache[filename] = _strip(audiofile.tags) # hmm
            #except:
            #    self._cache[filename] = {}

    def tags(self, Id = None, filename = None):
        if Id:
            return None # todo
        elif filename:
            self._cache_file(filename)
            return self._cache[filename]

    def tag(self, key, Id = None, filename = None):
        if Id:
            return None # todo
        elif filename:
            self._cache_file(filename)
            try:
                return self._cache[filename][key]
            except KeyError:
                return None
        
