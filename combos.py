from collections import defaultdict

FULL_DECK = [4, 16, 4, 4, 4, 4, 4, 4, 4, 4]
RANKS = [11, 10, 9, 8, 7, 6, 5, 4, 3, 2]

def remove_val_from_deck(deck, val):
    if not (2 <= val <= 11):
        raise ValueError("Card value must be between 2 and 11.")
    new_deck = deck.copy()
    new_deck[11 - val] -= 1
    return new_deck

def count_combinations(deck, num_cards, current_combination=[]):
    if num_cards == 0:
        return {tuple(sorted(current_combination)): 1}
    
    combinations = defaultdict(int)
    for i, count in enumerate(deck):
        if count > 0:
            new_deck = remove_val_from_deck(deck, RANKS[i])
            new_combination = current_combination + [RANKS[i]]
            sub_combinations = count_combinations(new_deck, num_cards - 1, new_combination)
            for comb, comb_count in sub_combinations.items():
                combinations[comb] += comb_count * count
    
    return combinations

def getAllCombos(numDecks = 1):
    # Count all combinations of 2 cards
    deckChute = []
    for r in FULL_DECK:
        deckChute.append(r * numDecks)
    combinations = count_combinations(deckChute, 2)

    extended_combos = []
    # Print the combinations and their count
    total_combinations = sum(combinations.values())
    #print(f"Total combinations: {total_combinations}")
    for combo, count in combinations.items():
        remainingDeck = remove_val_from_deck(deckChute, combo[0])
        remainingDeck = remove_val_from_deck(remainingDeck, combo[1])
        for rank, rankCount in zip(RANKS, remainingDeck):
            ex_combo = (combo[0],combo[1], rank, rankCount * count)
            extended_combos.append(ex_combo)
            #print(ex_combo)

    total_extended = 0
    for x in extended_combos:
        total_extended += x[3]
    return extended_combos
    #print(len(extended_combos))
