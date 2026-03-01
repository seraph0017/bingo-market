"""LMSR (Logarithmic Market Scoring Rule) trading engine."""

from __future__ import annotations

import math
from typing import List, Tuple
from dataclasses import dataclass


@dataclass
class LMSRState:
    """LMSR market state."""

    # Outstanding shares for each outcome
    shares: List[int]
    # Liquidity parameter (bigger = more liquidity, less price impact)
    b: float = 100.0

    @property
    def num_outcomes(self) -> int:
        return len(self.shares)


class LMSREngine:
    """
    Logarithmic Market Scoring Rule (LMSR) implementation.

    LMSR is a market maker mechanism that ensures:
    - Continuous liquidity (users can always buy/sell)
    - Price reflects market consensus probability
    - No bankruptcy for the market maker (bounded loss)

    Formula:
    - Cost function: C(q) = b * ln(sum(exp(q_i / b)))
    - Price for outcome i: p_i = exp(q_i / b) / sum(exp(q_j / b))
    - Cost to buy Δq: C(q + Δq) - C(q)

    Where:
    - q = vector of outstanding shares
    - b = liquidity parameter
    - p_i = price/probability of outcome i
    """

    def __init__(self, b: float = 100.0):
        """
        Initialize LMSR engine.

        Args:
            b: Liquidity parameter. Higher = more liquidity, less price impact.
               Lower = less liquidity, more price impact.
        """
        self.b = b

    def cost(self, state: LMSRState) -> float:
        """
        Calculate the cost function C(q).

        C(q) = b * ln(sum(exp(q_i / b)))
        """
        exp_sum = sum(math.exp(q / self.b) for q in state.shares)
        return self.b * math.log(exp_sum)

    def price(self, state: LMSRState, outcome_index: int) -> float:
        """
        Calculate current price for an outcome.

        p_i = exp(q_i / b) / sum(exp(q_j / b))

        This represents the market's implied probability of outcome i.
        """
        exp_values = [math.exp(q / self.b) for q in state.shares]
        exp_sum = sum(exp_values)
        return exp_values[outcome_index] / exp_sum

    def prices(self, state: LMSRState) -> List[float]:
        """Calculate prices for all outcomes."""
        return [self.price(state, i) for i in range(state.num_outcomes)]

    def cost_to_buy(self, state: LMSRState, outcome_index: int, quantity: int) -> float:
        """
        Calculate cost to buy shares of an outcome.

        Cost = C(q + Δq) - C(q)

        Args:
            state: Current market state
            outcome_index: Index of outcome to buy
            quantity: Number of shares to buy

        Returns:
            Cost in knowledge coins
        """
        new_shares = state.shares.copy()
        new_shares[outcome_index] += quantity
        new_state = LMSRState(shares=new_shares, b=self.b)

        return self.cost(new_state) - self.cost(state)

    def cost_to_sell(self, state: LMSRState, outcome_index: int, quantity: int) -> float:
        """
        Calculate payout for selling shares of an outcome.

        This is negative cost (user receives coins).

        Args:
            state: Current market state
            outcome_index: Index of outcome to sell
            quantity: Number of shares to sell (positive number)

        Returns:
            Payout in knowledge coins (positive = user receives)
        """
        return -self.cost_to_buy(state, outcome_index, -quantity)

    def buy(
        self, state: LMSRState, outcome_index: int, quantity: int
    ) -> Tuple[LMSRState, float, List[float]]:
        """
        Execute a buy order.

        Args:
            state: Current market state
            outcome_index: Index of outcome to buy
            quantity: Number of shares to buy

        Returns:
            Tuple of (new_state, cost, new_prices)
        """
        if quantity <= 0:
            raise ValueError("Quantity must be positive")

        new_shares = state.shares.copy()
        new_shares[outcome_index] += quantity
        new_state = LMSRState(shares=new_shares, b=self.b)

        cost = self.cost_to_buy(state, outcome_index, quantity)
        new_prices = self.prices(new_state)

        return new_state, cost, new_prices

    def sell(
        self, state: LMSRState, outcome_index: int, quantity: int
    ) -> Tuple[LMSRState, float, List[float]]:
        """
        Execute a sell order.

        Args:
            state: Current market state
            outcome_index: Index of outcome to sell
            quantity: Number of shares to sell

        Returns:
            Tuple of (new_state, payout, new_prices)
        """
        if quantity <= 0:
            raise ValueError("Quantity must be positive")

        # Can't sell more than you own
        if state.shares[outcome_index] < quantity:
            raise ValueError("Insufficient shares to sell")

        new_shares = state.shares.copy()
        new_shares[outcome_index] -= quantity
        new_state = LMSRState(shares=new_shares, b=self.b)

        payout = self.cost_to_sell(state, outcome_index, quantity)
        new_prices = self.prices(new_state)

        return new_state, payout, new_prices

    def calculate_payout(self, state: LMSRState, user_shares: List[int], winning_index: int) -> int:
        """
        Calculate payout for a user when market resolves.

        In LMSR, if you own shares of the winning outcome, you get 1 coin per share.
        Shares of losing outcomes are worth 0.

        Args:
            state: Final market state
            user_shares: User's shares for each outcome
            winning_index: Index of winning outcome

        Returns:
            Payout in knowledge coins
        """
        return user_shares[winning_index]

    def get_market_probabilities(self, state: LMSRState) -> List[float]:
        """
        Get market-implied probabilities for all outcomes.

        These are the current prices, which sum to 1.
        """
        return self.prices(state)

    def calculate_roi(self, buy_price: float, shares: int, outcome_won: bool) -> float:
        """
        Calculate return on investment.

        Args:
            buy_price: Average price paid per share
            shares: Number of shares owned
            outcome_won: Whether the bought outcome won

        Returns:
            ROI as percentage (e.g., 50.0 = 50% return)
        """
        if outcome_won:
            # Get 1 coin per share, ROI = (shares - cost) / cost * 100
            cost = buy_price * shares
            payout = shares
            return ((payout - cost) / cost) * 100 if cost > 0 else 0
        else:
            # Lost everything
            return -100.0
