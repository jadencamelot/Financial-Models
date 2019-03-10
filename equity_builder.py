import numpy as np
import string

YEARS = 12

"""
NAB Equity Builder simulation tool

Simulates a single equity builder loan.

Assumptions:
	- You have a fixed monthly amount available for investment
	- You do not increase the LVR during the loan term or refinance
	- Dividends are taxed at your marginal tax rate.
		* Negative gearing is taken into account. If dividends are less than
		  interest payments, then the shortfall is grossed-up by your marginal
		  tax rate.
	- After repayments are made, any additional cashflow is reinvested in the
	  underlying asset class with zero leverage.
		* Extra funds are NOT used to reduce debt
		* Extra funds are used to purchase extra shares OUTSIDE the equity
		  builder loan structure, and allowed to compound/provide dividends

Todo:
	- Add backtesting from real data
	- Add ability to suspend principal payments when LVR drops below 30%
	- Add ability to increase leverage during term of the loan
	- Make a nice CLI (if I can be bothered)
	- Improve docs to clarify a few things
"""

class Simulation():
	"""
	Default parameters (can be overridden).

	deposit (float)
		Initial deposit.

	lvr (float)
		Can be zero.
	
	savings_per_month (float)
		Total cashflow available for investment.
	
	loan_term (int)
		Loan term in years.
	"""
	annual_growth = 0.07
	annual_yield = 0.025
	marginal_tax = 0.37
	interest_rate = 0.0505
	deposit = 5000
	lvr = 0.5
	savings_per_month = 300
	loan_term = 10

	def __init__(self, **kwargs):
		"""
		Per-simulation parameters override defaults.
		"""
		acceptable_keys = (
			"annual_growth",
			"annual_yield",
			"marginal_tax",
			"interest_rate",
			"deposit",
			"lvr",
			"savings_per_month",
			"loan_term")

		for k in acceptable_keys:
			if k in kwargs.keys():
				self.__setattr__(k, kwargs[k])

		self._initial_setup()

	def _initial_setup(self):
		self.portfolio = self.deposit / (1 - self.lvr)
		self.loan_balance = self.portfolio - self.deposit
		self.original_loan_balance = self.loan_balance

	def run(self, years, method="slm", display_interval=False):
		"""
		Run a simulation.


		years (int)
			Simulate N years. If this is longer than the loan term, the
			simulation will continue with the loan paid off.
		
		method (str)
			SLM = "straight line method", where principal payments are fixed
			      and interest decreases over time.
			HLM = "home loan method", where total repayments are fixed and
			      principal payment increases over time.
		
		display_interval (int)
			Display stats every N months. Set to a falsy value to disable.
		"""
		periods = years * YEARS
		self.display_interval = display_interval
		if method.lower() == "slm":
			iterate_func = self._iterate_slm
		elif method.lower() == "hlm":
			iterate_func = self._iterate_hlm
		else:
			raise ValueError("Valid methods are 'slm' or 'hlm'.")

		# Run iterations
		for period in range(periods + 1):
			iterate_func(period)

		return self

	def _iterate_slm(self, period):
		principal_repayment = self.loan_balance / self.loan_term / 12
		interest_repayment = self.loan_balance * self.interest_rate / 12

		self._iterate(principal_repayment, interest_repayment, period)

	def _iterate_hlm(self, period):
		rate = self.interest_rate / 12
		ppmt = -np.ppmt(rate, period, self.loan_term * 12, self.original_loan_balance)
		ipmt = -np.ipmt(rate, period, self.loan_term * 12, self.original_loan_balance)
		# fmt = "{0:3d} {1:8,.2f} {2:8.2f} {3:8.2f}"
		# print(fmt.format(period, ppmt, ipmt, self.loan_balance))

		self._iterate(ppmt, ipmt, period)

	def _iterate(self, principal_repayment, interest_repayment, period):
		# Calculate divs
		dividends = self.portfolio * self.annual_yield / 12

		# Handle periods after end of loan		
		if self.loan_balance <= 0:
			interest_repayment = 0
			principal_repayment = 0

		# Handle final payment on loan
		if principal_repayment > self.loan_balance:
			principal_repayment = max(self.loan_balance, 0)

		# Update portfolio
		self.portfolio *= 1 + (self.annual_growth / 12)
		self.loan_balance -= principal_repayment

		# Handle tax (including negative gearing)
		taxable_cashflow = dividends - interest_repayment
		net_cashflow = taxable_cashflow * (1 - self.marginal_tax)

		# Buy more shares with excess cashflow (or sell to make repayments)
		excess_cashflow = self.savings_per_month + net_cashflow - principal_repayment
		self.portfolio += excess_cashflow

		if self.display_interval and period % self.display_interval == 0:
			print(f"\n---- Month {period} ----")
			fmt_thou = "{0:<15}$ {1:8,.2f}"
			fmt_mil  = "{0:<15}$ {1:8,.0f}"
			print(
				fmt_thou.format("Repayment:", interest_repayment + principal_repayment),
				fmt_thou.format(" - Principal:", principal_repayment),
				fmt_thou.format(" - Interest:", interest_repayment),
				
				fmt_thou.format("Cashflow:", excess_cashflow),
				fmt_thou.format(" - Savings:", self.savings_per_month),
				fmt_thou.format(" - Dividend:", dividends),
				fmt_thou.format(" - Taxable:", taxable_cashflow),
				fmt_thou.format(" - Net:", net_cashflow),
				"",
				fmt_mil.format("Portfolio:", self.portfolio),
				fmt_mil.format("Loan Balance:", self.loan_balance),
				fmt_mil.format("Equity:", self.portfolio - self.loan_balance),
				"",
				sep="\n"
			)

def example_simulation():
	series = []

	# Set parameters for all cases
	Simulation.deposit = 20000
	Simulation.savings_per_month = 600
	Simulation.loan_term = 10

	# Run a base case with zero leverage (aka no loan at all)
	base_case = Simulation(lvr=0.00, savings_per_month=300)
	base_case.run(10)
	base_result = base_case.portfolio

	print(f"Baseline: ${base_result:,.0f}\n")

	# Increasing LVR with same loan term
	series.append(Simulation(lvr=0.33))
	series.append(Simulation(lvr=0.50))
	series.append(Simulation(lvr=0.66))
	series.append(Simulation(lvr=0.75))

	# Longer loan terms
	series.append(Simulation(lvr=0.50, loan_term=15))
	series.append(Simulation(lvr=0.66, loan_term=15))

	# Run simulations
	for i, s in enumerate(series):
		s.run(10, "hlm", 0)

		name = f"Series {string.ascii_uppercase[i]}"
		result = s.portfolio - s.loan_balance
		performance = (result * 100 / base_result) - 100

		print(f"{name}: ${result:,.0f} = outperformed baseline by {performance:.2f}% ({s.lvr*100:.0f}% LVR)")

if __name__ == '__main__':
	example_simulation()
