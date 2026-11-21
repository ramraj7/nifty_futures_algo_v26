class DailyRisk:
    def __init__(self, max_loss=3500.0, max_trades=3):
        self.max_loss = float(max_loss)
        self.max_trades = int(max_trades)
        self.day = None
        self.trades = 0
        self.realized = 0.0

    def reset_if_new_day(self, day):
        if self.day != day:
            self.day, self.trades, self.realized = day, 0, 0.0

    def can_enter(self, day, unrealized=0.0, estimated_costs=0.0):
        self.reset_if_new_day(day)
        return self.trades < self.max_trades and (
            self.realized + unrealized - estimated_costs > -self.max_loss
        )

    def record_entry(self):
        self.trades += 1

    def record_exit(self, pnl):
        self.realized += float(pnl)

    def loss_limit_hit(self, unrealized=0.0, estimated_costs=0.0):
        return self.realized + unrealized - estimated_costs <= -self.max_loss
