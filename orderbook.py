import heapq
from collections import deque


class OrderBook:
    def __init__(self):
        #maintain 2 things for each side. a 'price levels' heap and a quantity dict
        self.bids_prices = []
        self.bids_quantities = {}
        self.asks_prices = []
        self.asks_quantities = {}
        self.buy_orders = {}
        self.sell_orders = {}


    def add_order(self, order_id: int, side: str, price: int, qty: int):
        """side is "buy" or "sell". Returns a list of trades"""

        trades = []

        if side == 'buy':
            #try to match before adding to the resting book.
            while self.best_ask() != None and self.best_ask()[0] <= price and qty > 0: # type: ignore
                
                # fetch the level at the best ask price. total qty and queue of orders.
                sell_price, _ = self.best_ask() # type: ignore
                sell_queue = self.asks_quantities[sell_price][1]

                while qty > 0 and sell_queue:
                    front_order_id = sell_queue[0]

                    if front_order_id in self.sell_orders:
                        front_order_qty = self.sell_orders[front_order_id][1]
                    else:
                        front_order_qty = 0
                        sell_queue.popleft()

                    fill_amt = min(front_order_qty, qty)

                    #record a trade if it happened
                    if fill_amt != 0:
                        trades.append((order_id, front_order_id, sell_price, fill_amt))
                        #subtract the fill from 3 places
                        qty -= fill_amt
                        self.asks_quantities[sell_price][0] -= fill_amt
                        self.sell_orders[front_order_id][1] -= fill_amt
                    

                    #if the resting order exists but is now empty, remove it from the front (popleft)
                    if front_order_id in self.sell_orders:
                        if self.sell_orders[front_order_id][1] == 0:
                            sell_queue.popleft()
                            self.sell_orders.pop(front_order_id)

                    #if the queue is empty, the price level is gone, so we clean it up: remove the dict entry and pop it from the heap
                    if not sell_queue:
                        heapq.heappop(self.asks_prices)
                        self.asks_quantities.pop(sell_price)


            # if the buy order is not fully completed, rest it
            if qty > 0:
                # if the price level exists, add to it
                if price in self.bids_quantities:
                    self.bids_quantities[price][1].append(order_id) #1=deque, 0=total
                    self.buy_orders[order_id] = [price, qty]
                    self.bids_quantities[price][0] += qty
                else:
                    heapq.heappush(self.bids_prices, -price) #NOTE THE NEGATIVE SIGN
                    self.bids_quantities[price] = [qty, deque([order_id])]
                    self.buy_orders[order_id] = [price, qty]


        elif side == 'sell':
            #mirrored matching logic as buy side
            while self.best_bid() != None and self.best_bid()[0] >= price and qty > 0: # type: ignore

                # fetch the level at the best bid price. total qty and queue of orders. That becomes the transaction sell price.
                sell_price, _ = self.best_bid() # type: ignore
                buy_queue = self.bids_quantities[sell_price][1]

                while qty > 0 and buy_queue:
                    front_order_id = buy_queue[0]

                    if front_order_id in self.buy_orders:
                        front_order_qty = self.buy_orders[front_order_id][1]
                    else:
                        front_order_qty = 0
                        buy_queue.popleft()

                    fill_amt = min(front_order_qty, qty)

                    #process a trade if it actually happened against a living order
                    if fill_amt != 0:
                        trades.append((front_order_id, order_id, sell_price, fill_amt))
                        #subtract the fill from 3 places
                        qty -= fill_amt
                        self.bids_quantities[sell_price][0] -= fill_amt
                        self.buy_orders[front_order_id][1] -= fill_amt

                    #if the resting order exists and is now empty, remove it from the front (popleft)
                    if front_order_id in self.buy_orders:
                        if self.buy_orders[front_order_id][1] == 0:
                            buy_queue.popleft()
                            self.buy_orders.pop(front_order_id)

                    #if the queue is empty, the price level is gone, so we clean it up: remove the dict entry and pop it from the heap
                    if not buy_queue:
                        heapq.heappop(self.bids_prices)
                        self.bids_quantities.pop(sell_price)

            if qty > 0:
                # same logic but without negation (the min-heap is what we want)
                if price in self.asks_quantities:
                    self.asks_quantities[price][1].append(order_id)
                    self.asks_quantities[price][0] += qty
                    self.sell_orders[order_id] = [price, qty]

                else:
                    heapq.heappush(self.asks_prices, price)
                    self.asks_quantities[price] = [qty, deque([order_id])]
                    self.sell_orders[order_id] = [price, qty]

        return trades



    def best_bid(self):
        """(price, total_qty_at_that_price) or None. The best bid is the highest bid""" 
        if self.bids_prices:
            price = -self.bids_prices[0]

            #remove any dead price levels here
            while self.bids_quantities[price][0] == 0:
                heapq.heappop(self.bids_prices)
                self.bids_quantities.pop(price)

                if not self.bids_prices:
                    return None
                
                price = -self.bids_prices[0]

            return (price, self.bids_quantities[price][0]) 
        return None

    def best_ask(self):
        """(price, total_qty_at_that_price) or None."""
        if self.asks_prices:
            price = self.asks_prices[0]

            #remove any dead price levels here
            while self.asks_quantities[price][0] == 0:
                heapq.heappop(self.asks_prices)
                self.asks_quantities.pop(price)

                if not self.asks_prices:
                    return None

                price = self.asks_prices[0]

            return (price, self.asks_quantities[price][0])
        return None

    def cancel(self, order_id):
        # check buy orders then sell orders
        if order_id in self.buy_orders:
            price, qty = self.buy_orders[order_id]

            #clean up the quantities
            self.bids_quantities[price][0] -= qty

            self.buy_orders.pop(order_id)
            return True
        
        elif order_id in self.sell_orders:
            price, qty = self.sell_orders[order_id]

            self.asks_quantities[price][0] -= qty

            self.sell_orders.pop(order_id)
            return True

        return False


class ConsolidatedBook:
    pass

#unit testing
if __name__ == '__main__':
    book = OrderBook()
