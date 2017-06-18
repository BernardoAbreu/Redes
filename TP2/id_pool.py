

class IdPool(object):

    def __init__(self):
        self.emitters = {}
        self.exhibitors = {}
        self.sock = {}


    def _get_next_id(self, minimum_id, pool):
        next_id = minimum_id
        want = minimum_id

        for i in pool:
            if i > want:
                break
            elif i == want:
                want += 1
        next_id = want

        return next_id


    def get_next_exhibitor_id(self, s):
        if len(self.exhibitors) < 4096:
            next_id = self._get_next_id(4096, self.exhibitors.iterkeys())
            self.exhibitors[next_id] = False
            self.sock[next_id] = s
            return next_id
        else:
            return -1


    def get_next_emitter_id(self, s):
        if len(self.emitters) < 4096:
            next_id = self._get_next_id(1, self.emitters.iterkeys())
            self.emitters[next_id] = False
            self.sock[next_id] = s
            return next_id
        else:
            return -1


    def remove_id(self, id):
        first, second = (self.emitters, self.exhibitors) if id < 4096 else (self.exhibitors, self.emitters)

        if first[id]:
            second[first[id]] = False

        del first[id]
        del self.sock[id]


    def id_exists(self, id):
        return (id in self.sock.iterkeys())


    def associate_clients(self, emitter, exhibitor):
        if emitter in self.emitters.iterkeys() and exhibitor in self.exhibitors.iterkeys():
            self.emitters[emitter] = exhibitor
            self.exhibitors[exhibitor] = emitter
            return True
        else:
            return False


    def get_associate(self,id):
        return self.emitters[id] if id < 4096 else self.exhibitor[id]


    def remove_socket_if_exists(self, s):
        self.sock = {k:v for k,v in self.sock.iteritems() if v != s}


    def get_sock(self, id):
        return self.sock[id]


    def get_all_clients(self):
        return self.sock.keys()


    def get_all_exhibitors(self):
        return self.exhibitors.keys()