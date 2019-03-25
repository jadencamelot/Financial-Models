#!/usr/bin/env python3

class Asset():
	def __init__(self, date, price, qty, cgt_eligible=True):
		self.date = date
		self.price = price
		self.qty = qty
		self.cgt_eligible = cgt_eligible

	def cgt_price(self, sale_date, sale_price):
		cgt = sale_price - self.price
		if self.cgt_eligible and sale_date - self.date > 365:
			cgt *= 0.5
		return cgt

	def __repr__(self):
		return str((self.date, self.price, self.qty))

class AssetPool():
	def __init__(self):
		self.pool = []
		self.taxable_gain = 0

	def __repr__(self):
		return str(self.pool)

	def buy(self, date, price, qty):
		asset = Asset(date, price, qty)
		self.pool.append(asset)

	def sell(self, date, price, qty):
		qty_left = qty
		total_taxable_gain = 0

		while qty_left > 0:
			if len(self.pool) < 1:
				print("wtf")

			index = self._choose_asset_to_sell(date, price)
			taxable_gain, qty_sold = self._sell_asset(index, date, price, qty_left)
			qty_left -= qty_sold
			total_taxable_gain += taxable_gain

		self.taxable_gain += total_taxable_gain
		return taxable_gain

	def _choose_asset_to_sell(self, date, price):
		# Find cheapest asset to sell in pool
		# TODO: make Asset class itself comparable
		cheapest_i = 0
		cheapest_cgt = self.pool[0].cgt_price(date, price)
		for i, asset in enumerate(self.pool):
			this_cgt = asset.cgt_price(date, price)
			if this_cgt < cheapest_cgt:
				cheapest_i = i
				cheapest_cgt = this_cgt

		return cheapest_i

	def _sell_asset(self, index, date, price, qty_sold):
		# Sell it
		asset = self.pool[index]
		if asset.qty > qty_sold:
			# Asset partially sold
			# Qty fully sold
			asset.qty -= qty_sold
		else:
			# Asset fully sold
			# Some qty remaining
			self.pool.pop(index)
			qty_sold = asset.qty

		taxable_gain = qty_sold * asset.cgt_price(date, price)

		return taxable_gain, qty_sold

def test_case_1():
	ap = AssetPool()

	ap.buy(0, 1000, 1)
	ap.buy(10, 2000, 1)
	ap.buy(20, 3000, 1)
	ap.buy(400, 4000, 1)

	print(ap)

	ap.sell(401, 5000, 2.5)

	print(ap.taxable_gain)
	assert ap.taxable_gain == 4000

def main():
	print(test_case_1())

if __name__ == '__main__':
	main()
