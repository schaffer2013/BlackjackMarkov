# Define softness options
import time


NO_ACE = 'NO_ACE'
SOFT = 'SOFT'
HARD = 'HARD'

FULL_DECK = [4, 16, 4, 4, 4, 4, 4, 4, 4, 4]
RANKS = [11, 10, 9, 8, 7, 6, 5, 4, 3, 2]

noAceCount = 20  # From 2 to 21 (inclusive) 
hardCount = 5   # HARD options for 12-16
softCount = 6   # From 11 to 16 (inclusive)
TOTAL_ARRAY_LENGTH = noAceCount + softCount + hardCount + 1  # Total array length including bust
HAND_VALUE_ARRAY = [
    (2, NO_ACE), (3, NO_ACE), (4, NO_ACE), (5, NO_ACE), (6, NO_ACE),
    (7, NO_ACE), (8, NO_ACE), (9, NO_ACE), (10, NO_ACE), (11, NO_ACE),
    (12, NO_ACE), (13, NO_ACE), (14, NO_ACE), (15, NO_ACE), (16, NO_ACE),
    (17, NO_ACE), (18, NO_ACE), (19, NO_ACE), (20, NO_ACE), (21, NO_ACE),
    (11, SOFT), (12, SOFT), (13, SOFT), (14, SOFT), (15, SOFT), (16, SOFT),
    (12, HARD), (13, HARD), (14, HARD), (15, HARD), (16, HARD),
    (22, NO_ACE)  # Bust case
]
EMPTY = [0.0] * TOTAL_ARRAY_LENGTH

def unitTest():
    if len(HAND_VALUE_ARRAY) != TOTAL_ARRAY_LENGTH:
        raise Exception("HAND_VALUE_ARRAY length does not match TOTAL_ARRAY_LENGTH")
    
    for i in range(TOTAL_ARRAY_LENGTH):
        check = valueToArray(HAND_VALUE_ARRAY[i])
        if not check[i]:
            raise Exception(f"Test failed for HAND_VALUE_ARRAY[{i}] = {HAND_VALUE_ARRAY[i]}")
    
    print("All tests passed.")

def deckToProbs(deck):
    total = sum(deck)
    probs = []
    for c in deck:
        probs.append(c/total)
    return probs

def scaleList(oldList, scalar):
    return [i * scalar for i in oldList]

def addLists(list1, list2):
    return [sum(x) for x in zip(list1, list2)]

def valueToArray(hand_value_tuple):
    """
    Converts a blackjack hand value and softness into an array representation.
    
    Args:
    hand_value_tuple (tuple): A tuple containing the hand value and softness (NO_ACE, SOFT, HARD).
    
    Returns:
    list: An array where indices represent hand values and bust, with True indicating the current hand value.
    """
    value, softness = hand_value_tuple
    arr = [False] * TOTAL_ARRAY_LENGTH
    
    # If bust
    if value > 21:
        arr[-1] = True
        return arr
    
    # Hard counts, including HARD options
    if softness == NO_ACE or value > 16:
        arr[value - 2] = True
    elif softness == HARD:
        arr[(value - 12) + noAceCount + softCount] = True
    # Soft counts
    else:
        arr[(value - 11) + noAceCount] = True
    
    return arr

def blackjack_hand_value(hand):
    """
    Calculate the value of a blackjack hand and determine its softness.
    
    Args:
    hand (list): A list of integers representing the ranks in a blackjack hand (between [2, 11]).
    
    Returns:
    tuple: A tuple containing the total value of the hand and the softness (NO_ACE, SOFT, HARD).
    """
    total_value = 0
    aces_count = 0
    softness = NO_ACE
    
    for card in hand:
        if card == 11:
            aces_count += 1
        total_value += card

    while total_value > 21 and aces_count > 0:
        total_value -= 10
        aces_count -= 1

    if aces_count > 0:
        softness = SOFT if total_value + 10 <= 21 else HARD

    return total_value, softness

def update_blackjack_hand(oldHandValue, wasSoft, newCardValue):
    """
    Update the blackjack hand value with a new card and determine its softness.
    
    Args:
    oldHandValue (int): The value of the hand before drawing the new card.
    wasSoft (str): The softness of the hand before drawing the new card (NO_ACE, SOFT, HARD).
    newCardValue (int): The value of the new card drawn (between 2 and 11).
    
    Returns:
    tuple: A tuple containing the new hand value and the softness (NO_ACE, SOFT, HARD).
    """
    if not (2 <= newCardValue <= 11):
        raise ValueError("New card value must be between 2 and 11.")

    # Calculate the new hand value
    newHandValue = oldHandValue + newCardValue
    softness = wasSoft

    # Check if the new hand is soft or hard
    if newCardValue == 11:
        if newHandValue <= 21:
            softness = SOFT
        else:
            newHandValue -= 10  # Convert the Ace from 11 to 1 if it causes a bust
            softness = HARD 
    elif wasSoft == SOFT and newHandValue > 21:
        newHandValue -= 10
        softness = HARD

    return newHandValue, softness

def arrFromHand(hand):
    value, softness = blackjack_hand_value(hand)
    return valueToArray((value, softness))

def newCardAddedToArray(oldHandValue, wasSoft, newCardValue):
    value, softness = update_blackjack_hand(oldHandValue, wasSoft, newCardValue)
    return valueToArray((value, softness))

def removeValFromDeck(deck, val):
    if not (2 <= val <= 11):
        raise ValueError("New card value must be between 2 and 11.")
    newDeck = deck.copy()
    newDeck[11-val] -= 1
    return newDeck

def dealerHold(value, remainingDeck = FULL_DECK, isSoft = NO_ACE):
    if value >= 17:
        return valueToArray((value, isSoft))
    
    # Distribution of hand values after drawing every possible card
    runningSums = [0.0] * TOTAL_ARRAY_LENGTH
    probsToDrawCard = deckToProbs(remainingDeck)
    for rank, prob in zip(RANKS, probsToDrawCard):
        nextRankArray = newCardAddedToArray(value, isSoft, rank)
        runningSums = addLists(runningSums, scaleList(nextRankArray, prob))

    debugList = []
    for i in range(TOTAL_ARRAY_LENGTH):
        debugList.append([HAND_VALUE_ARRAY[i], runningSums[i]])

    # Using distributed hand values to give their contribution to the total
    runningTotal = EMPTY.copy()
    for i in range(TOTAL_ARRAY_LENGTH):
        if runningSums[i] > 0.0:
            newVal, newSoft = HAND_VALUE_ARRAY[i]
            removedCard = newVal - value
            if removedCard <= 1:
                removedCard += 10
            nextGen = dealerHold(newVal, isSoft = newSoft, remainingDeck= removeValFromDeck(remainingDeck, removedCard))

            runningTotal = addLists(runningTotal, scaleList(nextGen, runningSums[i]))
            debugList = []
            for i in range(TOTAL_ARRAY_LENGTH):
                debugList.append([HAND_VALUE_ARRAY[i], runningTotal[i]])
            a = 1

    return runningTotal

# Run unit tests
unitTest()

# Example usage
result = dealerHold(0)
a = 1

