import os
import numpy as np
class GachaSimulator:
    def __init__(self, base_prob=0.11, prob_increment=0.18, increase_after=5):
        self.increase_after = increase_after
        self.base_prob = base_prob
        self.prob_increment = prob_increment
        self.max_prob = 1
        self.count = 0
        self.bigcount = 0

    def draw(self):
        prob = min(self.base_prob + max(self.count-self.increase_after,0) * self.prob_increment, self.max_prob)
        result = np.random.rand() < prob
        self.count = 0 if result else self.count + 1
        if result:
            if self.bigcount  < 1:
                self.bigcount +=1
                return int(np.random.choice([1,2]))
            else:
                self.bigcount = 0
                return 2
        else:
            return 0            
        
    
if __name__ == "__main__":
    simulator = GachaSimulator()
    draws = 10
    for _ in range(10):
        results = [simulator.draw() for _ in range(draws)]
        print(results)