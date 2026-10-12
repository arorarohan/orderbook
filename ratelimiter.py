"""a rate limiter demo"""
from collections import deque

class RateLimiter:
    def __init__(self, max_requests, window):
        self.max_requests = max_requests
        self.window = window
        self.users = {} #user:[cost, queue]
        self.global_requests = [0, deque()]
        self.global_window = None
        self.global_limit = None

    def _evict(self, queue: list, window, timestamp):
        while queue[1] and (timestamp - queue[1][0][0] >= window):
            _, recovered_cost = queue[1].popleft()
            queue[0] -= recovered_cost
            return

    def set_global_limit(self, max_units, window):
        self.global_window = window
        self.global_limit = max_units
        return


    def allow(self, user_id, timestamp, cost=1):
        # first create a queue for the user if they don't have one. The global queue exists on init so no need to initialize it.
        if user_id not in self.users:
            self.users[user_id] = [0, deque()]

        #pop from the user queue until the window is satisfied.
        self._evict(self.users[user_id], self.window, timestamp)

        #now the time range is within the window, so we measure the limit
        if self.users[user_id][0] + cost > self.max_requests:
            return False

        #do the same for the global queue if there is a set limit
        if self.global_limit:
            self._evict(self.global_requests, self.global_window, timestamp)

            if self.global_requests[0] + cost > self.global_limit:
                return False

        #Allowed! by this point

        #add to the queues and return if allowed, increment the running total too
        self.users[user_id][1].append((timestamp, cost))
        self.users[user_id][0] += cost
        self.global_requests[1].append((timestamp, cost))
        self.global_requests[0] += cost
        return True
