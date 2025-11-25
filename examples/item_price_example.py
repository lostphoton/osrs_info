from osrs_info import Decoder

api = Decoder()
items = api.items

# Substring search (tradeable-only)
hits = items.search("scythe")
scythe = hits[0]

print(scythe["id"], scythe["name"])

# Bundle of metadata + latest price
bundle = items.price(scythe["id"])

print("Name:", bundle["meta"]["name"])
print("High:", bundle["price"]["high"])
print("Low:", bundle["price"]["low"])
