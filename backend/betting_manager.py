import time
from backend.config import (
    ROUND_DURATION_SECONDS, BETTING_WINDOW_SECONDS,
    INITIAL_BALANCE, BET_THRESHOLD_LOW, BET_THRESHOLD_HIGH,
)


class BettingManager:
    def __init__(self, counter):
        self.counter = counter
        self.round_id = 0
        self.round_start_time = time.time()
        self.phase = "betting"  # "betting" | "active" | "resolved"
        self.bets = {}  # user_id -> {"option": str, "amount": int}
        self.balances = {}  # user_id -> int
        self.last_result = None
        self._start_new_round()

    def _start_new_round(self):
        self.round_id += 1
        self.round_start_time = time.time()
        self.phase = "betting"
        self.bets = {}
        self.last_result = None
        self.counter.reset()

    def get_balance(self, user_id):
        if user_id not in self.balances:
            self.balances[user_id] = INITIAL_BALANCE
        return self.balances[user_id]

    def place_bet(self, user_id, option, amount):
        """Place un pari. Retourne (success, message)."""
        if self.phase != "betting":
            return False, "Les paris sont fermés pour ce round."

        if option not in ("under", "between", "over"):
            return False, "Option invalide."

        if amount <= 0:
            return False, "Montant invalide."

        balance = self.get_balance(user_id)
        if amount > balance:
            return False, "Solde insuffisant."

        if user_id in self.bets:
            # Rembourser le pari précédent
            prev = self.bets[user_id]
            self.balances[user_id] += prev["amount"]

        self.balances[user_id] -= amount
        self.bets[user_id] = {"option": option, "amount": amount}
        return True, f"Pari placé : {option} pour {amount} coins."

    def tick(self):
        """Appelé à chaque frame pour gérer le lifecycle du round."""
        elapsed = time.time() - self.round_start_time

        if self.phase == "betting" and elapsed >= BETTING_WINDOW_SECONDS:
            self.phase = "active"

        if elapsed >= ROUND_DURATION_SECONDS:
            self._resolve_round()
            self._start_new_round()

    def _resolve_round(self):
        final_count = self.counter.count
        winning_option = self._determine_winner(final_count)

        # Calculer les gains
        for user_id, bet in self.bets.items():
            if bet["option"] == winning_option:
                multiplier = self._get_multiplier(bet["option"])
                winnings = int(bet["amount"] * multiplier)
                self.balances[user_id] += winnings

        self.last_result = {
            "round_id": self.round_id,
            "final_count": final_count,
            "winning_option": winning_option,
        }

    def _determine_winner(self, count):
        if count < BET_THRESHOLD_LOW:
            return "under"
        elif count <= BET_THRESHOLD_HIGH:
            return "between"
        else:
            return "over"

    def _get_multiplier(self, option):
        multipliers = {
            "under": 2.5,
            "between": 2.0,
            "over": 2.5,
        }
        return multipliers.get(option, 1.0)

    def get_bet_options(self):
        return [
            {
                "id": "under",
                "label": f"Moins de {BET_THRESHOLD_LOW}",
                "multiplier": self._get_multiplier("under"),
            },
            {
                "id": "between",
                "label": f"Entre {BET_THRESHOLD_LOW} et {BET_THRESHOLD_HIGH}",
                "multiplier": self._get_multiplier("between"),
            },
            {
                "id": "over",
                "label": f"Plus de {BET_THRESHOLD_HIGH}",
                "multiplier": self._get_multiplier("over"),
            },
        ]

    def get_state(self, user_id=None):
        elapsed = time.time() - self.round_start_time
        timer_remaining = max(0, int(ROUND_DURATION_SECONDS - elapsed))

        state = {
            "type": "state",
            "round_id": self.round_id,
            "phase": self.phase,
            "count": self.counter.count,
            "timer_seconds_remaining": timer_remaining,
            "bet_options": self.get_bet_options(),
        }

        if user_id:
            state["balance"] = self.get_balance(user_id)
            if user_id in self.bets:
                state["current_bet"] = self.bets[user_id]

        if self.last_result:
            state["last_result"] = self.last_result

        return state
