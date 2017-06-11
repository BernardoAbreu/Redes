

class IdPool(object):

    def __init__(self):
        self.emitters = {}
        self.exhibitors = {}



    def _get_next_id(self, minimum_id, pool):
        next_id = minimum_id
        want = minimum_id
        print 'get_next'
        for i in pool:
            print i
            if i > want:
                print 1
                break
            elif i == want:
                print 2
                want += 1
        next_id = want

        print 'end get_next'
        return next_id


    def get_next_exhibitor_id(self):
        if len(self.exhibitors) < 4096:
            next_id = self._get_next_id(4096, self.exhibitors.iterkeys())
            self.exhibitors[next_id] = False
            return next_id
        else:
            return -1

    def get_next_emitter_id(self):
        if len(self.emitters) < 4096:
            next_id = self._get_next_id(1, self.emitters.iterkeys())
            self.emitters[next_id] = False
            return next_id
        else:
            return -1


    def remove_id(self, id):
        first, second = (self.emitters, self.exhibitors) if id < 4096 else (self.exhibitors, self.emitters)

        if first:
            second[first[id]] = False

        del first[id]


    def id_exists(self, id):
        if id < 4096:
            return (id in self.emitters.iterkeys())
        else:
            return (id in self.exhibitors.iterkeys())


    def associate_clients(self, emitter, exhibitor):
        if emitter in self.emitters.iterkeys() and exhibitor in self.exhibitors.iterkeys():
            self.emitters[emitter] = exhibitor
            self.exhibitors[exhibitors] = emitter
            return True
        else:
            return False


    def get_all_clients(self):
        return self.emitters.keys() + self.exhibitors.keys()