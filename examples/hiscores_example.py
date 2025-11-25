from osrs_info import Decoder

api = Decoder()

hs = api.hiscores.get("C Engineer")

print("Attack level:", hs.skill("attack", "level"))
print("Zulrah KC:", hs.boss("zulrah", "score"))
print("Clues:", hs.clue("clue_scrolls_all", "score"))
